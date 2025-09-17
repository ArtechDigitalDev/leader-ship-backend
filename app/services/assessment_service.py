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


def delete_assessment(db: Session, *, assessment_id: int) -> bool:
    """Delete assessment"""
    assessment = get_assessment(db, assessment_id=assessment_id)
    if assessment:
        db.delete(assessment)
        db.commit()
        return True
    return False


def get_assessments_by_category(db: Session) -> dict:
    """Get all assessments grouped by category for participants"""
    assessments = db.query(Assessment).filter(Assessment.is_active == True).all()
    
    # Group by category
    categories = {}
    for assessment in assessments:
        category = assessment.category
        if category not in categories:
            categories[category] = {
                "category": category.lower().replace(" ", "_"),
                "categoryTitle": category.title(),
                "questions": []
            }
        
        # Add question with ID
        categories[category]["questions"].append({
            "id": assessment.id,
            "question": assessment.question
        })
    
    # Convert to list format
    result = list(categories.values())
    return result


def get_all_assessments_sorted_by_category(db: Session) -> list:
    """Get all assessments sorted by category for admins"""
    assessments = db.query(Assessment).order_by(Assessment.category, Assessment.id).all()
    
    result = []
    for assessment in assessments:
        result.append({
            "id": assessment.id,
            "category": assessment.category,
            "question": assessment.question,
            "is_active": assessment.is_active,
            "created_at": assessment.created_at,
            "updated_at": assessment.updated_at
        })
    
    return result