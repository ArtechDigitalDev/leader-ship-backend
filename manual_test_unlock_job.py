#!/usr/bin/env python3
"""
Manual test script for daily_lesson_unlock_job function
Run this to test the scheduler job manually multiple times
Updated to work with new immediate next lesson unlocking logic
"""

from app.core.scheduler import daily_lesson_unlock_job
from app.core.database import SessionLocal
from app.models.user_lesson import UserLesson, LessonStatus
from app.models.user_journey import UserJourney, JourneyStatus
from app.models.user import User
from app.models.daily_lesson import DailyLesson
from app.models.week import Week
from datetime import datetime

def get_next_lesson_to_unlock(db, user_id):
    """Get the next lesson to unlock for a user (first LOCKED lesson in sequence)"""
    # Get user's journey to find current category
    user_journey = db.query(UserJourney).filter(
        UserJourney.user_id == user_id,
        UserJourney.status == JourneyStatus.ACTIVE
    ).first()
    
    if not user_journey or not user_journey.current_category:
        return None
    
    # Get all lessons for current category, ordered by week and day number
    lessons = db.query(UserLesson).join(DailyLesson).join(Week).filter(
        UserLesson.user_id == user_id,
        Week.topic.ilike(user_journey.current_category)
    ).order_by(Week.week_number, DailyLesson.day_number).all()
    
    # Find the first LOCKED lesson
    for lesson in lessons:
        if lesson.status == LessonStatus.LOCKED:
            return lesson
    
    return None

def get_previous_lesson(db, current_lesson):
    """Get the previous lesson in the sequence"""
    current_week = current_lesson.daily_lesson.week
    current_lesson_num = current_lesson.daily_lesson.day_number
    
    # Find previous lesson in same week
    if current_lesson_num > 1:
        previous_lesson = db.query(DailyLesson).filter(
            DailyLesson.week_id == current_week.id,
            DailyLesson.day_number == current_lesson_num - 1
        ).first()
        
        if previous_lesson:
            return db.query(UserLesson).filter(
                UserLesson.user_id == current_lesson.user_id,
                UserLesson.daily_lesson_id == previous_lesson.id
            ).first()
    
    # If no previous lesson in same week, find last lesson of previous week
    previous_week = db.query(Week).filter(
        Week.topic.ilike(current_week.topic),
        Week.week_number == current_week.week_number - 1
    ).first()
    
    if previous_week:
        last_lesson_prev_week = db.query(DailyLesson).filter(
            DailyLesson.week_id == previous_week.id
        ).order_by(DailyLesson.day_number.desc()).first()
        
        if last_lesson_prev_week:
            return db.query(UserLesson).filter(
                UserLesson.user_id == current_lesson.user_id,
                UserLesson.daily_lesson_id == last_lesson_prev_week.id
            ).first()
    
    return None

