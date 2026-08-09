from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import UserPreference
from .profile_defaults import DEFAULT_PREFERENCES


def get_preferences(db: Session) -> dict:
    row = db.execute(select(UserPreference)).scalar_one_or_none()
    if row is None:
        row = UserPreference(data=DEFAULT_PREFERENCES)
        db.add(row)
        db.commit()
    merged = {**DEFAULT_PREFERENCES, **(row.data or {})}
    return merged


def update_preferences(db: Session, data: dict) -> dict:
    row = db.execute(select(UserPreference)).scalar_one_or_none()
    if row is None:
        row = UserPreference(data={})
        db.add(row)
    row.data = {**(row.data or {}), **data}
    db.commit()
    return {**DEFAULT_PREFERENCES, **row.data}
