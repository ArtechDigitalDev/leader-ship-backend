from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user_lesson import UserLesson, LessonStatus
from app.models.daily_lesson import DailyLesson
from app.models.week import Week
from app.models.user_progress import UserProgress
from app.models.user_journey import UserJourney, JourneyStatus
from app.models.user_preferences import UserPreferences
from app.utils.response import APIException
# {
#   "frequency": "daily",
#   "activeDays": [
#     "mon",
#     "tue",
#     "wed",
#     "thu",
#     "fri",
#     "sat",
#     "sun"
#   ],
#   "lessonTime": "00:00",
#   "reminderTime": "14:00",
#   "reminderType": "1",
#   "timezone": "ET"
# }

class SchedulerService:
    """Service for handling scheduled background tasks"""
    
    def __init__(self, db: Session):
        self.db = db

    def unlock_due_lessons(self) -> int:
        """Unlock lessons based on user preferences and completion time"""
        unlocked_count = 0
        
        try:
            # Get all users who have lessons
            users_with_lessons = self.db.query(UserLesson.user_id).distinct().all()
            print("users_with_lessons", users_with_lessons)
            
            for (user_id,) in users_with_lessons:
                # Get user preferences
                user_prefs = self._get_user_preferences(user_id)
                # print("user_prefs", user_prefs)
                
                # Get the next lesson to unlock for this user
                next_lesson = self._get_next_lesson_to_unlock(user_id)
                print("next_lesson", next_lesson)
                
                if next_lesson and self._should_unlock_lesson(next_lesson, user_prefs):
                    next_lesson.status = LessonStatus.AVAILABLE
                    unlocked_count += 1
            
            self.db.commit()
            return unlocked_count
            
        except Exception as e:
            self.db.rollback()
            raise e

    def _get_user_preferences(self, user_id: int) -> dict:
        """Get user preferences with defaults"""
        prefs = self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
        
        if prefs:
            return {
                "frequency": prefs.frequency,
                "active_days": prefs.active_days,
                "lesson_time": prefs.lesson_time,
                "timezone": prefs.timezone,
                "days_between_lessons": prefs.days_between_lessons,
                "reminder_enabled": prefs.reminder_enabled
            }
        else:
            # Return default preferences
            return {
                "frequency": "daily",
                "active_days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
                "lesson_time": "00:00",
                "timezone": "ET",
                "days_between_lessons": 1,
                "reminder_enabled": "true"
            }

    def _should_unlock_lesson(self, lesson: UserLesson, user_prefs: dict) -> bool:
        """Check if lesson should be unlocked based on user preferences"""
        now = datetime.now(timezone.utc)
        
        # Check if enough time has passed since lesson creation
        days_since_creation = (now - lesson.created_at).days
        days_between_lessons = user_prefs.get("days_between_lessons", 1)
        
        if days_since_creation < days_between_lessons:
            return False
        
        # Check if today is an active day
        if not self._is_active_day(now, user_prefs["active_days"]):
            return False
        
        # Check if previous lesson was completed
        previous_lesson = self._get_previous_lesson_in_sequence(lesson)
        
        if previous_lesson and previous_lesson.completed_at:
            days_since_completion = (now - previous_lesson.completed_at).days
            return days_since_completion >= days_between_lessons
        elif not previous_lesson:
            # First lesson in sequence - unlock if enough time passed
            return True
        
        return False

    def _is_active_day(self, now: datetime, active_days: list) -> bool:
        """Check if current day is in user's active days"""
        day_mapping = {
            0: "mon", 1: "tue", 2: "wed", 3: "thu", 
            4: "fri", 5: "sat", 6: "sun"
        }
        current_day = day_mapping[now.weekday()]
        return current_day in active_days

    def _get_previous_lesson_in_sequence(self, current_lesson: UserLesson) -> Optional[UserLesson]:
        """Get the previous lesson in the sequence"""
        current_week = current_lesson.daily_lesson.week
        current_lesson_num = current_lesson.daily_lesson.day_number
        
        # Find previous lesson in same week
        if current_lesson_num > 1:
            previous_lesson = self.db.query(DailyLesson).filter(
                DailyLesson.week_id == current_week.id,
                DailyLesson.day_number == current_lesson_num - 1
            ).first()
            
            if previous_lesson:
                return self.db.query(UserLesson).filter(
                    and_(
                        UserLesson.user_id == current_lesson.user_id,
                        UserLesson.daily_lesson_id == previous_lesson.id
                    )
                ).first()
        
        # If no previous lesson in same week, find last lesson of previous week
        previous_week = self.db.query(Week).filter(
            Week.topic.ilike(current_week.topic),
            Week.week_number == current_week.week_number - 1
        ).first()
        
        if previous_week:
            last_lesson_prev_week = self.db.query(DailyLesson).filter(
                DailyLesson.week_id == previous_week.id
            ).order_by(DailyLesson.day_number.desc()).first()
            
            if last_lesson_prev_week:
                return self.db.query(UserLesson).filter(
                    and_(
                        UserLesson.user_id == current_lesson.user_id,
                        UserLesson.daily_lesson_id == last_lesson_prev_week.id
                    )
                ).first()
        
        return None

    def _get_next_lesson_to_unlock(self, user_id: int) -> Optional[UserLesson]:
        """Get the next lesson to unlock for a user (first LOCKED lesson in sequence)"""
        # Get user's journey to find current category
        user_journey = self.db.query(UserJourney).filter(
            UserJourney.user_id == user_id,
            UserJourney.status == JourneyStatus.ACTIVE
        ).first()
        
        if not user_journey or not user_journey.current_category:
            return None
        
        # Get all lessons for current category, ordered by week and day number
        lessons = self.db.query(UserLesson).join(DailyLesson).join(Week).filter(
            UserLesson.user_id == user_id,
            Week.topic.ilike(user_journey.current_category)
        ).order_by(Week.week_number, DailyLesson.day_number).all()
        
        # Find the first LOCKED lesson
        for lesson in lessons:
            if lesson.status == LessonStatus.LOCKED:
                return lesson
        
        return None

    def update_user_streaks(self) -> int:
        """Update user streaks based on last activity"""
        updated_count = 0
        
        try:
            # Get all users with progress
            user_progresses = self.db.query(UserProgress).all()
            
            for progress in user_progresses:
                if progress.last_activity_date:
                    # Calculate days since last activity
                    now_date = datetime.now(timezone.utc).date()
                    days_since_activity = (now_date - progress.last_activity_date).days
                    
                    if days_since_activity > 1:
                        # Streak broken, reset to 0
                        progress.current_streak_days = 0
                        updated_count += 1
                    elif days_since_activity == 1:
                        # Continue streak
                        progress.current_streak_days += 1
                        if progress.current_streak_days > progress.longest_streak_days:
                            progress.longest_streak_days = progress.current_streak_days
                        updated_count += 1
            
            self.db.commit()
            return updated_count
            
        except Exception as e:
            self.db.rollback()
            raise e

    def check_category_completions(self) -> int:
        """Check and update category completion status"""
        updated_count = 0
        
        try:
            # Get all active journeys
            active_journeys = self.db.query(UserJourney).filter(
                UserJourney.status == JourneyStatus.ACTIVE
            ).all()
            
            for journey in active_journeys:
                if journey.current_category:
                    # Check if all lessons in current category are completed
                    total_lessons = self.db.query(UserLesson).join(DailyLesson).join(Week).filter(
                        UserLesson.user_id == journey.user_id,
                        Week.topic.ilike(journey.current_category)
                    ).count()
                    
                    completed_lessons = self.db.query(UserLesson).join(DailyLesson).join(Week).filter(
                        UserLesson.user_id == journey.user_id,
                        Week.topic.ilike(journey.current_category),
                        UserLesson.status == LessonStatus.COMPLETED
                    ).count()
                    
                    if completed_lessons == total_lessons and total_lessons > 0:
                        # Category completed
                        journey.current_category = None
                        journey.status = JourneyStatus.COMPLETED
                        updated_count += 1
            
            self.db.commit()
            return updated_count
            
        except Exception as e:
            self.db.rollback()
            raise e

    def cleanup_old_data(self) -> dict:
        """Clean up old temporary data and logs"""
        cleanup_stats = {
            "cleaned_sessions": 0,
            "cleaned_logs": 0,
            "optimized_queries": 0
        }
        
        try:
            # Clean up old sessions (older than 30 days)
            # This would depend on your session storage implementation
            
            # Clean up old logs (older than 90 days)
            # This would depend on your logging implementation
            
            # Optimize database queries
            # This could include updating statistics, rebuilding indexes, etc.
            
            self.db.commit()
            return cleanup_stats
            
        except Exception as e:
            self.db.rollback()
            raise e

    def send_daily_reminders(self) -> int:
        """Send daily reminders to users"""
        sent_count = 0
        
        try:
            # Get users who haven't completed lessons today
            # This would integrate with your notification system
            
            # For now, just return a placeholder count
            # In real implementation, this would:
            # 1. Query users who need reminders
            # 2. Send notifications (email, push, SMS)
            # 3. Log the notifications sent
            
            return sent_count
            
        except Exception as e:
            raise e

    def generate_daily_reports(self) -> dict:
        """Generate daily progress reports"""
        try:
            # Get daily statistics
            total_users = self.db.query(UserProgress).count()
            active_users = self.db.query(UserProgress).filter(
                UserProgress.last_activity_date >= datetime.utcnow().date() - timedelta(days=1)
            ).count()
            
            total_lessons_completed = self.db.query(UserLesson).filter(
                UserLesson.status == LessonStatus.COMPLETED,
                UserLesson.completed_at >= datetime.utcnow().date() - timedelta(days=1)
            ).count()
            
            return {
                "date": datetime.utcnow().date(),
                "total_users": total_users,
                "active_users": active_users,
                "total_lessons_completed": total_lessons_completed,
                "active_percentage": round((active_users / total_users) * 100, 2) if total_users > 0 else 0
            }
            
        except Exception as e:
            raise e

    def backup_user_data(self) -> dict:
        """Create backup of user data"""
        try:
            # This would implement actual backup logic
            # For now, return a placeholder
            
            backup_info = {
                "timestamp": datetime.utcnow(),
                "users_backed_up": self.db.query(UserProgress).count(),
                "backup_size_mb": 0,  # Would calculate actual size
                "backup_location": "/backups/daily_backup.sql"
            }
            
            return backup_info
            
        except Exception as e:
            raise e
