from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.user_journey_service import UserJourneyService
from app.schemas.user_journey import (
    UserJourneyCreate,
    UserJourneyUpdate,
    UserJourney,
    UserJourneyWithProgress,
    UserJourneyStartRequest
)
from app.utils.response import APIException, APIResponse

router = APIRouter(prefix="/user-journeys", tags=["user-journeys"])


@router.post("/start")
async def start_user_journey(
    request: UserJourneyStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Start a new user journey or continue to next category"""
    try:
        service = UserJourneyService(db)
        
        journey_data = UserJourneyCreate(
            user_id=current_user.id,
            assessment_result_id=request.assessment_result_id,
            growth_focus_category="",  # Will be set from assessment
            intentional_advantage_category="",  # Will be set from assessment
            current_category=""  # Will be set from assessment
        )
        
        # This will either create new journey or update existing one
        journey = service.start_or_update_journey(journey_data)
        
        # Convert to Pydantic schema
        journey_schema = UserJourney.from_orm(journey)
        
        return APIResponse(
            success=True,
            message="User journey started/updated successfully",
            data=journey_schema
        )
        
    except ValueError as e:
        raise APIException(
            status_code=400,
            message=str(e),
            success=False
        )
    except Exception as e:
        raise APIException(
            status_code=500,
            message="Failed to start/update user journey",
            success=False
        )


@router.get("/active")
async def get_active_user_journey(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get the active journey for the current user"""
    service = UserJourneyService(db)
    journey = service.get_active_user_journey(current_user.id)
    
    if not journey:
        raise APIException(
            status_code=404,
            message="No active journey found for user",
            success=False
        )
    
    # Convert to Pydantic schema
    journey_schema = UserJourney.from_orm(journey)
    
    return APIResponse(
        success=True,
        message="Active journey retrieved successfully",
        data=journey_schema
    )


@router.get("/category-progression")
async def get_category_progression(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get category progression based on assessment scores"""
    service = UserJourneyService(db)
    
    # Get user's active journey
    journey = service.get_active_user_journey(current_user.id)
    
    if not journey:
        raise APIException(
            status_code=404,
            message="No active journey found",
            success=False
        )
    
    # Get assessment result
    from app.models.assessment_result import AssessmentResult
    assessment_result = db.query(AssessmentResult).filter(
        AssessmentResult.id == journey.assessment_result_id
    ).first()
    
    if not assessment_result:
        raise APIException(
            status_code=404,
            message="Assessment result not found",
            success=False
        )
    
    # Get categories sorted by scores (lowest to highest)
    category_scores = {
        'Clarity': assessment_result.clarity_score,
        'Consistency': assessment_result.consistency_score,
        'Connection': assessment_result.connection_score,
        'Courage': assessment_result.courage_score,
        'Curiosity': assessment_result.curiosity_score
    }
    
    # Sort categories by score (ascending - lowest first)
    sorted_categories = sorted(category_scores.items(), key=lambda x: x[1])
    
    # Create response data
    progression_data = {
        'current_category': journey.current_category,
        'completed_categories': journey.categories_completed or [],
        'category_order': [{'name': cat, 'score': score} for cat, score in sorted_categories],
        'next_growth_focus': sorted_categories[len(journey.categories_completed or []):] if journey.categories_completed else sorted_categories,
        'journey_status': journey.status,
        'total_categories_completed': journey.total_categories_completed
    }
    
    return APIResponse(
        success=True,
        message="Category progression retrieved successfully",
        data=progression_data
    )


@router.get("/{journey_id}")
async def get_user_journey(
    journey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific user journey"""
    service = UserJourneyService(db)
    journey = service.get_user_journey(current_user.id, journey_id)
    
    if not journey:
        raise APIException(
            status_code=404,
            message="Journey not found",
            success=False
        )
    
    # Convert to Pydantic schema
    journey_schema = UserJourney.from_orm(journey)
    
    return APIResponse(
        success=True,
        message="Journey retrieved successfully",
        data=journey_schema
    )


@router.get("/")
async def get_user_journeys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all journeys for the current user"""
    service = UserJourneyService(db)
    
    # This would need to be implemented in the service
    from app.models.user_journey import UserJourney
    journeys = db.query(UserJourney).filter(
        UserJourney.user_id == current_user.id
    ).order_by(UserJourney.created_at.desc()).all()
    
    # Convert to Pydantic schemas
    journey_schemas = [UserJourney.from_orm(journey) for journey in journeys]
    
    return APIResponse(
        success=True,
        message="User journeys retrieved successfully",
        data=journey_schemas
    )


@router.put("/{journey_id}")
async def update_user_journey(
    journey_id: int,
    update_data: UserJourneyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a user journey"""
    service = UserJourneyService(db)
    journey = service.update_user_journey(journey_id, current_user.id, update_data)
    
    if not journey:
        raise APIException(
            status_code=404,
            message="Journey not found",
            success=False
        )
    
    # Convert to Pydantic schema
    journey_schema = UserJourney.from_orm(journey)
    
    return APIResponse(
        success=True,
        message="Journey updated successfully",
        data=journey_schema
    )


@router.post("/{journey_id}/complete-category")
async def complete_category_and_move_to_next(
    journey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Complete current category and move to next one"""
    service = UserJourneyService(db)
    journey = service.complete_category_and_move_to_next(current_user.id, journey_id)
    
    if not journey:
        raise APIException(
            status_code=404,
            message="Journey not found or category not ready for completion",
            success=False
        )
    
    # Convert to Pydantic schema
    journey_schema = UserJourney.from_orm(journey)
    
    return APIResponse(
        success=True,
        message="Category completed and moved to next successfully",
        data=journey_schema
    )


@router.delete("/{journey_id}")
async def delete_user_journey(
    journey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a user journey (soft delete by marking as paused)"""
    service = UserJourneyService(db)
    journey = service.get_user_journey(current_user.id, journey_id)
    
    if not journey:
        raise APIException(
            status_code=404,
            message="Journey not found",
            success=False
        )
    
    # Soft delete by updating status to paused
    from app.models.user_journey import JourneyStatus
    update_data = UserJourneyUpdate(status=JourneyStatus.PAUSED)
    updated_journey = service.update_user_journey(journey_id, current_user.id, update_data)
    
    return APIResponse(
        success=True,
        message="Journey paused successfully",
        data=updated_journey
    )
