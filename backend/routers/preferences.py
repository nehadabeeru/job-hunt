from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..preferences import get_preferences, update_preferences

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


@router.get("")
def read(db: Session = Depends(get_db)):
    return get_preferences(db)


@router.put("")
def write(data: dict = Body(...), db: Session = Depends(get_db)):
    return update_preferences(db, data)
