"""Fetch → normalize → dedupe → upsert → score → alerts, for one company."""
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from .connectors import CONNECTORS, FetchError
from .dedupe import content_hash, fingerprint
from .models import Alert, AlertEvent, Company, Job, JobSnapshot, JobSource
from .normalize import normalize
from .preferences import get_preferences
from .scoring import score_job

log = logging.getLogger("jobradar.ingest")


async def poll_company(company_id: int, client: httpx.AsyncClient, db: Session) -> dict:
    company = db.get(Company, company_id)
    if not company:
        return {"company": company_id, "error": "not found"}
    connector = CONNECTORS.get(company.ats_type)
    now = datetime.now(timezone.utc)
    result = {"company": company.name, "new": 0, "updated": 0, "total": 0}
    try:
        if not connector:
            raise FetchError(f"no connector for ats_type='{company.ats_type}' — run detect or set it")
        raw_jobs = await connector.get_jobs(company, client)
        result["total"] = len(raw_jobs)
        prefs = get_preferences(db)
        seen_ids = set()
        for raw in raw_jobs:
            fields = normalize(raw)
            fp = fingerprint(company.id, fields["title"], fields["location"], fields["apply_url"])
            job = _find_existing(db, company.id, fields["external_job_id"], fp)
            ch = content_hash(fields["title"], fields["location"], fields["description"], fields["salary_raw"])
            if job is None:
                job = Job(company_id=company.id, fingerprint=fp, ats_provider=company.ats_type,
                          first_seen_at=now, last_seen_at=now, is_active=True, status="New", **fields)
                score, explanation = score_job({**fields, "first_seen_at": now}, prefs, now)
                job.match_score, job.match_explanation = score, explanation
                db.add(job)
                db.flush()
                db.add(JobSource(job_id=job.id, provider=company.ats_type, url=fields["source_url"]))
                db.add(JobSnapshot(job_id=job.id, payload=raw.raw, content_hash=ch))
                result["new"] += 1
            else:
                # Reappearing/ongoing job: only treat as changed if meaningful fields differ.
                last_snap = db.execute(
                    select(JobSnapshot).where(JobSnapshot.job_id == job.id).order_by(JobSnapshot.captured_at.desc()).limit(1)
                ).scalar_one_or_none()
                if last_snap is None or last_snap.content_hash != ch:
                    for k, v in fields.items():
                        setattr(job, k, v)
                    score, explanation = score_job({**fields, "first_seen_at": job.first_seen_at}, prefs, now)
                    job.match_score, job.match_explanation = score, explanation
                    db.add(JobSnapshot(job_id=job.id, payload=raw.raw, content_hash=ch))
                    result["updated"] += 1
                job.last_seen_at = now
                job.is_active = True
            seen_ids.add(job.id)
        # Jobs no longer on the board → inactive (kept for history/tracking).
        for job in db.execute(select(Job).where(Job.company_id == company.id, Job.is_active == True, Job.is_demo == False)).scalars():
            if job.id not in seen_ids and result["total"] > 0:
                job.is_active = False
        company.last_status = f"ok — {result['total']} jobs, {result['new']} new"
        company.consecutive_failures = 0
        _run_alerts(db, now)
    except FetchError as exc:
        company.last_status = f"error: {exc}"
        company.consecutive_failures += 1
        result["error"] = str(exc)
        log.warning("poll failed company=%s err=%s", company.name, exc)
    except Exception as exc:
        company.last_status = f"error: {exc.__class__.__name__}: {exc}"
        company.consecutive_failures += 1
        result["error"] = str(exc)
        log.exception("poll crashed company=%s", company.name)
    finally:
        company.last_checked_at = now
        db.commit()
    return result


def _find_existing(db: Session, company_id: int, external_id: str, fp: str) -> Job | None:
    if external_id:
        job = db.execute(select(Job).where(Job.company_id == company_id, Job.external_job_id == external_id)).scalar_one_or_none()
        if job:
            return job
    return db.execute(select(Job).where(Job.company_id == company_id, Job.fingerprint == fp)).scalar_one_or_none()


def _run_alerts(db: Session, now: datetime):
    """Evaluate alert rules against fresh jobs; AlertEvent unique index prevents duplicates."""
    alerts = db.execute(select(Alert).where(Alert.enabled == True)).scalars().all()
    if not alerts:
        return
    for alert in alerts:
        cutoff_seconds = alert.max_age_minutes * 60
        candidates = db.execute(
            select(Job).where(Job.match_score >= alert.min_score, Job.is_active == True, Job.is_demo == False)
        ).scalars().all()
        for job in candidates:
            fs = job.first_seen_at if job.first_seen_at.tzinfo else job.first_seen_at.replace(tzinfo=timezone.utc)
            if (now - fs).total_seconds() > cutoff_seconds:
                continue
            exists = db.execute(
                select(AlertEvent).where(AlertEvent.alert_id == alert.id, AlertEvent.job_id == job.id)
            ).scalar_one_or_none()
            if exists:
                continue
            db.add(AlertEvent(alert_id=alert.id, job_id=job.id, fired_at=now))
            _deliver(alert, job)


def _deliver(alert: Alert, job: Job):
    channels = alert.channels or []
    # "browser": events are exposed at GET /api/alerts/events; the frontend polls
    # and raises Notification API toasts. "email": sent if SMTP is configured.
    if "email" in channels:
        from .notify import send_email_alert
        send_email_alert(alert, job)
