from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Lesson scheduling preferences
    frequency = Column(String(20), default="daily")  # daily, weekly
    active_days = Column(JSON, default=["mon", "tue", "wed", "thu", "fri", "sat", "sun"])
    lesson_time = Column(String(5), default="09:00")  # HH:MM format
    timezone = Column(String(50), default="UTC")  # Default UTC timezone
    
    # Reminder preferences
    reminder_enabled = Column(String(10), default="true")  # true, false
    reminder_time = Column(String(5), default="14:00")  # HH:MM format
    reminder_type = Column(String(10), default="1")  # 0=No reminders, 1=Send 1 reminder, 2=Send 2 reminders
    
    # Lesson progression
    days_between_lessons = Column(Integer, default=1)  # Minimum days between lessons
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="preferences")