def main():
    print("=" * 70)
    print("MANUAL TEST: daily_lesson_unlock_job (Updated Logic)")
    print("=" * 70)
    print(f"Test started at: {datetime.now()}")
    print()
    
    # Check database state before
    db = SessionLocal()
    try:
        print("BEFORE JOB EXECUTION:")
        print("-" * 40)
        
        # Overall lesson counts
        locked_count = db.query(UserLesson).filter(UserLesson.status == LessonStatus.LOCKED).count()
        available_count = db.query(UserLesson).filter(UserLesson.status == LessonStatus.AVAILABLE).count()
        completed_count = db.query(UserLesson).filter(UserLesson.status == LessonStatus.COMPLETED).count()
        
        print(f"LOCKED lessons:   {locked_count}")
        print(f"AVAILABLE lessons: {available_count}")
        print(f"COMPLETED lessons: {completed_count}")
        print()
        
        # Show user-specific details
        print("USER-SPECIFIC DETAILS:")
        print("-" * 40)
        users_with_journeys = db.query(User).join(UserJourney).filter(
            UserJourney.status == JourneyStatus.ACTIVE
        ).all()
        
        for user in users_with_journeys:
            user_locked = db.query(UserLesson).filter(
                UserLesson.user_id == user.id,
                UserLesson.status == LessonStatus.LOCKED
            ).count()
            
            user_available = db.query(UserLesson).filter(
                UserLesson.user_id == user.id,
                UserLesson.status == LessonStatus.AVAILABLE
            ).count()
            
            user_completed = db.query(UserLesson).filter(
                UserLesson.user_id == user.id,
                UserLesson.status == LessonStatus.COMPLETED
            ).count()
            
            journey = db.query(UserJourney).filter(
                UserJourney.user_id == user.id,
                UserJourney.status == JourneyStatus.ACTIVE
            ).first()
            
            current_category = journey.current_category if journey else "None"
            
            print(f"User {user.id} ({user.email}):")
            print(f"  Current Category: {current_category}")
            print(f"  LOCKED: {user_locked}, AVAILABLE: {user_available}, COMPLETED: {user_completed}")
            
            # Show immediate next lesson to unlock
            if user_locked > 0:
                next_lesson = get_next_lesson_to_unlock(db, user.id)
                if next_lesson:
                    days_since_creation = (datetime.now() - next_lesson.created_at.replace(tzinfo=None)).days
                    print(f"  Next Lesson to Unlock: ID {next_lesson.id} (Daily Lesson {next_lesson.daily_lesson_id})")
                    print(f"    Created: {next_lesson.created_at}")
                    print(f"    Days since creation: {days_since_creation}")
                    
                    # Check if previous lesson exists and is completed
                    previous_lesson = get_previous_lesson(db, next_lesson)
                    if previous_lesson:
                        if previous_lesson.completed_at:
                            days_since_completion = (datetime.now() - previous_lesson.completed_at.replace(tzinfo=None)).days
                            print(f"    Previous lesson: ID {previous_lesson.id} (completed {days_since_completion} days ago)")
                        else:
                            print(f"    Previous lesson: ID {previous_lesson.id} (NOT COMPLETED)")
                    else:
                        print(f"    Previous lesson: None (First lesson in sequence)")
                    
                    # Show unlock status
                    if days_since_creation >= 1:
                        if previous_lesson and previous_lesson.completed_at:
                            days_since_completion = (datetime.now() - previous_lesson.completed_at.replace(tzinfo=None)).days
                            if days_since_completion >= 1:
                                print(f"    Unlock Status: READY TO UNLOCK ✅")
                            else:
                                print(f"    Unlock Status: Waiting for previous lesson completion")
                        else:
                            print(f"    Unlock Status: READY TO UNLOCK ✅ (First lesson)")
                    else:
                        print(f"    Unlock Status: Waiting for 1 day to pass")
                else:
                    print(f"  Next Lesson to Unlock: None found")
            else:
                print(f"  Next Lesson to Unlock: No locked lessons")
            print()
        
    finally:
        db.close()
    
    # Execute the job
    print("EXECUTING JOB...")
    print("-" * 40)
    
    try:
        result = daily_lesson_unlock_job()
        print(f"SUCCESS: Job completed successfully!")
        print(f"RESULT: {result} lessons unlocked")
        print()
        
    except Exception as e:
        print(f"ERROR: Job failed with error:")
        print(f"   {e}")
        print()
        import traceback
        traceback.print_exc()
        return
    
    # Check database state after
    db = SessionLocal()
    try:
        print("AFTER JOB EXECUTION:")
        print("-" * 40)
        
        # Overall lesson counts
        locked_count_after = db.query(UserLesson).filter(UserLesson.status == LessonStatus.LOCKED).count()
        available_count_after = db.query(UserLesson).filter(UserLesson.status == LessonStatus.AVAILABLE).count()
        completed_count_after = db.query(UserLesson).filter(UserLesson.status == LessonStatus.COMPLETED).count()
        
        print(f"LOCKED lessons:   {locked_count_after}")
        print(f"AVAILABLE lessons: {available_count_after}")
        print(f"COMPLETED lessons: {completed_count_after}")
        print()
        
        # Show changes
        print("CHANGES DETECTED:")
        print("-" * 40)
        print(f"LOCKED:   {locked_count} -> {locked_count_after} (change: {locked_count_after - locked_count})")
        print(f"AVAILABLE: {available_count} -> {available_count_after} (change: {available_count_after - available_count})")
        print(f"COMPLETED: {completed_count} -> {completed_count_after} (change: {completed_count_after - completed_count})")
        
        # Show user-specific changes
        if (available_count_after - available_count) > 0:
            print()
            print("USER-SPECIFIC CHANGES:")
            print("-" * 40)
            for user in users_with_journeys:
                user_available_after = db.query(UserLesson).filter(
                    UserLesson.user_id == user.id,
                    UserLesson.status == LessonStatus.AVAILABLE
                ).count()
                
                user_available_before = db.query(UserLesson).filter(
                    UserLesson.user_id == user.id,
                    UserLesson.status == LessonStatus.AVAILABLE
                ).count()
                
                if user_available_after > user_available_before:
                    print(f"User {user.id}: AVAILABLE lessons increased from {user_available_before} to {user_available_after}")
        
        # Show recently updated lessons
        if (locked_count_after - locked_count) != 0 or (available_count_after - available_count) != 0:
            print()
            print("RECENTLY UPDATED LESSONS:")
            print("-" * 40)
            recent_lessons = db.query(UserLesson).order_by(UserLesson.updated_at.desc()).limit(5).all()
            for lesson in recent_lessons:
                print(f"ID: {lesson.id}, User: {lesson.user_id}, Status: {lesson.status.name}, Updated: {lesson.updated_at}")
        
    finally:
        db.close()
    
    print()
    print("=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)
    
    # Additional information
    print()
    print("NOTES:")
    print("- Lessons unlock after 1 day from creation")
    print("- Only the immediate next lesson unlocks per user")
    print("- Previous lesson must be completed for next to unlock")
    print("- Scheduler runs daily at midnight (00:00)")
    print("=" * 70)

if __name__ == "__main__":
    main()
