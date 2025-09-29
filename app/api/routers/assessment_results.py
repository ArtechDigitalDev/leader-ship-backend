from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.assessment_result import AssessmentResult
from app.schemas.assessment_result import (
    AssessmentResultResponse, 
    AssessmentSubmission, 
    AssessmentResultSummary,
    AssessmentResultCreate,
    AssessmentResultUpdate
)
from app.services.assessment_result_service import AssessmentResultService
from app.utils.response import APIResponse

router = APIRouter(prefix="/assessment-results", tags=["Assessment Results"])


@router.post("/submit", response_model=APIResponse)
async def submit_assessment(
    assessment_data: AssessmentSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit assessment responses and get calculated results"""
    try:
        service = AssessmentResultService(db)
        
        # Create assessment result
        result = service.create_assessment_result(
            user_id=current_user.id,
            responses=assessment_data.responses
        )
        
        return APIResponse(
            success=True,
            message="Assessment submitted successfully",
            data=AssessmentResultResponse.from_orm(result)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to submit assessment: {str(e)}"
        )


@router.get("/my-results", response_model=APIResponse)
async def get_my_assessment_results(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's assessment results"""
    try:
        service = AssessmentResultService(db)
        results = service.get_user_assessment_results(current_user.id)
        
        return APIResponse(
            success=True,
            message="Assessment results retrieved successfully",
            data=[AssessmentResultResponse.from_orm(result) for result in results]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve assessment results: {str(e)}"
        )


@router.get("/latest", response_model=APIResponse)
async def get_latest_assessment_result(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's latest assessment result"""
    try:
        service = AssessmentResultService(db)
        result = service.get_latest_assessment_result(current_user.id)
        
        if not result:
            return APIResponse(
                success=True,
                message="No assessment results found",
                data=None
            )
        
        return APIResponse(
            success=True,
            message="Latest assessment result retrieved successfully",
            data=AssessmentResultResponse.from_orm(result)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve latest assessment result: {str(e)}"
        )


@router.get("/my-result", response_model=APIResponse)
async def get_my_latest_result(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's latest assessment result (alternative endpoint)"""
    try:
        service = AssessmentResultService(db)
        result = service.get_latest_assessment_result(current_user.id)
        
        if not result:
            return APIResponse(
                success=True,
                message="No assessment results found",
                data=None
            )
        
        return APIResponse(
            success=True,
            message="Latest assessment result retrieved successfully",
            data=AssessmentResultResponse.from_orm(result)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve latest assessment result: {str(e)}"
        )


@router.get("/summary/{result_id}", response_model=APIResponse)
async def get_assessment_summary(
    result_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary of a specific assessment result"""
    try:
        service = AssessmentResultService(db)
        summary = service.get_assessment_result_summary(result_id)
        
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment result not found"
            )
        
        # Check if user owns this result or is admin
        result = service.get_assessment_result(result_id)
        if result.user_id != current_user.id and not current_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this assessment result"
            )
        
        return APIResponse(
            success=True,
            message="Assessment summary retrieved successfully",
            data=summary
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve assessment summary: {str(e)}"
        )


@router.get("/growth-focus", response_model=APIResponse)
async def get_my_growth_focus(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's growth focus from latest assessment"""
    try:
        service = AssessmentResultService(db)
        growth_focus = service.get_user_growth_focus(current_user.id)
        
        if not growth_focus:
            return APIResponse(
                success=True,
                message="No assessment results found",
                data=None
            )
        
        return APIResponse(
            success=True,
            message="Growth focus retrieved successfully",
            data={"growth_focus": growth_focus}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve growth focus: {str(e)}"
        )


@router.get("/intentional-advantage", response_model=APIResponse)
async def get_my_intentional_advantage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's intentional advantage from latest assessment"""
    try:
        service = AssessmentResultService(db)
        intentional_advantage = service.get_user_intentional_advantage(current_user.id)
        
        if not intentional_advantage:
            return APIResponse(
                success=True,
                message="No assessment results found",
                data=None
            )
        
        return APIResponse(
            success=True,
            message="Intentional advantage retrieved successfully",
            data={"intentional_advantage": intentional_advantage}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve intentional advantage: {str(e)}"
        )


# Admin endpoints
@router.get("/admin/all", response_model=APIResponse)
async def get_all_assessment_results(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all assessment results (Admin only)"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this endpoint"
        )
    
    try:
        service = AssessmentResultService(db)
        results = db.query(AssessmentResult).order_by(AssessmentResult.created_at.desc()).all()
        
        return APIResponse(
            success=True,
            message="All assessment results retrieved successfully",
            data=[AssessmentResultResponse.from_orm(result) for result in results]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve all assessment results: {str(e)}"
        )


@router.delete("/{result_id}", response_model=APIResponse)
async def delete_assessment_result(
    result_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an assessment result"""
    try:
        service = AssessmentResultService(db)
        
        # Check if result exists and user has permission
        result = service.get_assessment_result(result_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment result not found"
            )
        
        if result.user_id != current_user.id and not current_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this assessment result"
            )
        
        success = service.delete_assessment_result(result_id)
        
        if success:
            return APIResponse(
                success=True,
                message="Assessment result deleted successfully",
                data=None
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete assessment result"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete assessment result: {str(e)}"
        )
