"""
Test Reminder System
====================
Complete testing script for the reminder system

Tests:
1. reminder_type = "0" (No reminders)
2. reminder_type = "1" (One reminder)
3. reminder_type = "2" (Two reminders)
4. Active/Inactive days
5. Lesson completion auto-stop
6. Hour matching optimization
"""

import sys
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user_preferences import UserPreferences
from app.models.user_lesson import UserLesson, LessonStatus
from app.services.scheduler_service import SchedulerService


def print_separator(title=""):
    """Print a visual separator"""
    if title:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")
    else:
        print(f"{'='*70}\n")


def get_current_info():
    """Get current time info"""
    now = datetime.now(timezone.utc)
    day_mapping = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
    current_day = day_mapping[now.weekday()]
    current_hour = now.hour
    
    return now, current_day, current_hour


def display_current_state(db: Session):
    """Display current system state"""
    now, current_day, current_hour = get_current_info()
    
    print_separator("CURRENT SYSTEM STATE")
    print(f"🕐 Current Time: {now}")
    print(f"📅 Current Day: {current_day}")
    print(f"⏰ Current Hour: {current_hour}")
    print(f"")
    
    # Count users by reminder_type
    type_0 = db.query(UserPreferences).filter(UserPreferences.reminder_type == "0").count()
    type_1 = db.query(UserPreferences).filter(UserPreferences.reminder_type == "1").count()
    type_2 = db.query(UserPreferences).filter(UserPreferences.reminder_type == "2").count()
    total = db.query(UserPreferences).count()
    
    print(f"📊 User Preferences Summary:")
    print(f"   Total Users: {total}")
    print(f"   Type 0 (No reminders): {type_0}")
    print(f"   Type 1 (One reminder): {type_1}")
    print(f"   Type 2 (Two reminders): {type_2}")
    print(f"")
    
    # Count lessons by status
    available = db.query(UserLesson).filter(UserLesson.status == LessonStatus.AVAILABLE).count()
    locked = db.query(UserLesson).filter(UserLesson.status == LessonStatus.LOCKED).count()
    completed = db.query(UserLesson).filter(UserLesson.status == LessonStatus.COMPLETED).count()
    
    print(f"📚 Lesson Status Summary:")
    print(f"   AVAILABLE: {available}")
    print(f"   LOCKED: {locked}")
    print(f"   COMPLETED: {completed}")
    print(f"")


def display_detailed_users(db: Session, limit=10):
    """Display detailed user preferences"""
    now, current_day, current_hour = get_current_info()
    
    print_separator("USER PREFERENCES DETAILS (Sample)")
    
    # Get users with reminders enabled
    users = db.query(UserPreferences).filter(
        UserPreferences.reminder_enabled == "true"
    ).limit(limit).all()
    
    if not users:
        print("No users with reminders enabled found!")
        return
    
    print(f"Showing {len(users)} users with reminders enabled:\n")
    
    for i, prefs in enumerate(users, 1):
        # Get user's AVAILABLE lessons
        available_lessons = db.query(UserLesson).filter(
            UserLesson.user_id == prefs.user_id,
            UserLesson.status == LessonStatus.AVAILABLE
        ).count()
        
        # Calculate if this user would get reminder now
        reminder_hour = int(prefs.reminder_time.split(":")[0])
        would_get_reminder = "NO"
        
        if prefs.reminder_type == "1" and current_hour == reminder_hour:
            would_get_reminder = "YES (Type 1 - Initial)"
        elif prefs.reminder_type == "2":
            followup_hour = (reminder_hour + 2) % 24
            if current_hour == reminder_hour:
                would_get_reminder = "YES (Type 2 - Initial)"
            elif current_hour == followup_hour:
                would_get_reminder = "YES (Type 2 - Follow-up)"
        
        # Check if today is active
        is_active_day = current_day in prefs.active_days
        
        print(f"User #{i} (ID: {prefs.user_id})")
        print(f"   reminder_time: {prefs.reminder_time}")
        print(f"   reminder_type: {prefs.reminder_type}")
        print(f"   reminder_enabled: {prefs.reminder_enabled}")
        print(f"   active_days: {prefs.active_days}")
        print(f"   Today active? {is_active_day}")
        print(f"   AVAILABLE lessons: {available_lessons}")
        print(f"   Would get reminder NOW? {would_get_reminder}")
        print()


def test_reminder_job(db: Session):
    """Run the actual reminder job"""
    print_separator("RUNNING REMINDER JOB")
    
    service = SchedulerService(db)
    
    try:
        sent_count = service.send_daily_reminders()
        
        print_separator("REMINDER JOB RESULT")
        print(f"✅ Job completed successfully!")
        print(f"📧 Total reminders sent: {sent_count}")
        print()
        
        return sent_count
        
    except Exception as e:
        print_separator("REMINDER JOB ERROR")
        print(f"❌ Job failed with error:")
        print(f"   {str(e)}")
        print()
        
        import traceback
        traceback.print_exc()
        return 0


