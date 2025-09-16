from typing import Optional
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentCreate, AssessmentUpdate


# Assessment CRUD operations
def create_assessment(db: Session, *, obj_in: AssessmentCreate) -> Assessment:
    """Create a new assessment"""
    assessment = Assessment(**obj_in.dict())
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def get_assessment(db: Session, *, assessment_id: int) -> Optional[Assessment]:
    """Get assessment by ID"""
    return db.query(Assessment).filter(Assessment.id == assessment_id).first()


def update_assessment(db: Session, *, db_obj: Assessment, obj_in: AssessmentUpdate) -> Assessment:
    """Update assessment"""
    update_data = obj_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj