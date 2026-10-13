from datetime import date

from app.queries import previous_month
from app.reports import archive_path, ensure_previous_month_archived


def make_entry(client, **kw):
    body = {
        "title": "Write docs",
        "started_at": "2026-10-07T09:00",
        "ended_at": "2026-10-07T10:30",
    } | kw
    r = client.post("/api/entries", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_api_requires_login(anon):
    assert anon.get("/api/entries?month=2026-10").status_code == 401
    assert anon.get("/api/auth/me").status_code == 401


def test_wrong_password_is_throttled(anon):
    for _ in range(5):
        r = anon.post("/api/auth/login", json={"username": "tester", "password": "nope"})
        assert r.status_code == 401
    r = anon.post("/api/auth/login", json={"username": "tester", "password": "s3cret"})
    assert r.status_code == 429


def test_logout_clears_session(client):
    assert client.get("/api/auth/me").status_code == 200
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401


def test_entry_crud_and_duration(client):
    e = make_entry(client)
    assert e["minutes"] == 90 and not e["running"]

    r = client.put(f"/api/entries/{e['id']}", json={
        "title": "Write more docs", "started_at": "2026-10-07T09:00", "ended_at": "2026-10-07T11:00",
    })
    assert r.json()["minutes"] == 120

    listed = client.get("/api/entries?month=2026-10").json()
    assert [x["title"] for x in listed] == ["Write more docs"]
    assert client.get("/api/entries?month=2026-11").json() == []

    assert client.delete(f"/api/entries/{e['id']}").status_code == 204
    assert client.get("/api/entries?month=2026-10").json() == []


def test_end_before_start_rejected(client):
    r = client.post("/api/entries", json={
        "title": "x", "started_at": "2026-10-07T10:00", "ended_at": "2026-10-07T09:00",
    })
    assert r.status_code == 422


def test_timer_start_switches_running_entry(client):
    first = client.post("/api/timer/start", json={"title": "Task A"}).json()
    assert first["running"]
    second = client.post("/api/timer/start", json={"title": "Task B"}).json()
    assert client.get("/api/timer").json()["entry"]["id"] == second["id"]

    month = first["started_at"][:7]
    by_id = {e["id"]: e for e in client.get(f"/api/entries?month={month}").json()}
    assert not by_id[first["id"]]["running"]

    stopped = client.post("/api/timer/stop").json()
    assert not stopped["running"]
    assert client.get("/api/timer").json()["entry"] is None
    assert client.post("/api/timer/stop").status_code == 409


def test_project_delete_keeps_entries(client):
    p = client.post("/api/projects", json={"name": "Client X", "color": "#ff0000"}).json()
    assert client.post("/api/projects", json={"name": "Client X"}).status_code == 409
    e = make_entry(client, project_id=p["id"])
    assert e["project_name"] == "Client X"

    client.delete(f"/api/projects/{p['id']}")
    [kept] = client.get("/api/entries?month=2026-10").json()
    assert kept["id"] == e["id"] and kept["project_id"] is None


def test_filters_and_csv(client):
    p = client.post("/api/projects", json={"name": "Ops"}).json()
    make_entry(client, title="Deploy server", project_id=p["id"])
    make_entry(client, title="Email client", started_at="2026-10-08T09:00", ended_at="2026-10-08T09:15")

    assert len(client.get(f"/api/entries?month=2026-10&project_id={p['id']}").json()) == 1
    assert len(client.get("/api/entries?month=2026-10&project_id=0").json()) == 1
    assert len(client.get("/api/entries?month=2026-10&q=deploy").json()) == 1

    csv = client.get("/api/entries/export.csv?month=2026-10").text
    assert "Deploy server" in csv and "Email client" in csv


def test_pdf_report(client):
    make_entry(client, notes="Covered <setup> & install steps")
    r = client.get("/api/reports/2026-10/pdf")
    assert r.status_code == 200
    assert r.content.startswith(b"%PDF")

    empty = client.get("/api/reports/2025-01/pdf")
    assert empty.content.startswith(b"%PDF")
    assert client.get("/api/reports/2026-13/pdf").status_code == 422


def test_archive_and_listing(client):
    make_entry(client)
    assert client.get("/api/reports/2026-10/archived").status_code == 404
    client.post("/api/reports/2026-10/archive")
    assert client.get("/api/reports/2026-10/archived").content.startswith(b"%PDF")
    listed = {m["month"]: m for m in client.get("/api/reports").json()}
    assert listed["2026-10"]["entries"] == 1 and listed["2026-10"]["archived"]
    archive_path("2026-10").unlink()


def test_auto_archive_previous_month(client, monkeypatch):
    from datetime import datetime

    from app import reports

    monkeypatch.setattr(reports, "now_local", lambda: datetime(2026, 11, 1, 0, 30))
    assert ensure_previous_month_archived() is None  # no entries yet

    make_entry(client)
    path = ensure_previous_month_archived()
    assert path == archive_path("2026-10") and path.exists()
    assert ensure_previous_month_archived() is None  # never overwrites
    path.unlink()


def test_previous_month():
    assert previous_month(date(2026, 1, 15)) == "2025-12"
    assert previous_month(date(2026, 10, 1)) == "2026-09"
