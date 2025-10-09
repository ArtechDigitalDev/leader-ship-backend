from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class CoachStats(BaseModel):
    """Coach dashboard statistics"""
    participants: int
    avg_completion_rate: float
    journey_started: int
    journey_completed: int


class ParticipantOverview(BaseModel):
    """Individual participant overview"""
    user_name: str
    email: str
    progress: float  # Percentage of completion
    categories_completed: List[str]  # List of completed category names
    current_category: Optional[str] = None
    last_completed_lesson: Optional[str] = None
    last_lesson_completed_date: Optional[datetime] = None
    current_lesson_missed_count: int = 0  # Number of times current lesson has been missed


class CoachDashboardResponse(BaseModel):
    """Complete coach dashboard response"""
    coach_stats: CoachStats
    participants_overview: List[ParticipantOverview]


class CoachStatsResponse(BaseModel):
    """Coach statistics response"""
    participants: int
    avg_completion_rate: float
    journey_started: int
    journey_completed: int
