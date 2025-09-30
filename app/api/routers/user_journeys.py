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
    UserJourneyWithProgress
)
from app.utils.response import APIException

router = APIRouter(prefix="/user-journeys", tags=["user-journeys"])


@router.post("/start", response_model=UserJourney)
async def start_user_journey(
    assessment_result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Start a new user journey based on assessment results"""
    try:
        service = UserJourneyService(db)
        
        # Check if user already has an active journey
        active_journey = service.get_active_user_journey(current_user.id)
        if active_journey:
            raise APIException(
                status_code=400,
                message="User already has an active journey. Complete or pause current journey first.",
                success=False
            )
        
        journey_data = UserJourneyCreate(
            user_id=current_user.id,
            assessment_result_id=assessment_result_id,
            growth_focus_category="",  # Will be set from assessment
            intentional_advantage_category="",  # Will be set from assessment
            current_category=""  # Will be set from assessment
        )
        
        journey = service.create_user_journey(journey_data)
        return journey
        
    except ValueError as e:
        raise APIException(
            status_code=400,
            message=str(e),
            success=False
        )
    except Exception as e:
        raise APIException(
            status_code=500,
            message="Failed to start user journey",
            success=False
        )


@router.get("/active", response_model=UserJourney)
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
    
    return journey


@router.get("/{journey_id}", response_model=UserJourney)
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
    
    return journey


@router.get("/", response_model=List[UserJourney])
async def get_user_journeys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all journeys for the current user"""
    service = UserJourneyService(db)
    
    # This would need to be implemented in the service
    journeys = db.query(service.model).filter(
        service.model.user_id == current_user.id
    ).order_by(service.model.created_at.desc()).all()
    
    return journeys


@router.put("/{journey_id}", response_model=UserJourney)
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
    
    return journey


@router.post("/{journey_id}/complete-category", response_model=UserJourney)
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
    
    return journey


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
    update_data = UserJourneyUpdate(status="paused")
    updated_journey = service.update_user_journey(journey_id, current_user.id, update_data)
    
    return {"message": "Journey paused successfully", "success": True}
