from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.orm.attributes import flag_modified

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

    def user_has_existing_journey(self, user_id: int) -> bool:
        """Check if user already has any journey (since they can only take assessment once)"""
        existing_journey = self.db.query(UserJourney).filter(
            UserJourney.user_id == user_id
        ).first()
        return existing_journey is not None

    def start_or_update_journey(self, journey_data: UserJourneyCreate) -> UserJourney:
        """Start new journey or update existing one to next category"""
        
        # Check if user has existing journey
        existing_journey = self.db.query(UserJourney).filter(
            UserJourney.user_id == journey_data.user_id
        ).first()
        
        if existing_journey:
            # Only update to next category if journey is completed (current_category is None, status is completed)
            if existing_journey.current_category is None and existing_journey.status == JourneyStatus.COMPLETED:
                # Update existing journey to next category
                return self._update_journey_to_next_category(existing_journey, journey_data.assessment_result_id)
            else:
                # Journey is still active, return existing journey
                raise APIException(
                    status_code=400,
                    message=f"Great progress! You're currently working on {existing_journey.current_category}. Complete all lessons in this category to unlock the next one. Keep going!",
                    success=False
                )
        else:
            # Create new journey
            return self._create_new_journey(journey_data)

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
            growth_focus_category=assessment_result.growth_focus.capitalize(),
            intentional_advantage_category=assessment_result.intentional_advantage.capitalize(),
            current_category=assessment_result.growth_focus.capitalize(),
            status=JourneyStatus.ACTIVE
        )
        
        self.db.add(user_journey)
        self.db.flush()  # Get the ID
        
        # Initialize lessons for the growth focus category
        self._initialize_lessons_for_category(
            user_journey.id, 
            journey_data.user_id, 
            assessment_result.growth_focus.capitalize()
        )
        
        # Create or update user progress
        self._create_or_update_user_progress(
            journey_data.user_id, 
            user_journey.id, 
            assessment_result.growth_focus.capitalize()
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
        """Complete current category and reset for next category"""
        user_journey = self.get_user_journey(user_id, journey_id)
        
        # Get assessment result to determine category order based on scores
        assessment_result = self.db.query(AssessmentResult).filter(
            AssessmentResult.id == user_journey.assessment_result_id
        ).first()
        
        if not assessment_result:
            raise APIException(
                status_code=404,
                message="Assessment result not found",
                success=False
            )
        
        # Get categories sorted by scores (lowest to highest)
        category_scores = {
            'Clarity': assessment_result.clarity_score,
            'Consistency': assessment_result.consistency_score,
            'Connection': assessment_result.connection_score,
            'Courage': assessment_result.courage_score,
            'Curiosity': assessment_result.curiosity_score
        }
        
        # Sort categories by score (ascending - lowest first)
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1])
        categories = [cat for cat, score in sorted_categories]
        # Track if a category was actually completed in this call
        category_was_completed = False
        
        # First, if current_category exists, complete it and add to categories_completed
        if user_journey.current_category is not None:
            current_index = categories.index(user_journey.current_category)
            
            # Add completed category to the array (capitalize first letter)
            if user_journey.categories_completed is None:
                user_journey.categories_completed = []
            user_journey.categories_completed.append(user_journey.current_category.capitalize())
            
            # Mark the array field as modified for SQLAlchemy
            flag_modified(user_journey, 'categories_completed')
            
            # Update journey progress
            user_journey.total_categories_completed += 1
            
            # Mark that a category was completed
            category_was_completed = True
            
        # Now handle the next steps based on current state
        completed_count = len(user_journey.categories_completed or [])
        
        if completed_count >= len(categories):
            # All categories completed
            user_journey.status = JourneyStatus.COMPLETED
            user_journey.completed_at = datetime.utcnow()
            user_journey.current_category = None
            # Reset journey fields
            user_journey.growth_focus_category = None
            user_journey.intentional_advantage_category = None
        else:
            # Move to next category
            next_category = categories[completed_count]
            
            # Update AssessmentResult growth_focus to next category
            assessment_result.growth_focus = next_category
            
            # Reset journey fields for fresh start
            user_journey.current_category = None
            user_journey.growth_focus_category = None
            user_journey.intentional_advantage_category = None
            
            # Set status to completed (category is done, ready for next)
            user_journey.status = JourneyStatus.COMPLETED
            
        # Update user progress only if a category was actually completed
        if category_was_completed:
            self._update_user_progress_on_category_completion(user_id, user_journey.current_category)
        
        self.db.commit()
        self.db.refresh(user_journey)
        
        return user_journey

    def _create_new_journey(self, journey_data: UserJourneyCreate) -> UserJourney:
        """Create a new user journey"""
        return self.create_user_journey(journey_data)

    def _update_journey_to_next_category(self, existing_journey: UserJourney, assessment_result_id: int) -> UserJourney:
        """Update existing journey to next category"""
        
        # Get assessment result (growth_focus already updated by complete_category_and_move_to_next)
        assessment_result = self.db.query(AssessmentResult).filter(
            AssessmentResult.id == assessment_result_id
        ).first()
        
        if not assessment_result:
            raise APIException(
                status_code=404,
                message="Assessment result not found",
                success=False
            )
        
        # Use the growth_focus from assessment_result (already set to next category)
        next_category = assessment_result.growth_focus
        
        if not next_category:
            # All categories completed
            existing_journey.status = JourneyStatus.COMPLETED
            existing_journey.completed_at = datetime.utcnow()
            existing_journey.current_category = None
            existing_journey.growth_focus_category = None
            existing_journey.intentional_advantage_category = None
        else:
            # Set current category to the next category from assessment_result
            existing_journey.current_category = next_category
            existing_journey.status = JourneyStatus.ACTIVE
            existing_journey.growth_focus_category = assessment_result.growth_focus
            existing_journey.intentional_advantage_category = assessment_result.intentional_advantage
            
            # Initialize lessons for new category
            self._initialize_lessons_for_category(existing_journey.id, existing_journey.user_id, next_category)
        
        # Update user progress
        self._create_or_update_user_progress(existing_journey.user_id, existing_journey.id, existing_journey.current_category)
        
        self.db.commit()
        self.db.refresh(existing_journey)
        
        return existing_journey

    def _initialize_lessons_for_category(self, journey_id: int, user_id: int, category: str):
        """Initialize user lessons for a specific category"""
        
        # Get all weeks for this category (case-insensitive)
        weeks = self.db.query(Week).filter(Week.topic.ilike(category)).order_by(Week.week_number).all()
        
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
