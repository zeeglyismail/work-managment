import os
import tempfile

# Settings are read at import time, so point the app at a throwaway data dir first.
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="worklog-test-")
os.environ["APP_USERNAME"] = "tester"
os.environ["APP_PASSWORD"] = "s3cret"
os.environ["STATIC_DIR"] = os.path.join(os.environ["DATA_DIR"], "no-frontend")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import auth  # noqa: E402
from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def anon():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    auth._failures.clear()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def client(anon):
    r = anon.post("/api/auth/login", json={"username": "tester", "password": "s3cret"})
    assert r.status_code == 200
    return anon
