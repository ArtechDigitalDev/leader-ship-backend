from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class TimezoneEnum(str, Enum):
    """Supported timezone options"""
    ET = "ET"  # Eastern Time (UTC-5/-4)
    CT = "CT"  # Central Time (UTC-6/-5)
    MT = "MT"  # Mountain Time (UTC-7/-6)
    PT = "PT"  # Pacific Time (UTC-8/-7)
    BDT = "BDT"  # Bangladesh Time (UTC+6)


class UserPreferencesBase(BaseModel):
    """Base schema for user preferences"""
    frequency: str = Field(default="daily", description="Learning frequency")
    active_days: List[str] = Field(
        default=["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        description="Days when lessons should be available"
    )
    lesson_time: str = Field(default="09:00", description="Preferred lesson delivery time (HH:MM)")
    timezone: str = Field(default="ET", description="User's timezone (ET, CT, MT, PT, BDT)")
    days_between_lessons: int = Field(default=1, description="Days between lesson unlocks")
    reminder_enabled: str = Field(default="true", description="Enable/disable reminders")
    reminder_time: str = Field(default="14:00", description="Reminder time (HH:MM)")
    reminder_type: str = Field(default="1", description="Follow-up reminder count (0=No reminders, 1=Send 1 reminder, 2=Send 2 reminders)")
    
    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v):
        """Validate timezone is one of the supported options"""
        valid_timezones = ["ET", "CT", "MT", "PT", "BDT"]
        if v not in valid_timezones:
            raise ValueError(f"Timezone must be one of: {', '.join(valid_timezones)}")
        return v


class UserPreferencesResponse(UserPreferencesBase):
    """Response schema for user preferences"""
    id: int
    user_id: int
    
    model_config = {"from_attributes": True}


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences - all fields optional"""
    frequency: Optional[str] = None
    active_days: Optional[List[str]] = None
    lesson_time: Optional[str] = None
    timezone: Optional[str] = None
    days_between_lessons: Optional[int] = None
    reminder_enabled: Optional[str] = None
    reminder_time: Optional[str] = None
    reminder_type: Optional[str] = None

