import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..auth import require_user
from ..config import now_local
from ..db import get_db
from ..models import Entry, Project
from ..queries import entries_between, month_bounds, running_entry, to_out
from ..schemas import MONTH, EntryIn, EntryOut, TimerStartIn

router = APIRouter(prefix="/api", tags=["entries"], dependencies=[Depends(require_user)])

MonthQuery = Query(pattern=MONTH.pattern, description="YYYY-MM")


def _get(db: Session, entry_id: int) -> Entry:
    entry = db.get(Entry, entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")
    return entry


def _check_project(db: Session, project_id: int | None) -> None:
    if project_id is not None and not db.get(Project, project_id):
        raise HTTPException(422, "Unknown project")


def _check_single_running(db: Session, body: EntryIn, entry_id: int | None = None) -> None:
    if body.ended_at is not None:
        return
    current = running_entry(db)
    if current and current.id != entry_id:
        raise HTTPException(409, "Another timer is already running - stop it first")


@router.get("/entries", response_model=list[EntryOut])
def list_entries(
    month: str = MonthQuery,
    project_id: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    start, end = month_bounds(month)
    stmt = select(Entry).where(Entry.started_at >= start, Entry.started_at < end)
    if project_id is not None:
        stmt = stmt.where(Entry.project_id == (None if project_id == 0 else project_id))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Entry.title.ilike(like), Entry.notes.ilike(like)))
    stmt = stmt.order_by(Entry.started_at.desc())
    return [to_out(e) for e in db.scalars(stmt)]


@router.post("/entries", response_model=EntryOut, status_code=201)
def create_entry(body: EntryIn, db: Session = Depends(get_db)):
    _check_project(db, body.project_id)
    _check_single_running(db, body)
    entry = Entry(**body.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return to_out(entry)


@router.put("/entries/{entry_id}", response_model=EntryOut)
def update_entry(entry_id: int, body: EntryIn, db: Session = Depends(get_db)):
    entry = _get(db, entry_id)
    _check_project(db, body.project_id)
    _check_single_running(db, body, entry_id)
    for k, v in body.model_dump().items():
        setattr(entry, k, v)
    db.commit()
    db.refresh(entry)
    return to_out(entry)


@router.delete("/entries/{entry_id}", status_code=204)
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    db.delete(_get(db, entry_id))
    db.commit()


@router.get("/timer")
def current_timer(db: Session = Depends(get_db)):
    # "now" lets the browser tick the clock without trusting its own timezone.
    entry = running_entry(db)
    return {"entry": to_out(entry) if entry else None, "now": now_local()}


@router.post("/timer/start", response_model=EntryOut, status_code=201)
def start_timer(body: TimerStartIn, db: Session = Depends(get_db)):
    _check_project(db, body.project_id)
    now = now_local()
    # Starting new work implicitly finishes whatever was running.
    current = running_entry(db)
    if current:
        current.ended_at = max(now, current.started_at)
    entry = Entry(**body.model_dump(), started_at=now)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return to_out(entry)


@router.post("/timer/stop", response_model=EntryOut)
def stop_timer(db: Session = Depends(get_db)):
    entry = running_entry(db)
    if not entry:
        raise HTTPException(409, "No timer is running")
    entry.ended_at = max(now_local(), entry.started_at)
    db.commit()
    db.refresh(entry)
    return to_out(entry)


@router.get("/entries/export.csv")
def export_csv(month: str = MonthQuery, db: Session = Depends(get_db)):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Date", "Start", "End", "Minutes", "Project", "Title", "Notes"])
    for e in entries_between(db, *month_bounds(month)):
        writer.writerow([
            e.started_at.date().isoformat(),
            e.started_at.strftime("%H:%M"),
            e.ended_at.strftime("%H:%M") if e.ended_at else "running",
            e.minutes(),
            e.project.name if e.project else "",
            e.title,
            e.notes,
        ])
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="worklog-{month}.csv"'},
    )
