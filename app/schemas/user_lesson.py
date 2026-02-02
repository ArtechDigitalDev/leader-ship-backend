from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.user_lesson import LessonStatus


class UserLessonBase(BaseModel):
    status: LessonStatus = LessonStatus.LOCKED
    points_earned: int = 0
    commit_text: Optional[str] = None
    commit_by_days: Optional[int] = None  # Any number of days (frontend can send any value)
    days_between_lessons: int = 1


class UserLessonCreate(UserLessonBase):
    user_id: int
    user_journey_id: int
    daily_lesson_id: int


class UserLessonUpdate(BaseModel):
    status: Optional[LessonStatus] = None
    points_earned: Optional[int] = None
    commit_text: Optional[str] = None
    commit_by_days: Optional[int] = None
    unlocked_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    days_between_lessons: Optional[int] = None


class UserLessonInDB(UserLessonBase):
    id: int
    user_id: int
    user_journey_id: int
    daily_lesson_id: int
    unlocked_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLesson(UserLessonInDB):
    pass


class UserLessonWithDetails(UserLesson):
    # Include daily lesson details
    daily_lesson_title: Optional[str] = None
    daily_lesson_day_number: Optional[int] = None
    week_topic: Optional[str] = None
    week_number: Optional[int] = None


class LessonCompletionRequest(BaseModel):
    points_earned: int
    commit_text: Optional[str] = None


class LessonCommitRequest(BaseModel):
    """User commits to complete this lesson within X days (before actual completion)."""
    commit_by_days: int = Field(..., ge=1, description="By when will you complete this action? (number of days)")
    commit_text: Optional[str] = None


class LessonUnlockRequest(BaseModel):
    days_between_lessons: int = 1
