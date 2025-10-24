from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class UserProgressBase(BaseModel):
    total_points_earned: int = 0
    total_lessons_completed: int = 0
    total_weeks_completed: int = 0
    total_categories_completed: int = 0
    current_category: Optional[str] = None
    current_week_number: Optional[int] = None
    current_streak_days: int = 0
    longest_streak_days: int = 0
    last_activity_date: Optional[date] = None


class UserProgressCreate(UserProgressBase):
    user_id: int
    current_journey_id: Optional[int] = None


class UserProgressUpdate(BaseModel):
    total_points_earned: Optional[int] = None
    total_lessons_completed: Optional[int] = None
    total_weeks_completed: Optional[int] = None
    total_categories_completed: Optional[int] = None
    current_journey_id: Optional[int] = None
    current_category: Optional[str] = None
    current_week_number: Optional[int] = None
    current_streak_days: Optional[int] = None
    longest_streak_days: Optional[int] = None
    last_activity_date: Optional[date] = None


class UserProgressInDB(UserProgressBase):
    id: int
    user_id: int
    current_journey_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProgress(UserProgressInDB):
    pass


class UserProgressWithStats(UserProgress):
    # Additional calculated stats
    average_points_per_lesson: Optional[float] = None
    completion_rate: Optional[float] = None
    days_since_last_activity: Optional[int] = None
    get_current_lesson_miss_day_count: Optional[int] = None
    next_milestone: Optional[str] = None


class ProgressUpdateRequest(BaseModel):
    points_earned: Optional[int] = None
    lesson_completed: Optional[bool] = None
    week_completed: Optional[bool] = None
    category_completed: Optional[bool] = None
    streak_updated: Optional[bool] = None
