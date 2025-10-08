from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.schemas.user_preferences import UserPreferencesResponse, UserPreferencesUpdate
from app.utils.response import APIResponse, APIException

router = APIRouter(prefix="/user-preferences", tags=["user-preferences"])


@router.get("/")
async def get_user_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's preferences
    
    Returns user's learning preferences including:
    - Lesson frequency and active days
    - Preferred lesson time
    - Reminder settings
    """
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        raise APIException(
            status_code=404,
            message="User preferences not found",
            success=False
        )
    
    return APIResponse(
        success=True,
        message="User preferences retrieved successfully",
        data=UserPreferencesResponse.model_validate(preferences)
    )


@router.put("/")
async def update_user_preferences(
    preferences_data: UserPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update current user's preferences
    
    Allows users to customize:
    - Learning frequency (daily, weekly, etc.)
    - Active days for lessons
    - Preferred lesson delivery time
    - Reminder settings
    """
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        raise APIException(
            status_code=404,
            message="User preferences not found",
            success=False
        )
    
    # Update only provided fields
    update_data = preferences_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(preferences, field, value)
    
    db.commit()
    db.refresh(preferences)
    
    return APIResponse(
        success=True,
        message="User preferences updated successfully",
        data=UserPreferencesResponse.model_validate(preferences)
    )

