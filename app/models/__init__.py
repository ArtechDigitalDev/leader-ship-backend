# app/models/__init__.py

from .user import User
from .assessment import Assessment
from .week import Week
from .daily_lesson import DailyLesson

# Import Base from database
from app.core.database import Base

__all__ = [
    "Base",
    "User",
    "Assessment",
    "Week",
    "DailyLesson"
]