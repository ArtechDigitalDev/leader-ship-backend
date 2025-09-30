from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.user_lesson import UserLesson, LessonStatus
from app.models.user_progress import UserProgress
from app.models.daily_lesson import DailyLesson
from app.models.week import Week
from app.schemas.user_lesson import UserLessonCreate, UserLessonUpdate, LessonCompletionRequest
from app.utils.response import APIException


class UserLessonService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_lesson(self, user_id: int, lesson_id: int) -> Optional[UserLesson]:
        """Get a specific user lesson"""
        lesson = self.db.query(UserLesson).filter(
            and_(UserLesson.id == lesson_id, UserLesson.user_id == user_id)
        ).first()
        
        if not lesson:
            raise APIException(
                status_code=404,
                message="Lesson not found",
                success=False
            )
        
        return lesson

    def get_user_lessons_by_category(self, user_id: int, category: str) -> List[UserLesson]:
        """Get all user lessons for a specific category"""
        return self.db.query(UserLesson).join(DailyLesson).join(Week).filter(
            and_(
                UserLesson.user_id == user_id,
                Week.topic == category
            )
        ).order_by(Week.week_number, DailyLesson.day_number).all()

    def get_available_lessons(self, user_id: int) -> List[UserLesson]:
        """Get all available lessons for a user"""
        return self.db.query(UserLesson).filter(
            and_(
                UserLesson.user_id == user_id,
                UserLesson.status == LessonStatus.AVAILABLE
            )
        ).order_by(UserLesson.created_at).all()

    def start_lesson(self, user_id: int, lesson_id: int) -> UserLesson:
        """Mark a lesson as started"""
        user_lesson = self.get_user_lesson(user_id, lesson_id)
        
        if user_lesson.status != LessonStatus.AVAILABLE:
            raise APIException(
                status_code=400,
                message="Lesson is not available to start",
                success=False
            )
        
        user_lesson.status = LessonStatus.AVAILABLE  # Still available, just marked as started
        user_lesson.started_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user_lesson)
        
        return user_lesson

    def complete_lesson(self, user_id: int, lesson_id: int, completion_data: LessonCompletionRequest) -> UserLesson:
        """Complete a lesson and award points"""
        user_lesson = self.get_user_lesson(user_id, lesson_id)
        
        if user_lesson.status == LessonStatus.COMPLETED:
            raise APIException(
                status_code=400,
                message="Lesson is already completed",
                success=False
            )
        
        if completion_data.points_earned < 0 or completion_data.points_earned > 25:
            raise APIException(
                status_code=400,
                message="Points earned must be between 0 and 25",
                success=False
            )
        
        # Update lesson
        user_lesson.status = LessonStatus.COMPLETED
        user_lesson.points_earned = completion_data.points_earned
        user_lesson.completed_at = datetime.utcnow()
        
        # Update user progress
        self._update_user_progress_on_lesson_completion(user_id, completion_data.points_earned)
        
        # Check if next lesson should be unlocked
        self._unlock_next_lesson_if_ready(user_lesson)
        
        self.db.commit()
        self.db.refresh(user_lesson)
        
        return user_lesson

    def unlock_lesson_manually(self, user_id: int, lesson_id: int) -> UserLesson:
        """Manually unlock a lesson (for admin or user preference)"""
        user_lesson = self.get_user_lesson(user_id, lesson_id)
        
        if user_lesson.status != LessonStatus.LOCKED:
            raise APIException(
                status_code=400,
                message="Lesson is not locked or already unlocked",
                success=False
            )
        
        user_lesson.status = LessonStatus.AVAILABLE
        user_lesson.unlocked_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user_lesson)
        
        return user_lesson

    def update_lesson_settings(self, user_id: int, lesson_id: int, days_between_lessons: int) -> UserLesson:
        """Update lesson progression settings"""
        user_lesson = self.get_user_lesson(user_id, lesson_id)
        
        if days_between_lessons < 0 or days_between_lessons > 7:
            raise APIException(
                status_code=400,
                message="Days between lessons must be between 0 and 7",
                success=False
            )
        
        user_lesson.days_between_lessons = days_between_lessons
        
        self.db.commit()
        self.db.refresh(user_lesson)
        
        return user_lesson

    def get_lessons_due_for_unlock(self) -> List[UserLesson]:
        """Get lessons that are due to be unlocked (for background job)"""
        today = datetime.utcnow().date()
        
        # Find completed lessons where next lesson should be unlocked
        completed_lessons = self.db.query(UserLesson).filter(
            and_(
                UserLesson.status == LessonStatus.COMPLETED,
                UserLesson.completed_at.isnot(None)
            )
        ).all()
        
        lessons_to_unlock = []
        for lesson in completed_lessons:
            # Calculate unlock date
            unlock_date = lesson.completed_at.date() + timedelta(days=lesson.days_between_lessons)
            
            if unlock_date <= today:
                # Find next lesson
                next_lesson = self._find_next_lesson(lesson)
                if next_lesson and next_lesson.status == LessonStatus.LOCKED:
                    lessons_to_unlock.append(next_lesson)
        
        return lessons_to_unlock

    def unlock_due_lessons(self) -> int:
        """Unlock lessons that are due (background job)"""
        lessons_to_unlock = self.get_lessons_due_for_unlock()
        
        for lesson in lessons_to_unlock:
            lesson.status = LessonStatus.AVAILABLE
            lesson.unlocked_at = datetime.utcnow()
        
        self.db.commit()
        
        return len(lessons_to_unlock)

    def _update_user_progress_on_lesson_completion(self, user_id: int, points_earned: int):
        """Update user progress when a lesson is completed"""
        user_progress = self.db.query(UserProgress).filter(UserProgress.user_id == user_id).first()
        
        if user_progress:
            user_progress.total_points_earned += points_earned
            user_progress.total_lessons_completed += 1
            user_progress.last_activity_date = datetime.utcnow().date()
            user_progress.current_streak_days += 1
            
            # Update longest streak
            if user_progress.current_streak_days > user_progress.longest_streak_days:
                user_progress.longest_streak_days = user_progress.current_streak_days

    def _unlock_next_lesson_if_ready(self, completed_lesson: UserLesson):
        """Check if next lesson should be unlocked based on timing"""
        if completed_lesson.days_between_lessons == 0:
            # Immediate unlock
            next_lesson = self._find_next_lesson(completed_lesson)
            if next_lesson and next_lesson.status == LessonStatus.LOCKED:
                next_lesson.status = LessonStatus.AVAILABLE
                next_lesson.unlocked_at = datetime.utcnow()

    def _find_next_lesson(self, current_lesson: UserLesson) -> Optional[UserLesson]:
        """Find the next lesson in sequence"""
        # Get the daily lesson details
        daily_lesson = self.db.query(DailyLesson).filter(
            DailyLesson.id == current_lesson.daily_lesson_id
        ).first()
        
        if not daily_lesson:
            return None
        
        # Find next lesson in same week
        next_daily_lesson = self.db.query(DailyLesson).filter(
            and_(
                DailyLesson.week_id == daily_lesson.week_id,
                DailyLesson.day_number == daily_lesson.day_number + 1
            )
        ).first()
        
        if next_daily_lesson:
            # Next lesson in same week
            return self.db.query(UserLesson).filter(
                and_(
                    UserLesson.user_id == current_lesson.user_id,
                    UserLesson.daily_lesson_id == next_daily_lesson.id
                )
            ).first()
        
        # If no next lesson in same week, find first lesson of next week
        next_week = self.db.query(Week).filter(
            Week.id > daily_lesson.week_id
        ).order_by(Week.id).first()
        
        if next_week:
            first_lesson_next_week = self.db.query(DailyLesson).filter(
                and_(
                    DailyLesson.week_id == next_week.id,
                    DailyLesson.day_number == 1
                )
            ).first()
            
            if first_lesson_next_week:
                return self.db.query(UserLesson).filter(
                    and_(
                        UserLesson.user_id == current_lesson.user_id,
                        UserLesson.daily_lesson_id == first_lesson_next_week.id
                    )
                ).first()
        
        return None
