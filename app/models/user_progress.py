from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)  # One row per user
    
    # Overall statistics
    total_points_earned = Column(Integer, default=0)
    total_lessons_completed = Column(Integer, default=0)
    total_weeks_completed = Column(Integer, default=0)
    total_categories_completed = Column(Integer, default=0)
    
    # Current status
    current_journey_id = Column(Integer, ForeignKey("user_journeys.id"), nullable=True)
    current_category = Column(String(20), nullable=True)
    current_week_number = Column(Integer, nullable=True)
    
    # Streaks and achievements
    current_streak_days = Column(Integer, default=0)
    longest_streak_days = Column(Integer, default=0)
    last_activity_date = Column(Date, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_progress")
    current_journey = relationship("UserJourney")
    
    def __repr__(self):
        return f"<UserProgress(user_id={self.user_id}, total_points={self.total_points_earned}, current_category={self.current_category})>"
