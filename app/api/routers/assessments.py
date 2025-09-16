from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services import assessment_service as crud
from app.api import deps
from app.schemas.assessment import (
    AssessmentCreate, AssessmentResponse, AssessmentUpdate
)
from app.models.user import User
from app.utils.response import APIResponse

router = APIRouter()


# Basic CRUD operations only

@router.post("/", response_model=APIResponse)
def create_assessment(
    *,
    db: Session = Depends(deps.get_db),
    assessment_in: AssessmentCreate,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Create new assessment (Admin only).
    """
    assessment = crud.create_assessment(db, obj_in=assessment_in)
    return APIResponse(
        success=True,
        message="Assessment created successfully",
        data={
            "id": assessment.id,
            "category": assessment.category,
            "question": assessment.question,
            "is_active": assessment.is_active,
            "created_at": assessment.created_at
        }
    )


@router.get("/{assessment_id}", response_model=APIResponse)
def get_assessment(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Get assessment by ID.
    """
    assessment = crud.get_assessment(db, assessment_id=assessment_id)
    if not assessment:
        return APIResponse(
            success=False,
            message="Assessment not found",
            data=None
        )
    
    return APIResponse(
        success=True,
        message="Assessment retrieved successfully",
        data={
            "id": assessment.id,
            "category": assessment.category,
            "question": assessment.question,
            "is_active": assessment.is_active,
            "created_at": assessment.created_at,
            "updated_at": assessment.updated_at
        }
    )


@router.put("/{assessment_id}", response_model=APIResponse)
def update_assessment(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    assessment_in: AssessmentUpdate,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Update assessment (Admin only).
    """
    assessment = crud.get_assessment(db, assessment_id=assessment_id)
    if not assessment:
        return APIResponse(
            success=False,
            message="Assessment not found",
            data=None
        )
    
    updated_assessment = crud.update_assessment(db, db_obj=assessment, obj_in=assessment_in)
    return APIResponse(
        success=True,
        message="Assessment updated successfully",
        data={
            "id": updated_assessment.id,
            "category": updated_assessment.category,
            "question": updated_assessment.question,
            "is_active": updated_assessment.is_active,
            "created_at": updated_assessment.created_at,
            "updated_at": updated_assessment.updated_at
        }
    )


@router.delete("/{assessment_id}")
def delete_assessment(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Delete assessment (Admin only).
    """
    assessment = crud.delete_assessment(db, assessment_id=assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    return {"message": "Assessment deleted successfully"}


