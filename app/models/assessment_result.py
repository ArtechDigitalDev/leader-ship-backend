from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Individual category scores (5-25 each)
    clarity_score = Column(Integer, nullable=False)
    consistency_score = Column(Integer, nullable=False)
    connection_score = Column(Integer, nullable=False)
    courage_score = Column(Integer, nullable=False)
    curiosity_score = Column(Integer, nullable=False)
    
    # Total score (25-125)
    total_score = Column(Integer, nullable=False)
    
    # Calculated results
    growth_focus = Column(String, nullable=False)  # Lowest scoring category
    intentional_advantage = Column(String, nullable=False)  # Highest scoring category
    
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="assessment_results")
    user_journeys = relationship("UserJourney", back_populates="assessment_result")
    
    @staticmethod
    def calculate_scores(responses: dict):
        """Calculate scores from responses"""
        categories = ['clarity', 'consistency', 'connection', 'courage', 'curiosity']
        scores = {}
        
        for category in categories:
            category_questions = [q for q in responses.keys() if q.startswith(category)]
            category_score = sum(responses[q] for q in category_questions)
            scores[f"{category}_score"] = category_score
        
        # Calculate total score
        total_score = sum(scores.values())
        
        # Find growth focus (lowest score) and intentional advantage (highest score)
        category_scores = {
            'clarity': scores['clarity_score'],
            'consistency': scores['consistency_score'],
            'connection': scores['connection_score'],
            'courage': scores['courage_score'],
            'curiosity': scores['curiosity_score']
        }
        
        growth_focus = min(category_scores, key=category_scores.get).title()
        intentional_advantage = max(category_scores, key=category_scores.get).title()
        
        return scores, total_score, growth_focus, intentional_advantage
