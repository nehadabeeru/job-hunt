from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Application, Company, Job
from ..preferences import get_preferences

router = APIRouter(prefix="/api/stats", tags=["stats"])


def _day_start(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    today = _day_start(now)
    week = today - timedelta(days=now.weekday())
    month = today.replace(day=1)
    prefs = get_preferences(db)

    companies = db.execute(select(func.count()).select_from(Company).where(Company.enabled == True)).scalar_one()
    new_today = db.execute(select(func.count()).select_from(Job).where(Job.first_seen_at >= today)).scalar_one()
    strong_today = db.execute(select(func.count()).select_from(Job).where(Job.first_seen_at >= today, Job.match_score >= 85)).scalar_one()

    def apps_since(dt):
        return db.execute(select(func.count()).select_from(Application).where(Application.applied_at >= dt)).scalar_one()

    apps_today, apps_week, apps_month = apps_since(today), apps_since(week), apps_since(month)
    goal = prefs.get("daily_application_goal", 30)

    # Streak: consecutive days meeting the goal, counted backward. Today only
    # counts if it already hit the goal (it's still in progress otherwise).
    def apps_on(day):
        return db.execute(select(func.count()).select_from(Application).where(
            Application.applied_at >= day, Application.applied_at < day + timedelta(days=1))).scalar_one()

    streak = 0
    day = today if apps_on(today) >= goal else today - timedelta(days=1)
    while streak <= 365 and apps_on(day) >= goal:
        streak += 1
        day -= timedelta(days=1)

    funnel = {
        "applications": db.execute(select(func.count()).select_from(Application)).scalar_one(),
        "recruiter_screens": db.execute(select(func.count()).select_from(Application).where(Application.stage.in_(["recruiter_screen", "interview", "offer"]))).scalar_one(),
        "interviews": db.execute(select(func.count()).select_from(Application).where(Application.stage.in_(["interview", "offer"]))).scalar_one(),
        "offers": db.execute(select(func.count()).select_from(Application).where(Application.stage == "offer")).scalar_one(),
    }
    return {
        "companies_monitored": companies,
        "new_jobs_today": new_today,
        "strong_matches_today": strong_today,
        "applications_today": apps_today,
        "applications_week": apps_week,
        "applications_month": apps_month,
        "daily_goal": goal,
        "streak_days": streak,
        "funnel": funnel,
    }
