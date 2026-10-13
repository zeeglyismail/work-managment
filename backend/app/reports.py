import asyncio
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam
from fastapi.responses import FileResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth import require_user
from .config import now_local, settings
from .db import SessionLocal, get_db
from .models import Entry
from .pdf import render_month_report
from .queries import entries_between, month_bounds, previous_month
from .schemas import MONTH

log = logging.getLogger("worklog")

router = APIRouter(prefix="/api/reports", tags=["reports"], dependencies=[Depends(require_user)])

MonthPath = PathParam(pattern=MONTH.pattern)
CHECK_INTERVAL_SECONDS = 60 * 60


def archive_path(month: str) -> Path:
    return settings.reports_dir / f"work-report-{month}.pdf"


def build_report(db: Session, month: str) -> bytes:
    entries = entries_between(db, *month_bounds(month))
    return render_month_report(month, entries, settings.owner_name, now_local())


def write_archive(db: Session, month: str) -> Path:
    path = archive_path(month)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(build_report(db, month))
    tmp.replace(path)
    return path


def ensure_previous_month_archived() -> Path | None:
    """Archive last month's report once the month is over.

    Runs at startup and hourly, so a container that was down on the 1st
    still catches up. An existing archive is never overwritten here.
    """
    month = previous_month(now_local().date())
    path = archive_path(month)
    if path.exists():
        return None
    with SessionLocal() as db:
        if not entries_between(db, *month_bounds(month)):
            return None
        written = write_archive(db, month)
    log.info("Auto-generated monthly report %s", written.name)
    return written


async def auto_report_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(ensure_previous_month_archived)
        except Exception:
            log.exception("Monthly report generation failed")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


@router.get("")
def list_reports(db: Session = Depends(get_db)):
    month_col = func.strftime("%Y-%m", Entry.started_at)
    rows = db.execute(
        select(month_col, func.count(Entry.id)).group_by(month_col)
    ).all()
    months = {m: {"month": m, "entries": n, "archived": None} for m, n in rows}

    if settings.reports_dir.exists():
        for f in settings.reports_dir.glob("work-report-*.pdf"):
            m = f.stem.removeprefix("work-report-")
            item = months.setdefault(m, {"month": m, "entries": 0, "archived": None})
            item["archived"] = {
                "generated_at": datetime.fromtimestamp(f.stat().st_mtime, settings.tz)
                .replace(tzinfo=None, microsecond=0),
                "size": f.stat().st_size,
            }

    current = now_local().strftime("%Y-%m")
    months.setdefault(current, {"month": current, "entries": 0, "archived": None})
    return sorted(months.values(), key=lambda m: m["month"], reverse=True)


@router.get("/{month}/pdf")
def download_live(month: str = MonthPath, db: Session = Depends(get_db)):
    return Response(
        build_report(db, month),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="work-report-{month}.pdf"'},
    )


@router.get("/{month}/archived")
def download_archived(month: str = MonthPath):
    path = archive_path(month)
    if not path.exists():
        raise HTTPException(404, "No archived report for that month")
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@router.post("/{month}/archive")
def regenerate_archive(month: str = MonthPath, db: Session = Depends(get_db)):
    path = write_archive(db, month)
    return {"month": month, "file": path.name}
