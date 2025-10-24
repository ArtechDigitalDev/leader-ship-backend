from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.user_progress import UserProgress
from app.models.user_journey import UserJourney
from app.models.user_lesson import UserLesson, LessonStatus
from app.models.week import Week
from app.models.daily_lesson import DailyLesson
from app.schemas.user_progress import UserProgressCreate, UserProgressUpdate
from app.utils.response import APIException
from app.services.coach_service import get_current_lesson_miss_count


class UserProgressService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_progress(self, user_id: int) -> Optional[UserProgress]:
        """Get user progress"""
        return self.db.query(UserProgress).filter(UserProgress.user_id == user_id).first()

    def create_user_progress(self, progress_data: UserProgressCreate) -> UserProgress:
        """Create new user progress"""
        user_progress = UserProgress(**progress_data.dict())
        self.db.add(user_progress)
        self.db.commit()
        self.db.refresh(user_progress)
        return user_progress

    def update_user_progress(self, user_id: int, update_data: UserProgressUpdate) -> UserProgress:
        """Update user progress"""
        user_progress = self.get_user_progress(user_id)
        
        if not user_progress:
            raise APIException(
                status_code=404,
                message="User progress not found. Start a journey first.",
                success=False
            )
        
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(user_progress, field, value)
        
        self.db.commit()
        self.db.refresh(user_progress)
        
        return user_progress

    def update_progress_on_lesson_completion(self, user_id: int, points_earned: int) -> UserProgress:
        """Update progress when a lesson is completed"""
        user_progress = self.get_user_progress(user_id)
        
        if not user_progress:
            raise APIException(
                status_code=404,
                message="User progress not found. Start a journey first.",
                success=False
            )
        
        if points_earned < 0 or points_earned > 25:
            raise APIException(
                status_code=400,
                message="Points earned must be between 0 and 25",
                success=False
            )
        
        user_progress.total_points_earned += points_earned
        user_progress.total_lessons_completed += 1
        user_progress.last_activity_date = datetime.utcnow().date()
        
        # Update streak
        self._update_streak(user_progress)
        
        self.db.commit()
        self.db.refresh(user_progress)
        
        return user_progress

    def update_progress_on_week_completion(self, user_id: int) -> UserProgress:
        """Update progress when a week is completed"""
        user_progress = self.get_user_progress(user_id)
        
        if not user_progress:
            raise APIException(
                status_code=404,
                message="User progress not found. Start a journey first.",
                success=False
            )
        
        user_progress.total_weeks_completed += 1
        
        # Update current week number
        if user_progress.current_week_number:
            user_progress.current_week_number += 1
        
        self.db.commit()
        self.db.refresh(user_progress)
        
        return user_progress

    def update_progress_on_category_completion(self, user_id: int, next_category: Optional[str]) -> UserProgress:
        """Update progress when a category is completed"""
        user_progress = self.get_user_progress(user_id)
        
        if not user_progress:
            raise APIException(
                status_code=404,
                message="User progress not found. Start a journey first.",
                success=False
            )
        
        user_progress.total_categories_completed += 1
        user_progress.current_category = next_category
        
        if next_category:
            user_progress.current_week_number = 1
        
        self.db.commit()
        self.db.refresh(user_progress)
        
        return user_progress

    def get_progress_stats(self, user_id: int) -> Dict[str, Any]:
        """Get detailed progress statistics"""
        user_progress = self.get_user_progress(user_id)
        
        if not user_progress:
            # Return default values when no progress found
            # Get total lessons from daily_lessons table
            total_lessons = self.db.query(DailyLesson).count()
            
            return {
                "user_id": user_id,
                "total_points_earned": 0,
                "total_lessons_completed": 0,
                "total_lessons": total_lessons,
                "total_lessons_completed_percentage": 0.0,
                "total_weeks_completed": 0,
                "total_categories_completed": 0,
                "current_category": None,
                "current_week_number": 1,
                "current_streak_days": 0,
                "longest_streak_days": 0,
                "last_activity_date": None,
                "average_points_per_lesson": 0,
                "days_since_last_activity": 0,
                "get_current_lesson_miss_day_count": 0,
                "next_milestone": "Start your first lesson"
            }
        
        # Get total lessons from daily_lessons table
        total_lessons = self.db.query(DailyLesson).count()
        
        # Calculate completion percentage
        completion_percentage = 0.0
        if total_lessons > 0:
            completion_percentage = round(
                (user_progress.total_lessons_completed / total_lessons) * 100, 2
            )
        
        # Calculate additional stats
        stats = {
            "user_id": user_id,
            "total_points_earned": user_progress.total_points_earned,
            "total_lessons_completed": user_progress.total_lessons_completed,
            "total_lessons": total_lessons,
            "total_lessons_completed_percentage": completion_percentage,
            "total_weeks_completed": user_progress.total_weeks_completed,
            "total_categories_completed": user_progress.total_categories_completed,
            "current_category": user_progress.current_category,
            "current_week_number": user_progress.current_week_number,
            "current_streak_days": user_progress.current_streak_days,
            "longest_streak_days": user_progress.longest_streak_days,
            "last_activity_date": user_progress.last_activity_date,
        }
        
        # Calculate derived stats
        if user_progress.total_lessons_completed > 0:
            stats["average_points_per_lesson"] = round(
                user_progress.total_points_earned / user_progress.total_lessons_completed, 2
            )
        
        # Get current lesson miss day count
        stats["get_current_lesson_miss_day_count"] = get_current_lesson_miss_count(self.db, user_id)
        
        # Calculate completion rate
        if user_progress.current_category:
            total_lessons_in_category = self._get_total_lessons_in_category(user_progress.current_category)
            completed_lessons_in_category = self._get_completed_lessons_in_category(user_id, user_progress.current_category)
            
            if total_lessons_in_category > 0:
                stats["completion_rate"] = round(
                    (completed_lessons_in_category / total_lessons_in_category) * 100, 2
                )
        
        # Calculate days since last activity
        if user_progress.last_activity_date:
            days_since = (datetime.utcnow().date() - user_progress.last_activity_date).days
            stats["days_since_last_activity"] = days_since
        
        # Get next milestone
        stats["next_milestone"] = self._get_next_milestone(user_progress)
        
        return stats

    def reset_streak_if_broken(self, user_id: int) -> Optional[UserProgress]:
        """Reset streak if user hasn't been active for more than 1 day"""
        user_progress = self.get_user_progress(user_id)
        
        if not user_progress or not user_progress.last_activity_date:
            return user_progress
        
        days_since_activity = (datetime.utcnow().date() - user_progress.last_activity_date).days
        
        if days_since_activity > 1 and user_progress.current_streak_days > 0:
            user_progress.current_streak_days = 0
            self.db.commit()
            self.db.refresh(user_progress)
        
        return user_progress

    def _update_streak(self, user_progress: UserProgress):
        """Update streak based on last activity"""
        if not user_progress.last_activity_date:
            user_progress.current_streak_days = 1
            return
        
        days_since_activity = (datetime.utcnow().date() - user_progress.last_activity_date).days
        
        if days_since_activity == 0:
            # Same day, maintain streak
            pass
        elif days_since_activity == 1:
            # Consecutive day, increment streak
            user_progress.current_streak_days += 1
        else:
            # Streak broken, reset
            user_progress.current_streak_days = 1
        
        # Update longest streak
        if user_progress.current_streak_days > user_progress.longest_streak_days:
            user_progress.longest_streak_days = user_progress.current_streak_days

    def _get_total_lessons_in_category(self, category: str) -> int:
        """Get total number of lessons in a category"""
        return self.db.query(DailyLesson).join(Week).filter(
            Week.topic.ilike(category)
        ).count()

    def _get_completed_lessons_in_category(self, user_id: int, category: str) -> int:
        """Get number of completed lessons in a category"""
        return self.db.query(UserLesson).join(DailyLesson).join(Week).filter(
            UserLesson.user_id == user_id,
            Week.topic.ilike(category),
            UserLesson.status == LessonStatus.COMPLETED
        ).count()

    def _get_next_milestone(self, user_progress: UserProgress) -> str:
        """Get next milestone for motivation"""
        if user_progress.total_lessons_completed == 0:
            return "Complete your first lesson"
        elif user_progress.total_lessons_completed < 5:
            return "Complete 5 lessons"
        elif user_progress.total_lessons_completed < 10:
            return "Complete 10 lessons"
        elif user_progress.total_weeks_completed < 1:
            return "Complete your first week"
        elif user_progress.total_categories_completed < 1:
            return "Complete your first category"
        elif user_progress.current_streak_days < 7:
            return "Build a 7-day streak"
        elif user_progress.current_streak_days < 30:
            return "Build a 30-day streak"
        else:
            return "Master all 5 categories"
