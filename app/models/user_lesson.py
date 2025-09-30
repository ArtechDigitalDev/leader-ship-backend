from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class LessonStatus(str, enum.Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    COMPLETED = "completed"


class UserLesson(Base):
    __tablename__ = "user_lessons"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_journey_id = Column(Integer, ForeignKey("user_journeys.id"), nullable=False)
    daily_lesson_id = Column(Integer, ForeignKey("daily_lessons.id"), nullable=False)
    
    # Lesson progress
    status = Column(Enum(LessonStatus), default=LessonStatus.LOCKED, nullable=False)
    points_earned = Column(Integer, default=0)  # 0-25 points per lesson
    
    # Timing
    unlocked_at = Column(DateTime(timezone=True), nullable=True)  # When lesson became available
    started_at = Column(DateTime(timezone=True), nullable=True)   # When user started the lesson
    completed_at = Column(DateTime(timezone=True), nullable=True) # When user completed the lesson
    
    # User-defined progression
    days_between_lessons = Column(Integer, default=1)  # User can set 1/2/3 days
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_lessons")
    user_journey = relationship("UserJourney", back_populates="user_lessons")
    daily_lesson = relationship("DailyLesson", back_populates="user_lessons")
    
    def __repr__(self):
        return f"<UserLesson(id={self.id}, user_id={self.user_id}, daily_lesson_id={self.daily_lesson_id}, status={self.status})>"
