from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user_lesson import UserLesson, LessonStatus
from app.models.daily_lesson import DailyLesson
from app.models.week import Week
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
            # Smart filtering: Get users whose lesson_time matches current hour
            current_hour = datetime.now(timezone.utc).hour
            
            # Get users with LOCKED lessons whose lesson_time hour matches current hour
            users_to_process = self._get_users_for_current_hour(current_hour)
            print(f"users_to_process for hour {current_hour}: {users_to_process}")
 
            for user_id in users_to_process:
                # Get the next lesson to unlock for this user (with all validations)
                next_lesson = self._get_next_lesson_to_unlock(user_id)
                print(f"next_lesson for user {user_id}: {next_lesson}")
                
                # If we get a lesson, it's ready to unlock (all checks passed)
                if next_lesson:
                    now = datetime.now(timezone.utc)
                    next_lesson.status = LessonStatus.AVAILABLE
                    next_lesson.unlocked_at = now
                    unlocked_count += 1
            
            self.db.commit()
            return unlocked_count
            
        except Exception as e:
            self.db.rollback()
            raise e

    def _get_users_for_current_hour(self, current_hour: int) -> list:
        """
        Get users for current hour using OPTIMAL filtering order
        
        Optimized approach:
        1. Filter by active_day (today) - from UserPreferences
        2. Filter by lesson_time (current hour) - from UserPreferences  
        3. Check LOCKED lessons (only for filtered users)
        
        Why better?
        - Start with smallest dataset (preferences)
        - Then check larger dataset (lessons) only for relevant users
        - Minimizes database queries and operations
        """
        now = datetime.now(timezone.utc)
        print("now", now)
        
        # Get current day name
        day_mapping = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
        current_day = day_mapping[now.weekday()]
        print("current_day", current_day)
        # Step 1 & 2: Filter by active_day AND lesson_time from preferences
        # This gives us a small set of candidate users
        all_preferences = self.db.query(UserPreferences).all()
        print("all_preferences", all_preferences)
        candidate_users = []
        for prefs in all_preferences:
            # Check 1: Is today an active day?
            if current_day not in prefs.active_days:
                continue
            print("prefs.lesson_time", prefs.lesson_time)
            # Check 2: Does lesson_time hour match current hour?
            lesson_hour = int(prefs.lesson_time.split(":")[0])
            print("lesson_hour", lesson_hour , "current_hour", current_hour)
            if lesson_hour != current_hour:
                continue
            
            # Both conditions met
            candidate_users.append(prefs.user_id)
        print("candidate_users", candidate_users)
        # Early return if no candidates
        if not candidate_users:
            return []
        
        # Step 3: Check LOCKED lessons ONLY for candidate users
        # This is much more efficient than checking all users first
        users_with_locked = self.db.query(UserLesson.user_id).filter(
            UserLesson.user_id.in_(candidate_users),
            UserLesson.status == LessonStatus.LOCKED
        ).distinct().all()
        
        result = [user_id for (user_id,) in users_with_locked]
        return result

    def _get_next_lesson_to_unlock(self, user_id: int) -> Optional[UserLesson]:
        """
        Get the next lesson to unlock with validation
        
        Only checks: Previous lesson completed (sequential learning)
        Schedule controlled by: active_days + lesson_time (already filtered)
        
        Returns None if any check fails, returns lesson if ready to unlock
        """
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

        print("lessons", lessons)
        
        # Find the first LOCKED lesson and validate
        for i, lesson in enumerate(lessons):
            if lesson.status == LessonStatus.LOCKED:
                # Only check: Previous lesson completed or doesn't exist
                if i > 0:
                    previous_lesson = lessons[i - 1]
                    
                    # Previous must be completed (not just AVAILABLE)
                    if not previous_lesson.completed_at:
                        print(f"Previous lesson {previous_lesson.id} not completed yet.")
                        return None
                
                # Ready to unlock!
                # Schedule controlled by: active_days + lesson_time
                print(f"Lesson {lesson.id} ready to unlock!")
                return lesson
        
        return None

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
