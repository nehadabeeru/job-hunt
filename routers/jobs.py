from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Application, Company, Job
from ..preferences import get_preferences
from ..schemas import STATUSES, JobDetailOut, JobOut, StatusUpdate
from ..scoring import score_job

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

SORTS = {
    "newest": Job.first_seen_at.desc(),
    "score": Job.match_score.desc(),
    "company": Company.name.asc(),
    "experience": Job.experience_min_years.asc().nullslast(),
    "salary": Job.salary_max.desc().nullslast(),
}


@router.get("")
def list_jobs(
    db: Session = Depends(get_db),
    q: str = "",
    company_id: int | None = None,
    min_score: float | None = None,
    freshness_hours: float | None = None,
    location: str = "",
    remote: str = "",           # remote|hybrid|onsite
    experience_max: float | None = None,
    salary_min: float | None = None,
    source: str = "",           # greenhouse|lever|ashby|workday
    status: str = "",           # New|Saved|Applied|... or "not_applied"
    active_only: bool = True,
    sort: str = "newest",
    page: int = 1,
    page_size: int = Query(50, le=200),
):
    stmt = select(Job, Company.name).join(Company, Job.company_id == Company.id)
    if active_only:
        stmt = stmt.where(Job.is_active == True)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(func.lower(Job.title).like(like) | func.lower(Job.description).like(like) | func.lower(Company.name).like(like))
    if company_id:
        stmt = stmt.where(Job.company_id == company_id)
    if min_score is not None:
        stmt = stmt.where(Job.match_score >= min_score)
    if freshness_hours is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=freshness_hours)
        stmt = stmt.where(Job.first_seen_at >= cutoff)
    if location:
        stmt = stmt.where(func.lower(Job.location).like(f"%{location.lower()}%"))
    if remote:
        stmt = stmt.where(Job.remote_status == remote)
    if experience_max is not None:
        stmt = stmt.where((Job.experience_min_years == None) | (Job.experience_min_years <= experience_max))
    if salary_min is not None:
        stmt = stmt.where(Job.salary_max >= salary_min)
    if source:
        stmt = stmt.where(Job.ats_provider == source)
    if status == "not_applied":
        stmt = stmt.where(Job.status.notin_(["Applied", "Interview", "Rejected", "Skip"]))
    elif status:
        stmt = stmt.where(Job.status == status)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    stmt = stmt.order_by(SORTS.get(sort, SORTS["newest"]), Job.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = db.execute(stmt).all()
    items = []
    for job, company_name in rows:
        out = JobOut.model_validate(job).model_dump()
        out["company_name"] = company_name
        items.append(out)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    out = JobDetailOut.model_validate(job).model_dump()
    out["company_name"] = job.company.name if job.company else ""
    return out


@router.patch("/{job_id}/status")
def set_status(job_id: int, body: StatusUpdate, db: Session = Depends(get_db)):
    if body.status not in STATUSES:
        raise HTTPException(422, f"status must be one of {STATUSES}")
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    job.status = body.status
    if body.status == "Applied":
        exists = db.execute(select(Application).where(Application.job_id == job_id)).scalar_one_or_none()
        if not exists:
            db.add(Application(job_id=job_id))
    db.commit()
    return {"ok": True, "status": job.status}


@router.post("/rescore")
def rescore_all(db: Session = Depends(get_db)):
    """Re-run scoring for all active jobs (after editing preferences/weights)."""
    prefs = get_preferences(db)
    now = datetime.now(timezone.utc)
    count = 0
    for job in db.execute(select(Job).where(Job.is_active == True)).scalars():
        fields = {
            "title": job.title, "description": job.description, "requirements": job.requirements,
            "preferred_qualifications": job.preferred_qualifications, "location": job.location,
            "remote_status": job.remote_status, "experience_min_years": job.experience_min_years,
            "experience_raw": job.experience_raw, "first_seen_at": job.first_seen_at,
        }
        job.match_score, job.match_explanation = score_job(fields, prefs, now)
        count += 1
    db.commit()
    return {"rescored": count}
