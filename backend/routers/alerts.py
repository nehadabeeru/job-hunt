from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Alert, AlertEvent, Job
from ..schemas import AlertIn

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(db: Session = Depends(get_db)):
    return [
        {"id": a.id, "name": a.name, "min_score": a.min_score, "max_age_minutes": a.max_age_minutes,
         "channels": a.channels, "enabled": a.enabled}
        for a in db.execute(select(Alert)).scalars()
    ]


@router.post("", status_code=201)
def create_alert(body: AlertIn, db: Session = Depends(get_db)):
    a = Alert(**body.model_dump())
    db.add(a)
    db.commit()
    return {"id": a.id}


@router.delete("/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if not a:
        raise HTTPException(404, "alert not found")
    db.delete(a)
    db.commit()
    return {"ok": True}


@router.get("/events")
def unseen_events(db: Session = Depends(get_db)):
    """Browser channel: the frontend polls this and shows Notification toasts."""
    rows = db.execute(
        select(AlertEvent, Job).join(Job, AlertEvent.job_id == Job.id).where(AlertEvent.seen == False).order_by(AlertEvent.fired_at.desc()).limit(20)
    ).all()
    out = []
    for ev, job in rows:
        out.append({"id": ev.id, "job_id": job.id, "title": job.title, "score": job.match_score,
                    "company_id": job.company_id, "fired_at": ev.fired_at.isoformat()})
        ev.seen = True
    db.commit()
    return out
