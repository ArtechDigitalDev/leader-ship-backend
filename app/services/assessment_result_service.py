from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.assessment_result import AssessmentResult
from app.schemas.assessment_result import AssessmentResultCreate, AssessmentResultUpdate


class AssessmentResultService:
    def __init__(self, db: Session):
        self.db = db

    def create_assessment_result(self, user_id: int, responses: Dict[str, int]) -> AssessmentResult:
        """Create a new assessment result with calculated scores"""
        # Calculate scores from responses using the static method
        scores, total_score, growth_focus, intentional_advantage = AssessmentResult.calculate_scores(responses)
        
        # Create assessment result
        assessment_result = AssessmentResult(
            user_id=user_id,
            clarity_score=scores['clarity_score'],
            consistency_score=scores['consistency_score'],
            connection_score=scores['connection_score'],
            courage_score=scores['courage_score'],
            curiosity_score=scores['curiosity_score'],
            total_score=total_score,
            growth_focus=growth_focus,
            intentional_advantage=intentional_advantage
        )
        
        self.db.add(assessment_result)
        self.db.commit()
        self.db.refresh(assessment_result)
        
        return assessment_result

    def get_assessment_result(self, result_id: int) -> Optional[AssessmentResult]:
        """Get a specific assessment result by ID"""
        return self.db.query(AssessmentResult).filter(AssessmentResult.id == result_id).first()

    def get_user_assessment_results(self, user_id: int) -> List[AssessmentResult]:
        """Get all assessment results for a specific user"""
        return self.db.query(AssessmentResult).filter(
            AssessmentResult.user_id == user_id
        ).order_by(desc(AssessmentResult.created_at)).all()

    def get_latest_assessment_result(self, user_id: int) -> Optional[AssessmentResult]:
        """Get the latest assessment result for a user"""
        return self.db.query(AssessmentResult).filter(
            AssessmentResult.user_id == user_id
        ).order_by(desc(AssessmentResult.created_at)).first()

    def update_assessment_result(self, result_id: int, update_data: AssessmentResultUpdate) -> Optional[AssessmentResult]:
        """Update an existing assessment result"""
        assessment_result = self.get_assessment_result(result_id)
        if not assessment_result:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(assessment_result, field, value)
        
        # Note: Since we don't store raw responses, we can't recalculate scores from updates
        # If scores need to be updated, the entire assessment should be retaken
        
        self.db.commit()
        self.db.refresh(assessment_result)
        
        return assessment_result

    def delete_assessment_result(self, result_id: int) -> bool:
        """Delete an assessment result"""
        assessment_result = self.get_assessment_result(result_id)
        if not assessment_result:
            return False
        
        self.db.delete(assessment_result)
        self.db.commit()
        return True

    def get_assessment_result_summary(self, result_id: int) -> Optional[Dict[str, Any]]:
        """Get a summary of assessment results"""
        assessment_result = self.get_assessment_result(result_id)
        if not assessment_result:
            return None
        
        return {
            "id": assessment_result.id,
            "user_id": assessment_result.user_id,
            "total_score": assessment_result.total_score,
            "growth_focus": assessment_result.growth_focus,
            "intentional_advantage": assessment_result.intentional_advantage,
            "category_scores": {
                "clarity": assessment_result.clarity_score,
                "consistency": assessment_result.consistency_score,
                "connection": assessment_result.connection_score,
                "courage": assessment_result.courage_score,
                "curiosity": assessment_result.curiosity_score
            },
            "created_at": assessment_result.created_at
        }

    def get_user_growth_focus(self, user_id: int) -> Optional[str]:
        """Get the user's current growth focus from their latest assessment"""
        latest_result = self.get_latest_assessment_result(user_id)
        return latest_result.growth_focus if latest_result else None

    def get_user_intentional_advantage(self, user_id: int) -> Optional[str]:
        """Get the user's current intentional advantage from their latest assessment"""
        latest_result = self.get_latest_assessment_result(user_id)
        return latest_result.intentional_advantage if latest_result else None
