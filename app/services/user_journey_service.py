from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user_journey import UserJourney, JourneyStatus
from app.models.user_lesson import UserLesson, LessonStatus
from app.models.user_progress import UserProgress
from app.models.week import Week
from app.models.daily_lesson import DailyLesson
from app.models.assessment_result import AssessmentResult
from app.schemas.user_journey import UserJourneyCreate, UserJourneyUpdate
from app.utils.response import APIException


class UserJourneyService:
    def __init__(self, db: Session):
        self.db = db

    def create_user_journey(self, journey_data: UserJourneyCreate) -> UserJourney:
        """Create a new user journey based on assessment results"""
        
        # Get assessment result to determine growth focus and intentional advantage
        assessment_result = self.db.query(AssessmentResult).filter(
            AssessmentResult.id == journey_data.assessment_result_id
        ).first()
        
        if not assessment_result:
            raise APIException(
                status_code=404,
                message="Assessment result not found",
                success=False
            )
        
        # Create user journey
        user_journey = UserJourney(
            user_id=journey_data.user_id,
            assessment_result_id=journey_data.assessment_result_id,
            growth_focus_category=assessment_result.growth_focus.lower(),
            intentional_advantage_category=assessment_result.intentional_advantage.lower(),
            current_category=assessment_result.growth_focus.lower(),
            status=JourneyStatus.ACTIVE
        )
        
        self.db.add(user_journey)
        self.db.flush()  # Get the ID
        
        # Initialize lessons for the growth focus category
        self._initialize_lessons_for_category(
            user_journey.id, 
            journey_data.user_id, 
            assessment_result.growth_focus.lower()
        )
        
        # Create or update user progress
        self._create_or_update_user_progress(
            journey_data.user_id, 
            user_journey.id, 
            assessment_result.growth_focus.lower()
        )
        
        self.db.commit()
        self.db.refresh(user_journey)
        
        return user_journey

    def get_user_journey(self, user_id: int, journey_id: int) -> Optional[UserJourney]:
        """Get a specific user journey"""
        journey = self.db.query(UserJourney).filter(
            and_(UserJourney.id == journey_id, UserJourney.user_id == user_id)
        ).first()
        
        if not journey:
            raise APIException(
                status_code=404,
                message="Journey not found",
                success=False
            )
        
        return journey

    def get_active_user_journey(self, user_id: int) -> Optional[UserJourney]:
        """Get the active journey for a user"""
        journey = self.db.query(UserJourney).filter(
            and_(UserJourney.user_id == user_id, UserJourney.status == JourneyStatus.ACTIVE)
        ).first()
        
        # Note: This method returns None if no active journey found
        # The router will handle the 404 response
        return journey

    def update_user_journey(self, journey_id: int, user_id: int, update_data: UserJourneyUpdate) -> UserJourney:
        """Update user journey"""
        user_journey = self.get_user_journey(user_id, journey_id)
        
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(user_journey, field, value)
        
        self.db.commit()
        self.db.refresh(user_journey)
        
        return user_journey

    def complete_category_and_move_to_next(self, user_id: int, journey_id: int) -> UserJourney:
        """Complete current category and move to next one"""
        user_journey = self.get_user_journey(user_id, journey_id)
        
        # Get all categories in order
        categories = ['clarity', 'consistency', 'connection', 'courage', 'curiosity']
        current_index = categories.index(user_journey.current_category)
        
        # Update journey progress
        user_journey.total_categories_completed += 1
        
        # Check if journey is complete
        if current_index + 1 >= len(categories):
            # Journey complete
            user_journey.status = JourneyStatus.COMPLETED
            user_journey.completed_at = datetime.utcnow()
            user_journey.current_category = None
        else:
            # Move to next category
            next_category = categories[current_index + 1]
            user_journey.current_category = next_category
            
            # Initialize lessons for new category
            self._initialize_lessons_for_category(journey_id, user_id, next_category)
        
        # Update user progress
        self._update_user_progress_on_category_completion(user_id, user_journey.current_category)
        
        self.db.commit()
        self.db.refresh(user_journey)
        
        return user_journey

    def _initialize_lessons_for_category(self, journey_id: int, user_id: int, category: str):
        """Initialize user lessons for a specific category"""
        
        # Get all weeks for this category
        weeks = self.db.query(Week).filter(Week.topic == category).order_by(Week.week_number).all()
        
        lesson_count = 0
        for week in weeks:
            # Get all daily lessons for this week
            daily_lessons = self.db.query(DailyLesson).filter(
                DailyLesson.week_id == week.id
            ).order_by(DailyLesson.day_number).all()
            
            for index, daily_lesson in enumerate(daily_lessons):
                # First lesson in first week should be available
                status = LessonStatus.AVAILABLE if (week.week_number == 1 and index == 0) else LessonStatus.LOCKED
                
                user_lesson = UserLesson(
                    user_id=user_id,
                    user_journey_id=journey_id,
                    daily_lesson_id=daily_lesson.id,
                    status=status,
                    days_between_lessons=1
                )
                
                # Set unlocked_at for available lessons
                if status == LessonStatus.AVAILABLE:
                    user_lesson.unlocked_at = datetime.utcnow()
                
                self.db.add(user_lesson)
                lesson_count += 1

    def _create_or_update_user_progress(self, user_id: int, journey_id: int, current_category: str):
        """Create or update user progress"""
        user_progress = self.db.query(UserProgress).filter(UserProgress.user_id == user_id).first()
        
        if not user_progress:
            user_progress = UserProgress(
                user_id=user_id,
                current_journey_id=journey_id,
                current_category=current_category,
                current_week_number=1
            )
            self.db.add(user_progress)
        else:
            user_progress.current_journey_id = journey_id
            user_progress.current_category = current_category
            user_progress.current_week_number = 1

    def _update_user_progress_on_category_completion(self, user_id: int, next_category: Optional[str]):
        """Update user progress when a category is completed"""
        user_progress = self.db.query(UserProgress).filter(UserProgress.user_id == user_id).first()
        
        if user_progress:
            user_progress.total_categories_completed += 1
            user_progress.current_category = next_category
            if next_category:
                user_progress.current_week_number = 1
