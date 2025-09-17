from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.week import Week
from app.schemas.week import WeekCreate, WeekUpdate


# Week CRUD operations
def create_week(db: Session, *, obj_in: WeekCreate) -> Week:
    """Create a new week"""
    week = Week(**obj_in.dict())
    db.add(week)
    db.commit()
    db.refresh(week)
    return week


def get_week(db: Session, *, week_id: int) -> Optional[Week]:
    """Get week by ID"""
    return db.query(Week).filter(Week.id == week_id).first()


def get_week_by_topic_and_number(db: Session, *, topic: str, week_number: int) -> Optional[Week]:
    """Get week by topic and week number"""
    return db.query(Week).filter(
        and_(Week.topic == topic, Week.week_number == week_number)
    ).first()


def get_weeks_by_topic(db: Session, *, topic: str) -> List[Week]:
    """Get all weeks for a specific topic"""
    return db.query(Week).filter(Week.topic == topic).order_by(Week.week_number).all()


def get_all_weeks(db: Session) -> List[Week]:
    """Get all weeks sorted by topic and week number"""
    return db.query(Week).order_by(Week.topic, Week.week_number).all()


def update_week(db: Session, *, db_obj: Week, obj_in: WeekUpdate) -> Week:
    """Update week"""
    update_data = obj_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_week(db: Session, *, week_id: int) -> bool:
    """Delete week"""
    week = get_week(db, week_id=week_id)
    if week:
        db.delete(week)
        db.commit()
        return True
    return False
