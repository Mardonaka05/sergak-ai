"""Events (violations) — list, filter, acknowledge, statistics"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.models.event import Event

router = APIRouter()


class EventOut(BaseModel):
    id: int
    timestamp: datetime
    camera_id: int
    module_name: str
    message: str
    confidence: float
    snapshot_path: str
    critical: bool
    acknowledged: bool

    class Config:
        from_attributes = True


@router.get("", response_model=List[EventOut])
async def list_events(
    limit: int = 50,
    camera_id: Optional[int] = None,
    module: Optional[str] = None,
    since: Optional[datetime] = None,
    only_critical: bool = False,
    db: AsyncSession = Depends(get_db),
):
    q = select(Event).order_by(desc(Event.timestamp)).limit(limit)
    if camera_id: q = q.where(Event.camera_id == camera_id)
    if module: q = q.where(Event.module_name == module)
    if since: q = q.where(Event.timestamp >= since)
    if only_critical: q = q.where(Event.critical == True)  # noqa
    res = await db.execute(q)
    return res.scalars().all()


@router.post("/{event_id}/ack")
async def acknowledge_event(event_id: int, db: AsyncSession = Depends(get_db)):
    e = await db.get(Event, event_id)
    if not e: raise HTTPException(404, "Event not found")
    e.acknowledged = True
    e.acknowledged_at = datetime.utcnow()
    await db.commit()
    return {"ok": True}


@router.get("/stats/summary")
async def stats_summary(db: AsyncSession = Depends(get_db)):
    """Dashboard summary stats"""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    yest_start = today_start - timedelta(days=1)
    total_today = (await db.execute(select(func.count(Event.id)).where(Event.timestamp >= today_start))).scalar() or 0
    total_yest = (await db.execute(select(func.count(Event.id)).where(Event.timestamp >= yest_start, Event.timestamp < today_start))).scalar() or 0
    critical_today = (await db.execute(select(func.count(Event.id)).where(Event.timestamp >= today_start, Event.critical == True))).scalar() or 0  # noqa
    return {
        "today_total": total_today,
        "yesterday_total": total_yest,
        "today_critical": critical_today,
        "trend_percent": int(((total_today - total_yest) / max(total_yest, 1)) * 100),
    }


@router.get("/stats/by-module")
async def stats_by_module(days: int = 7, db: AsyncSession = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)
    q = select(Event.module_name, func.count(Event.id)).where(Event.timestamp >= since).group_by(Event.module_name)
    res = await db.execute(q)
    return [{"module": r[0], "count": r[1]} for r in res.all()]


@router.get("/stats/hourly")
async def stats_hourly(days: int = 7, db: AsyncSession = Depends(get_db)):
    """Heatmap data — events count by hour-of-day for last N days.
    DB-agnostic (works for both SQLite and MySQL) — does aggregation in Python."""
    since = datetime.utcnow() - timedelta(days=days)
    q = select(Event.timestamp).where(Event.timestamp >= since)
    res = await db.execute(q)
    buckets = {}
    for (ts,) in res.all():
        if ts is None:
            continue
        # MySQL: Monday=0..Sunday=6; we want Python's weekday() for consistency
        dow = str(ts.weekday())  # 0=Monday, 6=Sunday
        hour = f"{ts.hour:02d}"
        key = (dow, hour)
        buckets[key] = buckets.get(key, 0) + 1
    return [{"dow": dow, "hour": hour, "count": cnt}
            for (dow, hour), cnt in sorted(buckets.items())]
