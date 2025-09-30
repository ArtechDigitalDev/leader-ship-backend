from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.user_journey import JourneyStatus


class UserJourneyBase(BaseModel):
    growth_focus_category: str
    intentional_advantage_category: str
    current_category: str
    status: JourneyStatus = JourneyStatus.ACTIVE


class UserJourneyCreate(UserJourneyBase):
    user_id: int
    assessment_result_id: int


class UserJourneyStartRequest(BaseModel):
    """Request schema for starting a new journey"""
    assessment_result_id: int


class UserJourneyUpdate(BaseModel):
    current_category: Optional[str] = None
    status: Optional[JourneyStatus] = None
    total_categories_completed: Optional[int] = None
    total_weeks_completed: Optional[int] = None
    total_lessons_completed: Optional[int] = None
    completed_at: Optional[datetime] = None


class UserJourneyInDB(UserJourneyBase):
    id: int
    user_id: int
    assessment_result_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_categories_completed: int = 0
    total_weeks_completed: int = 0
    total_lessons_completed: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserJourney(UserJourneyInDB):
    pass


class UserJourneyWithProgress(UserJourney):
    # Add progress-related fields for API responses
    current_week_progress: Optional[int] = None
    current_category_progress: Optional[int] = None
    total_lessons_in_current_category: Optional[int] = None
    completed_lessons_in_current_category: Optional[int] = None
