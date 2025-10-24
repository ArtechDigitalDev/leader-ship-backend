from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import logging

from app.models.user import User
from app.models.user_lesson import UserLesson, LessonStatus
from app.models.daily_lesson import DailyLesson
from app.models.week import Week
from app.models.user_journey import UserJourney, JourneyStatus
from app.models.user_preferences import UserPreferences
from app.utils.response import APIException
from app.utils.email import send_lesson_reminder
from app.utils.sms import sms_service

logger = logging.getLogger(__name__)

# Timezone offset mappings
TIMEZONE_OFFSETS = {
    "ET": -5,   # Eastern Time (UTC-5)
    "CT": -6,   # Central Time (UTC-6)
    "MT": -7,   # Mountain Time (UTC-7)
    "PT": -8,   # Pacific Time (UTC-8)
    "BDT": 6,   # Bangladesh Time (UTC+6)
}

def get_current_hour_in_timezone(tz_code: str) -> int:
    """
    Get current hour in specified timezone
    
    Args:
        tz_code: Timezone code (ET, CT, MT, PT, BDT)
    
    Returns:
        int: Current hour (0-23) in specified timezone
    """
    offset_hours = TIMEZONE_OFFSETS.get(tz_code, -5)  # Default to ET
    tz = timezone(timedelta(hours=offset_hours))
    now = datetime.now(tz)
    return now.hour
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
        """
        Unlock lessons based on user preferences and their timezone
        Supports multiple timezones (ET, CT, MT, PT, BDT)
        """
        unlocked_count = 0
        
        try:
            print(f"\n{'='*70}")
            print(f"LESSON UNLOCK JOB STARTED (Multi-Timezone Optimized)")
            print(f"{'='*70}")
            
            # Get users to process (optimized by timezone hours)
            users_to_process = self._get_users_for_current_hour()
            print(f"Users to process: {len(users_to_process)}")
 
            for user_id in users_to_process:
                # Get the next lesson to unlock for this user (with all validations)
                next_lesson = self._get_next_lesson_to_unlock(user_id)
                
                # If we get a lesson, it's ready to unlock (all checks passed)
                if next_lesson:
                    # Get user's timezone for timestamp
                    prefs = self.db.query(UserPreferences).filter(
                        UserPreferences.user_id == user_id
                    ).first()
                    user_tz = prefs.timezone if prefs else "ET"
                    
                    # Set timestamp in user's timezone
                    offset_hours = TIMEZONE_OFFSETS.get(user_tz, -5)
                    user_tz_obj = timezone(timedelta(hours=offset_hours))
                    now_user_tz = datetime.now(user_tz_obj)
                    
                    next_lesson.status = LessonStatus.AVAILABLE
                    next_lesson.unlocked_at = now_user_tz
                    unlocked_count += 1
                    print(f"Unlocked lesson {next_lesson.id} for user {user_id} ({user_tz})")
            
            self.db.commit()
            print(f"\n{'='*70}")
            print(f"LESSON UNLOCK COMPLETED: {unlocked_count} lessons unlocked")
            print(f"{'='*70}\n")
            return unlocked_count
            
        except Exception as e:
            self.db.rollback()
            raise e

    def _get_users_for_current_hour(self) -> list:
        """
        Get users for current hour with multi-timezone support and optimization
        
        Optimized approach:
        1. Calculate current hour for each timezone
        2. Filter by matching lesson_time hours (database level)
        3. Check each user's timezone and active_day
        4. Check LOCKED lessons only for matched users
        
        Why better?
        - Reduces 10,000 users to ~400 users via database query
        - Then filters by timezone-specific day/hour
        - Only checks LOCKED lessons for final candidates
        """
        day_mapping = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
        
        # Calculate current hour for each timezone
        timezone_hours = {}
        for tz_code in ["ET", "CT", "MT", "PT", "BDT"]:
            tz_hour = get_current_hour_in_timezone(tz_code)
            timezone_hours[tz_code] = tz_hour
            print(f"{tz_code}: Current hour = {tz_hour:02d}:00")
        
        # Build target hours set
        target_hours = set(timezone_hours.values())
        print(f"\nTarget hours: {sorted(target_hours)}")
        
        # Build query conditions
        hour_conditions = []
        for hour in target_hours:
            hour_conditions.append(
                UserPreferences.lesson_time.like(f"{hour:02d}:%")
            )
        
        # OPTIMIZED QUERY: Get users with matching lesson_time hours
        candidates = self.db.query(UserPreferences).filter(
            or_(*hour_conditions)
        ).all()
        
        print(f"Hour-matched candidates: {len(candidates)}")
        
        if not candidates:
            return []
        
        # Filter by timezone-specific day and hour
        matched_users = []
        for prefs in candidates:
            user_tz = prefs.timezone or "ET"
            
            # Get current time in user's timezone
            offset_hours = TIMEZONE_OFFSETS.get(user_tz, -5)
            user_tz_obj = timezone(timedelta(hours=offset_hours))
            user_now = datetime.now(user_tz_obj)
            user_current_hour = user_now.hour
            user_current_day = day_mapping[user_now.weekday()]
            
            # Check 1: Is today an active day for this user?
            if user_current_day not in prefs.active_days:
                continue
            
            # Check 2: Does lesson_time hour match current hour in THEIR timezone?
            lesson_hour = int(prefs.lesson_time.split(":")[0])
            if lesson_hour != user_current_hour:
                continue
            
            # Both conditions met
            matched_users.append(prefs.user_id)
        
        print(f"Day/hour matched users: {len(matched_users)}")
        
        if not matched_users:
            return []
        
        # Check LOCKED lessons ONLY for matched users
        users_with_locked = self.db.query(UserLesson.user_id).filter(
            UserLesson.user_id.in_(matched_users),
            UserLesson.status == LessonStatus.LOCKED
        ).distinct().all()
        
        result = [user_id for (user_id,) in users_with_locked]
        print(f"Users with LOCKED lessons: {len(result)}\n")
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

    async def send_daily_reminders(self) -> int:
        """
        Send reminders to users with uncompleted AVAILABLE lessons
        Supports multiple timezones (ET, CT, MT, PT, BDT)
        
        Reminder Logic:
        - reminder_type "0": No reminders
        - reminder_type "1": One reminder at reminder_time
        - reminder_type "2": Two reminders (at reminder_time + 2 hours later)
        
        Optimization:
        - Calculate current hour for each timezone
        - Filter users by matching reminder_time hours only
        
        Returns:
            int: Number of reminders sent
        """
        now = datetime.now(timezone.utc)
        sent_count = 0
        
        try:
            print(f"\n{'='*70}")
            print(f"REMINDER JOB STARTED (Multi-Timezone Optimized)")
            print(f"{'='*70}")
            print(f"Current UTC time: {now}")
            print(f"{'='*70}\n")
            
            # Calculate current hour for each timezone
            timezone_hours = {}
            for tz_code in ["ET", "CT", "MT", "PT", "BDT"]:
                tz_hour = get_current_hour_in_timezone(tz_code)
                timezone_hours[tz_code] = tz_hour
                print(f"{tz_code}: Current hour = {tz_hour:02d}:00")
            
            # Build list of all possible reminder hours to match
            # For type "1": just the reminder hour
            # For type "2": reminder hour AND reminder+2 hour
            target_hours = set()
            for tz_hour in timezone_hours.values():
                target_hours.add(tz_hour)  # Initial reminder
                target_hours.add((tz_hour - 2) % 24)  # Follow-up (2h ago was initial)
            
            print(f"\nTarget hours to check: {sorted(target_hours)}")
            
            # Build query conditions for matching hours
            hour_conditions = []
            for hour in target_hours:
                hour_prefix = f"{hour:02d}:"
                hour_conditions.append(UserPreferences.reminder_time.like(f"{hour_prefix}%"))
            
            # OPTIMIZED QUERY: Only get users with matching reminder_time hours
            candidates = self.db.query(UserPreferences).filter(
                UserPreferences.reminder_enabled == "true",
                UserPreferences.reminder_type != "0",
                or_(*hour_conditions)  # Match any of the target hours
            ).all()
            
            print(f"Users matched by hour optimization: {len(candidates)}")
            print()
            
            if len(candidates) == 0:
                print("No users match current hours")
                print(f"{'='*70}\n")
                return 0
            
            # Get day mapping
            day_mapping = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
            
            # Process only relevant users
            for i, prefs in enumerate(candidates, 1):
                print(f"--- Checking User #{i} (ID: {prefs.user_id}) ---")
                
                # Get current hour in USER's timezone
                user_tz = prefs.timezone or "ET"
                user_current_hour = get_current_hour_in_timezone(user_tz)
                print(f"  timezone: {user_tz}")
                print(f"  current_hour in {user_tz}: {user_current_hour}")
                
                # Extract reminder hour from reminder_time
                reminder_hour = int(prefs.reminder_time.split(":")[0])
                print(f"  reminder_time: {prefs.reminder_time} (hour: {reminder_hour})")
                print(f"  reminder_type: {prefs.reminder_type}")
                print(f"  reminder_enabled: {prefs.reminder_enabled}")
                print(f"  active_days: {prefs.active_days}")
                
                # Determine if we should send reminder THIS HOUR (in USER's timezone)
                should_send = False
                reminder_reason = ""
                
                if prefs.reminder_type == "1":
                    # Type 1: Send only at reminder_time
                    should_send = (user_current_hour == reminder_hour)
                    reminder_reason = f"Type 1: current({user_current_hour}) == reminder({reminder_hour})? {should_send}"
                    
                elif prefs.reminder_type == "2":
                    # Type 2: Send at reminder_time AND 2 hours later
                    second_reminder_hour = (reminder_hour + 2) % 24
                    is_initial = user_current_hour == reminder_hour
                    is_followup = user_current_hour == second_reminder_hour
                    should_send = is_initial or is_followup
                    
                    if is_initial:
                        reminder_reason = f"Type 2: Initial reminder (current {user_current_hour} == reminder {reminder_hour})"
                    elif is_followup:
                        reminder_reason = f"Type 2: Follow-up reminder (current {user_current_hour} == {reminder_hour}+2)"
                    else:
                        reminder_reason = f"Type 2: No match (current {user_current_hour} ≠ {reminder_hour} and ≠ {second_reminder_hour})"
                
                print(f"  {reminder_reason}")
                
                if not should_send:
                    print(f"  SKIP: Hour doesn't match\n")
                    continue
                
                # Check if today is an active day (in USER's timezone)
                # Calculate current day in user's timezone
                offset_hours = TIMEZONE_OFFSETS.get(user_tz, -5)
                user_tz_obj = timezone(timedelta(hours=offset_hours))
                user_now_full = datetime.now(user_tz_obj)
                user_current_day = day_mapping[user_now_full.weekday()]
                
                print(f"  Today ({user_current_day}) in active_days? {user_current_day in prefs.active_days}")
                if user_current_day not in prefs.active_days:
                    print(f"  SKIP: Today is not an active day\n")
                    continue
                
                # Check if user has AVAILABLE (uncompleted) lessons
                available_lessons = self.db.query(UserLesson).filter(
                    UserLesson.user_id == prefs.user_id,
                    UserLesson.status == LessonStatus.AVAILABLE
                ).count()
                
                print(f"  AVAILABLE lessons: {available_lessons}")
                
                if available_lessons == 0:
                    print(f"  SKIP: No AVAILABLE lessons (all completed or locked)\n")
                    continue  # User already completed all lessons
                
                # Send reminder notification
                is_followup = (user_current_hour != reminder_hour)
                print(f"  SENDING REMINDER ({'Follow-up' if is_followup else 'Initial'})")
                
                await self._send_notification(
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
            print(f"Total reminders sent: {sent_count}")
            print(f"{'='*70}\n")
            
            return sent_count
            
        except Exception as e:
            raise e
    
    async def _send_notification(self, user_id: int, available_lessons: int, reminder_type: str, is_followup: bool = False):
        """
        Send email and SMS notification to user
        
        Args:
            user_id: User ID to send notification to
            available_lessons: Number of available lessons
            reminder_type: Type of reminder ("0", "1", "2")
            is_followup: Whether this is a follow-up reminder
        """
        try:
            # Get user details
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user:
                logger.warning(f"User {user_id} not found")
                print(f"     User {user_id} not found")
                return
            
            # Build personalized message for logging
            if is_followup:
                message = f"Hi {user.full_name}, you have {available_lessons} lesson(s) pending. Complete them to continue your leadership journey."
            else:
                message = f"Hello {user.full_name}, your daily leadership lesson is ready. You have {available_lessons} lesson(s) to complete."
            
            # # Send EMAIL notification
            # if user.email:
            #     print(f"     📧 Sending email to user {user_id} ({user.email}): {message}")
                
            #     email_success = send_lesson_reminder(
            #         user_email=user.email,
            #         user_name=user.full_name or user.username,
            #         available_lessons=available_lessons,
            #         is_followup=is_followup,
            #         reminder_type=reminder_type
            #     )
                
            #     if email_success:
            #         logger.info(f"Email sent successfully to user {user_id} ({user.email})")
            #         print(f"     ✅ Email sent successfully!")
            #     else:
            #         logger.error(f"Failed to send email to user {user_id} ({user.email})")
            #         print(f"     ❌ Failed to send email")
            # else:
            #     print(f"     ⚠️  User {user_id} has no email address")
            
            # Send SMS notification
            if user.mobile_number:
                print(f"     Sending SMS to user {user_id} ({user.mobile_number}): {message}")
                
                sms_success = await sms_service.send_sms(
                    to_number=user.mobile_number,
                    message=message
                )
                
                if sms_success:
                    logger.info(f"SMS sent successfully to user {user_id} ({user.mobile_number})")
                    print(f"     SMS sent successfully!")
                else:
                    logger.error(f"Failed to send SMS to user {user_id} ({user.mobile_number})")
                    print(f"     Failed to send SMS")
            else:
                print(f"     User {user_id} has no mobile number")
                
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {str(e)}")
            print(f"     Error: {str(e)}")


# Support email functions
from app.utils.support_email import create_support_email_content
from app.utils.email import EmailService
from app.services.coach_service import get_current_lesson_miss_count


def get_users_with_missed_lessons(db: Session, min_miss_count: int = 3):
    """
    Get users who have missed lessons more than or equal to min_miss_count
    
    Args:
        db: Database session
        min_miss_count: Minimum number of missed lessons (default: 3)
    
    Returns:
        List of user data with missed lesson count
    """
    try:
        # Get all users with their preferences
        users = db.query(User).join(UserPreferences, isouter=True).all()
        
        users_with_misses = []
        
        for user in users:
            miss_count = get_current_lesson_miss_count(db, user.id)
            
            if miss_count == min_miss_count:
                users_with_misses.append({
                    'user_id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'username': user.username,
                    'missed_count': miss_count
                })
        
        logger.info(f"Found {len(users_with_misses)} users with exactly {min_miss_count} missed lessons")
        return users_with_misses
        
    except Exception as e:
        logger.error(f"Error getting users with missed lessons: {e}")
        return []


def send_support_email_to_struggling_users(db: Session, min_miss_count: int = 3):
    """
    Send support emails to users who have missed lessons
    
    Args:
        db: Database session
        min_miss_count: Minimum number of missed lessons (default: 3)
    
    Returns:
        dict: Results of email sending
    """
    try:
        email_service = EmailService()
        users_with_misses = get_users_with_missed_lessons(db, min_miss_count=min_miss_count)
        
        sent_count = 0
        failed_count = 0
        failed_emails = []
        
        for user_data in users_with_misses:
            try:
                # Create email content
                html_content, text_content = create_support_email_content(user_data)
                
                # Send email
                success = email_service.send_email(
                    to_email=user_data['email'],
                    subject="We're here to help with your lessons",
                    html_content=html_content,
                    text_content=text_content
                )
                
                if success:
                    sent_count += 1
                    logger.info(f"Support email sent to {user_data['email']} (missed: {user_data['missed_count']})")
                else:
                    failed_count += 1
                    failed_emails.append(user_data['email'])
                    logger.error(f"Failed to send support email to {user_data['email']}")
                    
            except Exception as e:
                failed_count += 1
                failed_emails.append(user_data['email'])
                logger.error(f"Error sending support email to {user_data['email']}: {e}")
        
        result = {
            'total_users': len(users_with_misses),
            'emails_sent': sent_count,
            'emails_failed': failed_count,
            'failed_emails': failed_emails,
            'success': sent_count > 0
        }
        
        logger.info(f"Support email job completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in send_support_email_to_struggling_users: {e}")
        return {
            'total_users': 0,
            'emails_sent': 0,
            'emails_failed': 0,
            'failed_emails': [],
            'success': False,
            'error': str(e)
        }
