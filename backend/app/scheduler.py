"""APScheduler loop: every tick, find companies that are due, fetch them
concurrently (bounded), one failure never blocks the rest."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from .config import settings
from .db import SessionLocal
from .ingest import poll_company
from .models import Company

log = logging.getLogger("jobradar.scheduler")
scheduler = AsyncIOScheduler()


async def tick():
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        companies = db.execute(select(Company).where(Company.enabled == True)).scalars().all()
        due = []
        for c in companies:
            interval = c.poll_interval_seconds or settings.DEFAULT_POLL_INTERVAL_SECONDS
            # Back off failing companies: interval doubles per consecutive failure (capped).
            interval *= min(2 ** min(c.consecutive_failures, 5), 32)
            last = c.last_checked_at
            if last is not None and last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            if last is None or last + timedelta(seconds=interval) <= now:
                due.append(c.id)
    if not due:
        return
    log.info("polling %d companies", len(due))
    sem = asyncio.Semaphore(settings.MAX_CONCURRENT_FETCHES)
    headers = {"User-Agent": "JobRadar/1.0 (personal job-search dashboard)"}
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        async def run_one(cid: int):
            async with sem:
                with SessionLocal() as db:
                    return await poll_company(cid, client, db)
        results = await asyncio.gather(*(run_one(cid) for cid in due), return_exceptions=True)
    ok = sum(1 for r in results if isinstance(r, dict) and "error" not in r)
    log.info("tick done ok=%d failed=%d", ok, len(results) - ok)


def start():
    scheduler.add_job(tick, "interval", seconds=settings.SCHEDULER_TICK_SECONDS, max_instances=1, coalesce=True)
    scheduler.start()
    log.info("scheduler started tick=%ss", settings.SCHEDULER_TICK_SECONDS)
