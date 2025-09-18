from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.daily_lesson import DailyLesson
from app.schemas.daily_lesson import DailyLessonCreate, DailyLessonUpdate


def get_daily_lesson(db: Session, *, daily_lesson_id: int) -> Optional[DailyLesson]:
    """Get a daily lesson by ID."""
    from sqlalchemy.orm import joinedload
    return db.query(DailyLesson).options(joinedload(DailyLesson.week)).filter(DailyLesson.id == daily_lesson_id).first()


def get_daily_lesson_by_week_and_day(db: Session, *, week_id: int, day_number: int) -> Optional[DailyLesson]:
    """Get a daily lesson by week ID and day number."""
    from sqlalchemy.orm import joinedload
    return db.query(DailyLesson).options(joinedload(DailyLesson.week)).filter(
        and_(DailyLesson.week_id == week_id, DailyLesson.day_number == day_number)
    ).first()


def get_daily_lessons_by_week(db: Session, *, week_id: int) -> List[DailyLesson]:
    """Get all daily lessons for a specific week."""
    from sqlalchemy.orm import joinedload
    return db.query(DailyLesson).options(joinedload(DailyLesson.week)).filter(DailyLesson.week_id == week_id).order_by(DailyLesson.day_number.asc()).all()


def get_daily_lessons(db: Session) -> List[DailyLesson]:
    """Get all daily lessons."""
    from sqlalchemy.orm import joinedload
    return db.query(DailyLesson).options(joinedload(DailyLesson.week)).order_by(DailyLesson.day_number.asc()).all()


def create_daily_lesson(db: Session, *, obj_in: DailyLessonCreate) -> DailyLesson:
    """Create a new daily lesson."""
    # Check if week exists
    from app.models.week import Week
    week = db.query(Week).filter(Week.id == obj_in.week_id).first()
    if not week:
        raise ValueError(f"Week does not exist")
    
    # Check if daily lesson already exists for this week and day
    existing_lesson = get_daily_lesson_by_week_and_day(
        db, week_id=obj_in.week_id, day_number=obj_in.day_number
    )
    if existing_lesson:
        raise ValueError(f"Daily lesson for week, day {obj_in.day_number} already exists")
    
    db_obj = DailyLesson(
        week_id=obj_in.week_id,
        day_number=obj_in.day_number,
        title=obj_in.title,
        daily_tip=obj_in.daily_tip.dict(),
        swipe_cards=[card.dict() for card in obj_in.swipe_cards],
        scenario=obj_in.scenario.dict(),
        go_deeper=[item.dict() for item in obj_in.go_deeper],
        reflection_prompt=obj_in.reflection_prompt,
        leader_win=obj_in.leader_win
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_daily_lesson(
    db: Session, *, db_obj: DailyLesson, obj_in: Union[DailyLessonUpdate, Dict[str, Any]]
) -> DailyLesson:
    """Update a daily lesson."""
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.dict(exclude_unset=True)
    
    # Check if week_id or day_number is being updated
    new_week_id = update_data.get('week_id', db_obj.week_id)
    new_day_number = update_data.get('day_number', db_obj.day_number)
    
    # If week_id or day_number is changing, check for duplicates
    if (update_data.get('week_id') is not None or update_data.get('day_number') is not None):
        existing_lesson = get_daily_lesson_by_week_and_day(
            db, week_id=new_week_id, day_number=new_day_number
        )
        if existing_lesson and existing_lesson.id != db_obj.id:
            # Get week title for better error message
            from app.models.week import Week
            week = db.query(Week).filter(Week.id == new_week_id).first()
            week_title = week.title if week else f"Week ID {new_week_id}"
            raise ValueError(f"Daily lesson for {week_title}, day {new_day_number} already exists. Please choose a different day number.")
    
    # Handle nested objects - convert Pydantic models to dict if needed
    if "daily_tip" in update_data and update_data["daily_tip"] is not None:
        if hasattr(update_data["daily_tip"], 'dict'):
            update_data["daily_tip"] = update_data["daily_tip"].dict()
    
    if "swipe_cards" in update_data and update_data["swipe_cards"] is not None:
        if update_data["swipe_cards"] and hasattr(update_data["swipe_cards"][0], 'dict'):
            update_data["swipe_cards"] = [card.dict() for card in update_data["swipe_cards"]]
    
    if "scenario" in update_data and update_data["scenario"] is not None:
        if hasattr(update_data["scenario"], 'dict'):
            update_data["scenario"] = update_data["scenario"].dict()
    
    if "go_deeper" in update_data and update_data["go_deeper"] is not None:
        if update_data["go_deeper"] and hasattr(update_data["go_deeper"][0], 'dict'):
            update_data["go_deeper"] = [item.dict() for item in update_data["go_deeper"]]
    
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_daily_lesson(db: Session, *, daily_lesson_id: int) -> DailyLesson:
    """Delete a daily lesson."""
    obj = db.query(DailyLesson).get(daily_lesson_id)
    db.delete(obj)
    db.commit()
    return obj
