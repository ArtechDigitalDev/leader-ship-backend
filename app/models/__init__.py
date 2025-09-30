# app/models/__init__.py

from .user import User
from .assessment import Assessment
from .assessment_result import AssessmentResult
from .week import Week
from .daily_lesson import DailyLesson
from .user_journey import UserJourney
from .user_lesson import UserLesson
from .user_progress import UserProgress

# Import Base from database
from app.core.database import Base

__all__ = [
    "Base",
    "User",
    "Assessment",
    "AssessmentResult",
    "Week",
    "DailyLesson",
    "UserJourney",
    "UserLesson",
    "UserProgress"
]