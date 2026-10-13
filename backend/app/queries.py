from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Entry
from .schemas import EntryOut


def month_bounds(month: str) -> tuple[datetime, datetime]:
    year, mon = (int(p) for p in month.split("-"))
    start = datetime(year, mon, 1)
    end = datetime(year + 1, 1, 1) if mon == 12 else datetime(year, mon + 1, 1)
    return start, end


def previous_month(today: date) -> str:
    first = today.replace(day=1)
    prev = first - timedelta(days=1)
    return f"{prev.year:04d}-{prev.month:02d}"


def entries_between(db: Session, start: datetime, end: datetime) -> list[Entry]:
    stmt = (
        select(Entry)
        .where(Entry.started_at >= start, Entry.started_at < end)
        .order_by(Entry.started_at)
    )
    return list(db.scalars(stmt))


def running_entry(db: Session) -> Entry | None:
    return db.scalars(select(Entry).where(Entry.ended_at.is_(None))).first()


def to_out(e: Entry) -> EntryOut:
    return EntryOut(
        id=e.id,
        title=e.title,
        notes=e.notes,
        project_id=e.project_id,
        project_name=e.project.name if e.project else None,
        project_color=e.project.color if e.project else None,
        started_at=e.started_at,
        ended_at=e.ended_at,
        minutes=e.minutes(),
        running=e.ended_at is None,
    )


def fmt_minutes(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h}h {m}m"
    return f"{h}h" if h else f"{m}m"
