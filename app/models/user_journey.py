from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class JourneyStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


class UserJourney(Base):
    __tablename__ = "user_journeys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assessment_result_id = Column(Integer, ForeignKey("assessment_results.id"), nullable=False)
    
    # Journey configuration
    growth_focus_category = Column(String(20), nullable=True)  # 'clarity', 'consistency', etc.
    intentional_advantage_category = Column(String(20), nullable=True)
    current_category = Column(String(20), nullable=True)  # Which category user is currently working on
    
    # Journey status
    status = Column(Enum(JourneyStatus), default=JourneyStatus.ACTIVE, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Progress tracking
    total_categories_completed = Column(Integer, default=0)
    total_weeks_completed = Column(Integer, default=0)
    total_lessons_completed = Column(Integer, default=0)
    categories_completed = Column(ARRAY(String), default=list)  # Array of completed categories
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_journeys")
    assessment_result = relationship("AssessmentResult", back_populates="user_journeys")
    user_lessons = relationship("UserLesson", back_populates="user_journey", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserJourney(id={self.id}, user_id={self.user_id}, current_category={self.current_category}, status={self.status})>"
