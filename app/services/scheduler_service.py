from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.user import User
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
        """
        Send reminders to users with uncompleted AVAILABLE lessons
        
        Reminder Logic (Optimized):
        - reminder_type "0": No reminders
        - reminder_type "1": One reminder at reminder_time
        - reminder_type "2": Two reminders (at reminder_time + 2 hours later)
        
        Optimization:
        - Only queries users whose reminder_time matches current hour
        - Automatically stops when lesson completed
        - No database tracking needed (stateless)
        
        Returns:
            int: Number of reminders sent
        """
        now = datetime.now(timezone.utc)
        current_hour = now.hour
        sent_count = 0
        
        try:
            # Get current day name
            day_mapping = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
            current_day = day_mapping[now.weekday()]
            
            print(f"\n{'='*70}")
            print(f"REMINDER JOB STARTED")
            print(f"{'='*70}")
            print(f"⏰ Current time: {now}")
            print(f"📅 Current day: {current_day}")
            print(f"🕐 Current hour: {current_hour}")
            print(f"{'='*70}\n")
            
            # Build target hour prefixes for database filtering
            current_hour_prefix = f"{current_hour:02d}:"  # e.g., "14:"
            followup_hour = (current_hour - 2) % 24
            followup_hour_prefix = f"{followup_hour:02d}:"  # e.g., "12:" (for type "2" follow-up)
            
            print(f"🔍 QUERY OPTIMIZATION:")
            print(f"   Looking for reminder_time starting with:")
            print(f"   - '{current_hour_prefix}xx' (initial reminders)")
            print(f"   - '{followup_hour_prefix}xx' (follow-up reminders for type 2)")
            print()
            
            # OPTIMIZED QUERY: Only get users whose reminder_time matches current hour
            # This reduces query from potentially 10,000 users to ~400 users
            candidates = self.db.query(UserPreferences).filter(
                UserPreferences.reminder_enabled == "true",
                UserPreferences.reminder_type != "0",  # Skip type "0" (no reminders)
                or_(
                    # Match users with reminder_time at current hour (for initial reminder)
                    UserPreferences.reminder_time.like(f"{current_hour_prefix}%"),
                    # Match users with reminder_time 2 hours ago (for follow-up reminder)
                    and_(
                        UserPreferences.reminder_type == "2",
                        UserPreferences.reminder_time.like(f"{followup_hour_prefix}%")
                    )
                )
            ).all()
            
            print(f"📊 QUERY RESULTS:")
            print(f"   Found {len(candidates)} candidate users")
            print()
            
            if len(candidates) == 0:
                print("ℹ️  No users match current hour - skipping reminder job")
                print(f"{'='*70}\n")
                return 0
            
            # Process only relevant users
            for i, prefs in enumerate(candidates, 1):
                print(f"--- Checking User #{i} (ID: {prefs.user_id}) ---")
                # Extract reminder hour from reminder_time
                reminder_hour = int(prefs.reminder_time.split(":")[0])
                print(f"  reminder_time: {prefs.reminder_time} (hour: {reminder_hour})")
                print(f"  reminder_type: {prefs.reminder_type}")
                print(f"  reminder_enabled: {prefs.reminder_enabled}")
                print(f"  active_days: {prefs.active_days}")
                
                # Determine if we should send reminder THIS HOUR
                should_send = False
                reminder_reason = ""
                
                if prefs.reminder_type == "1":
                    # Type 1: Send only at reminder_time
                    should_send = (current_hour == reminder_hour)
                    reminder_reason = f"Type 1: current({current_hour}) == reminder({reminder_hour})? {should_send}"
                    
                elif prefs.reminder_type == "2":
                    # Type 2: Send at reminder_time AND 2 hours later
                    second_reminder_hour = (reminder_hour + 2) % 24
                    is_initial = current_hour == reminder_hour
                    is_followup = current_hour == second_reminder_hour
                    should_send = is_initial or is_followup
                    
                    if is_initial:
                        reminder_reason = f"Type 2: Initial reminder (current {current_hour} == reminder {reminder_hour})"
                    elif is_followup:
                        reminder_reason = f"Type 2: Follow-up reminder (current {current_hour} == {reminder_hour}+2)"
                    else:
                        reminder_reason = f"Type 2: No match (current {current_hour} ≠ {reminder_hour} and ≠ {second_reminder_hour})"
                
                print(f"  {reminder_reason}")
                
                if not should_send:
                    print(f"  → SKIP: Hour doesn't match\n")
                    continue
                
                # Check if today is an active day
                print(f"  Today ({current_day}) in active_days? {current_day in prefs.active_days}")
                if current_day not in prefs.active_days:
                    print(f"  → SKIP: Today is not an active day\n")
                    continue
                
                # Check if user has AVAILABLE (uncompleted) lessons
                available_lessons = self.db.query(UserLesson).filter(
                    UserLesson.user_id == prefs.user_id,
                    UserLesson.status == LessonStatus.AVAILABLE
                ).count()
                
                print(f"  AVAILABLE lessons: {available_lessons}")
                
                if available_lessons == 0:
                    print(f"  → SKIP: No AVAILABLE lessons (all completed or locked)\n")
                    continue  # User already completed all lessons
                
                # Send reminder notification
                is_followup = (current_hour != reminder_hour)
                print(f"  ✅ SENDING REMINDER ({'Follow-up' if is_followup else 'Initial'})")
                
                self._send_notification(
                    user_id=prefs.user_id,
                    available_lessons=available_lessons,
                    reminder_type=prefs.reminder_type,
                    is_followup=is_followup
                )
                sent_count += 1
                print()
            
            print(f"{'='*70}")
            print(f"REMINDER JOB COMPLETED")
            print(f"{'='*70}")
            print(f"📧 Total reminders sent: {sent_count}")
            print(f"{'='*70}\n")
            
            return sent_count
            
        except Exception as e:
            raise e
    
    def _send_notification(self, user_id: int, available_lessons: int, reminder_type: str, is_followup: bool = False):
        """
        Send notification to user
        
        TODO: Integrate with actual notification service:
        - Email: SendGrid, AWS SES, Mailgun
        - Push: Firebase Cloud Messaging, OneSignal
        - SMS: Twilio, AWS SNS
        
        Args:
            user_id: User ID to send notification to
            available_lessons: Number of available lessons
            reminder_type: Type of reminder ("0", "1", "2")
            is_followup: Whether this is a follow-up reminder
        """
        # Build message based on reminder type and status
        if is_followup:
            message = f"Follow-up reminder: You still have {available_lessons} lesson(s) to complete today!"
        else:
            message = f"You have {available_lessons} lesson(s) to complete today!"
        
        # Log notification (replace with actual notification sending)
        print(f"     📧 Sending to user {user_id}: {message}")
        
        # Example future implementation:
        # from app.services.notification_service import send_email, send_push
        # 
        # user = self.db.query(User).filter(User.id == user_id).first()
        # 
        # if user.notification_preferences.get("email"):
        #     send_email(
        #         to=user.email,
        #         subject="Complete Your Daily Lesson",
        #         body=message
        #     )
        # 
        # if user.notification_preferences.get("push"):
        #     send_push(
        #         user_id=user_id,
        #         title="Lesson Reminder",
        #         body=message
        #     )
