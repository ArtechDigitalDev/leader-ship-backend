from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class WeeklyChallengeBase(BaseModel):
    challenge_title: str
    action: str
    why_details: List[str]
    validation_step: Optional[str] = None


class WeekBase(BaseModel):
    topic: str = Field(..., description="Five categories: Clarity, Consistency, Connection, Courage, Curiosity")
    week_number: int = Field(..., ge=1, le=7, description="Week number from 1 to 7")
    title: str
    intro: str
    weekly_challenge: Optional[WeeklyChallengeBase] = None


class WeekCreate(WeekBase):
    pass


class WeekUpdate(BaseModel):
    topic: Optional[str] = None
    week_number: Optional[int] = Field(None, ge=1, le=7)
    title: Optional[str] = None
    intro: Optional[str] = None
    weekly_challenge: Optional[WeeklyChallengeBase] = None


class WeekResponse(WeekBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
