import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import auth, reports
from .config import settings
from .db import Base, engine
from .routers import entries, projects, stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

SESSION_DAYS = 30


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.warn_insecure_defaults()
    Base.metadata.create_all(engine)
    task = asyncio.create_task(reports.auto_report_loop())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


app = FastAPI(title="Worklog", lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="worklog_session",
    max_age=SESSION_DAYS * 24 * 3600,
    same_site="lax",
    https_only=settings.cookie_secure,
)

for r in (auth.router, projects.router, entries.router, stats.router, reports.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"ok": True}


# Serve the built React app; any non-API path falls back to index.html so
# client-side routes survive a page refresh.
if settings.static_dir.is_dir():
    index_file = settings.static_dir / "index.html"
    app.mount("/assets", StaticFiles(directory=settings.static_dir / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404)
        candidate = (settings.static_dir / path).resolve()
        if path and candidate.is_file() and settings.static_dir.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(index_file)
