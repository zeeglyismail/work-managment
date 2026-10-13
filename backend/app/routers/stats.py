from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import require_user
from ..config import now_local
from ..db import get_db
from ..queries import entries_between

router = APIRouter(prefix="/api", tags=["stats"], dependencies=[Depends(require_user)])

TREND_DAYS = 14


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    now = now_local()
    today = datetime(now.year, now.month, now.day)
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    trend_start = today - timedelta(days=TREND_DAYS - 1)

    since = min(month_start, trend_start, week_start)
    entries = entries_between(db, since, today + timedelta(days=1))

    totals = {"today": 0, "week": 0, "month": 0}
    by_day: dict[str, int] = defaultdict(int)
    by_project: dict[tuple, int] = defaultdict(int)
    month_days: set = set()

    for e in entries:
        minutes = e.minutes(until=now)
        day = e.started_at.date()
        if e.started_at >= today:
            totals["today"] += minutes
        if e.started_at >= week_start:
            totals["week"] += minutes
        if e.started_at >= month_start:
            totals["month"] += minutes
            month_days.add(day)
            key = (e.project.name, e.project.color) if e.project else ("No project", "#9ca3af")
            by_project[key] += minutes
        if e.started_at >= trend_start:
            by_day[day.isoformat()] += minutes

    trend = []
    for i in range(TREND_DAYS):
        d = (trend_start + timedelta(days=i)).date().isoformat()
        trend.append({"date": d, "minutes": by_day.get(d, 0)})

    return {
        "now": now,
        "today_minutes": totals["today"],
        "week_minutes": totals["week"],
        "month_minutes": totals["month"],
        "month_days_worked": len(month_days),
        "by_project": [
            {"name": n, "color": c, "minutes": m}
            for (n, c), m in sorted(by_project.items(), key=lambda kv: -kv[1])
        ],
        "trend": trend,
    }
