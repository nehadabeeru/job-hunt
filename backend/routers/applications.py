from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Application, Job
from ..schemas import ApplicationStageUpdate

router = APIRouter(prefix="/api/applications", tags=["applications"])

STAGES = ["applied", "recruiter_screen", "interview", "offer", "rejected"]


@router.get("")
def list_applications(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Application, Job).join(Job, Application.job_id == Job.id).order_by(Application.applied_at.desc())
    ).all()
    return [
        {"id": a.id, "job_id": j.id, "title": j.title, "company_id": j.company_id,
         "applied_at": a.applied_at.isoformat(), "stage": a.stage, "notes": a.notes, "apply_url": j.apply_url}
        for a, j in rows
    ]


@router.patch("/{app_id}")
def update_stage(app_id: int, body: ApplicationStageUpdate, db: Session = Depends(get_db)):
    if body.stage not in STAGES:
        raise HTTPException(422, f"stage must be one of {STAGES}")
    a = db.get(Application, app_id)
    if not a:
        raise HTTPException(404, "application not found")
    a.stage = body.stage
    if body.notes:
        a.notes = body.notes
    # Keep job status in sync for the pipeline view.
    job = db.get(Job, a.job_id)
    if job:
        job.status = {"interview": "Interview", "offer": "Interview", "rejected": "Rejected"}.get(body.stage, job.status)
    db.commit()
    return {"ok": True}