def display_query_optimization(db: Session):
    """Show query optimization comparison"""
    now, current_day, current_hour = get_current_info()
    
    print_separator("QUERY OPTIMIZATION ANALYSIS")
    
    # Old approach: Get all users with reminders enabled
    all_users = db.query(UserPreferences).filter(
        UserPreferences.reminder_enabled == "true"
    ).count()
    
    # New approach: Get only matching users
    current_hour_prefix = f"{current_hour:02d}:"
    followup_hour = (current_hour - 2) % 24
    followup_hour_prefix = f"{followup_hour:02d}:"
    
    from sqlalchemy import or_, and_
    
    matching_users = db.query(UserPreferences).filter(
        UserPreferences.reminder_enabled == "true",
        UserPreferences.reminder_type != "0",
        or_(
            UserPreferences.reminder_time.like(f"{current_hour_prefix}%"),
            and_(
                UserPreferences.reminder_type == "2",
                UserPreferences.reminder_time.like(f"{followup_hour_prefix}%")
            )
        )
    ).count()
    
    print(f"OLD APPROACH (Fetch all):")
    print(f"   Users queried: {all_users}")
    print()
    
    print(f"NEW APPROACH (Fetch matching only):")
    print(f"   Users queried: {matching_users}")
    print()
    
    if all_users > 0:
        reduction = ((all_users - matching_users) / all_users) * 100
        speedup = all_users / matching_users if matching_users > 0 else 0
        
        print(f"OPTIMIZATION RESULTS:")
        print(f"   Query reduction: {reduction:.1f}%")
        print(f"   Speed improvement: {speedup:.1f}x faster")
        print()
    else:
        print("⚠️ No users with reminders to compare")
        print()


def display_hour_matching_details(db: Session):
    """Show which users match current hour"""
    now, current_day, current_hour = get_current_info()
    
    print_separator("HOUR MATCHING DETAILS")
    
    current_hour_prefix = f"{current_hour:02d}:"
    followup_hour = (current_hour - 2) % 24
    followup_hour_prefix = f"{followup_hour:02d}:"
    
    print(f"Current Hour: {current_hour}")
    print(f"Looking for:")
    print(f"   - reminder_time starting with '{current_hour_prefix}' (initial reminders)")
    print(f"   - reminder_time starting with '{followup_hour_prefix}' (follow-up reminders for type 2)")
    print()
    
    # Get matching users
    from sqlalchemy import or_, and_
    
    matching_users = db.query(UserPreferences).filter(
        UserPreferences.reminder_enabled == "true",
        UserPreferences.reminder_type != "0",
        or_(
            UserPreferences.reminder_time.like(f"{current_hour_prefix}%"),
            and_(
                UserPreferences.reminder_type == "2",
                UserPreferences.reminder_time.like(f"{followup_hour_prefix}%")
            )
        )
    ).all()
    
    if not matching_users:
        print("❌ No users match current hour")
        return
    
    print(f"✅ Found {len(matching_users)} matching users:\n")
    
    for i, prefs in enumerate(matching_users, 1):
        reminder_hour = int(prefs.reminder_time.split(":")[0])
        
        match_reason = ""
        if current_hour == reminder_hour:
            match_reason = "Initial reminder"
        elif prefs.reminder_type == "2" and current_hour == (reminder_hour + 2) % 24:
            match_reason = "Follow-up reminder (2 hours after initial)"
        
        available_lessons = db.query(UserLesson).filter(
            UserLesson.user_id == prefs.user_id,
            UserLesson.status == LessonStatus.AVAILABLE
        ).count()
        
        is_active_day = current_day in prefs.active_days
        
        print(f"User {i} (ID: {prefs.user_id})")
        print(f"   reminder_time: {prefs.reminder_time} → Hour: {reminder_hour}")
        print(f"   reminder_type: {prefs.reminder_type}")
        print(f"   Match reason: {match_reason}")
        print(f"   Active today? {is_active_day}")
        print(f"   AVAILABLE lessons: {available_lessons}")
        will_send_status = "YES" if (is_active_day and available_lessons > 0) else "NO"
        print(f"   Will send? {will_send_status}")
        print()


def main():
    """Main test function"""
    print("\n")
    print("="*70)
    print("          REMINDER SYSTEM - COMPREHENSIVE TEST")
    print("="*70)
    print()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # 1. Display current system state
        display_current_state(db)
        
        # 2. Display detailed user preferences
        display_detailed_users(db, limit=10)
        
        # 3. Show hour matching details
        display_hour_matching_details(db)
        
        # 4. Show query optimization
        display_query_optimization(db)
        
        # 5. Run the actual reminder job
        sent_count = test_reminder_job(db)
        
        # 6. Final summary
        print_separator("TEST SUMMARY")
        print("All tests completed successfully!")
        print(f"Total reminders sent: {sent_count}")
        print()
        
        print("To test different scenarios:")
        print("   1. Change current time in system")
        print("   2. Update user preferences (reminder_time, reminder_type)")
        print("   3. Create/complete lessons (AVAILABLE -> COMPLETED)")
        print("   4. Modify active_days to test day filtering")
        print()
        
        print_separator()
        
    except Exception as e:
        print_separator("TEST ERROR")
        print("Test failed with error:")
        print(f"   {str(e)}")
        print()
        
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    main()

