from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone

from app.models.user import User
from app.models.user_journey import UserJourney
from app.models.assessment_result import AssessmentResult
from app.models.week import Week
from app.models.daily_lesson import DailyLesson
from app.models.user_progress import UserProgress
from app.models.user_lesson import UserLesson, LessonStatus
from app.models.user_preferences import UserPreferences
from app.schemas.coach import CoachStats, ParticipantOverview, CoachDashboardResponse, CoachStatsResponse


def get_current_lesson_miss_count(db: Session, user_id: int) -> int:
    """
    Calculate how many times the current available lesson has been missed
    based on user's active days since it was unlocked
    
    Args:
        db: Database session
        user_id: User ID to check
    
    Returns:
        int: Number of times the current lesson has been missed
    """
    # Get the first AVAILABLE (unlocked but not completed) lesson
    current_lesson = db.query(UserLesson).filter(
        UserLesson.user_id == user_id,
        UserLesson.status == LessonStatus.AVAILABLE,
        UserLesson.completed_at.is_(None)
    ).order_by(UserLesson.id).first()
    
    if not current_lesson or not current_lesson.unlocked_at:
        return 0  # No available lesson to miss
    
    # Get user preferences for active days
    user_preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()
    
    # Default to all days if no preferences set
    active_days = user_preferences.active_days if user_preferences else [
        "mon", "tue", "wed", "thu", "fri", "sat", "sun"
    ]
    
    # Map weekday numbers to day names
    day_mapping = {
        0: "mon", 
        1: "tue", 
        2: "wed", 
        3: "thu", 
        4: "fri", 
        5: "sat", 
        6: "sun"
    }
    
    # Get dates
    unlock_date = current_lesson.unlocked_at.date()
    today = datetime.now(timezone.utc).date()
    
    # Count active days that have passed since unlock (excluding today)
    missed_count = 0
    current_date = unlock_date
    
    while current_date < today:
        weekday = day_mapping[current_date.weekday()]
        if weekday in active_days:
            missed_count += 1
        current_date += timedelta(days=1)
    
    return missed_count


def get_coach_stats(db: Session, coach_id: int) -> CoachStatsResponse:
    """Get comprehensive coach statistics"""
    
    # Get participants (users with role 'participant')
    participants = db.query(User).filter(
        User.role == "participant"
    ).count()
    
    # Get journey statistics
    total_journeys = db.query(UserJourney).count()
    journey_completed = db.query(UserJourney).filter(
        UserJourney.total_categories_completed >= 5
    ).count()
    
    # Calculate average completion rate based on lessons
    total_lessons_available = db.query(DailyLesson).count()
    total_lessons_completed = db.query(func.sum(UserProgress.total_lessons_completed)).scalar() or 0
    
    if total_lessons_available > 0 and participants > 0:
        # Calculate average completion rate per participant
        avg_completion_rate = ((total_lessons_completed / participants) / total_lessons_available) * 100
    else:
        avg_completion_rate = 0.0
    
    return CoachStatsResponse(
        participants=participants,
        avg_completion_rate=round(avg_completion_rate, 2),
        journey_started=total_journeys,
        journey_completed=journey_completed
    )


def get_participants_overview(db: Session) -> List[ParticipantOverview]:
    """Get participants overview with progress and last completed lesson"""
    
    # Get all participants
    participants = db.query(User).filter(
        User.role == "participant"
    ).all()
    
    participants_overview = []
    
    for user in participants:
        # Get user progress to calculate actual lesson completion percentage
        user_progress = db.query(UserProgress).filter(
            UserProgress.user_id == user.id
        ).first()
        
        # Get user journey for categories data
        user_journey = db.query(UserJourney).filter(
            UserJourney.user_id == user.id
        ).first()
        
        # Get total lessons available from daily_lessons table
        total_lessons_available = db.query(DailyLesson).count()
        
        if user_progress and total_lessons_available > 0:
            # Calculate progress percentage based on completed lessons
            progress = (user_progress.total_lessons_completed / total_lessons_available) * 100
            
            # Get last completed lesson from user progress
            if user_progress.total_lessons_completed > 0:
                last_completed_lesson = f"Completed {user_progress.total_lessons_completed} lessons"
            else:
                last_completed_lesson = "No lessons completed yet"
        else:
            progress = 0.0
            last_completed_lesson = "No progress yet"
        
        # Get last lesson completed date from user_progress.updated_at
        if user_progress and user_progress.updated_at:
            last_lesson_completed_date = user_progress.updated_at
        else:
            last_lesson_completed_date = None
        
        # Get categories data from user journey
        categories_completed = user_journey.categories_completed if user_journey and user_journey.categories_completed else []
        current_category = user_journey.current_category if user_journey else None
        
        # Get current lesson miss count
        current_lesson_missed_count = get_current_lesson_miss_count(db, user.id)
        
        participants_overview.append(ParticipantOverview(
            user_name=user.full_name or f"{user.first_name} {user.last_name}",
            email=user.email,
            progress=round(progress, 2),
            categories_completed=categories_completed,
            current_category=current_category,
            last_completed_lesson=last_completed_lesson,
            last_lesson_completed_date=last_lesson_completed_date,
            current_lesson_missed_count=current_lesson_missed_count
        ))
    
    # Sort by current_lesson_missed_count (highest to lowest)
    participants_overview.sort(key=lambda x: x.current_lesson_missed_count, reverse=True)
    
    return participants_overview


def get_coach_dashboard_data(db: Session, coach_id: int) -> CoachDashboardResponse:
    """Get complete coach dashboard data"""
    
    coach_stats = get_coach_stats(db, coach_id)
    participants_overview = get_participants_overview(db)
    
    return CoachDashboardResponse(
        coach_stats=CoachStats(
            participants=coach_stats.participants,
            avg_completion_rate=coach_stats.avg_completion_rate,
            journey_started=coach_stats.journey_started,
            journey_completed=coach_stats.journey_completed
        ),
        participants_overview=participants_overview
    )


def get_coach_participant_details(db: Session, coach_id: int, user_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific participant"""
    
    # Get user details
    user = db.query(User).filter(
        and_(User.id == user_id, User.role == "participant")
    ).first()
    
    if not user:
        return {"error": "Participant not found"}
    
    # Get user journey
    user_journey = db.query(UserJourney).filter(
        UserJourney.user_id == user_id
    ).first()
    
    # Get assessment results
    assessment_results = db.query(AssessmentResult).filter(
        AssessmentResult.user_id == user_id
    ).all()
    
    return {
        "user": {
            "id": user.id,
            "name": user.full_name or f"{user.first_name} {user.last_name}",
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at
        },
        "journey": {
            "total_categories_completed": user_journey.total_categories_completed if user_journey else 0,
            "total_lessons_completed": user_journey.total_lessons_completed if user_journey else 0,
            "current_category": user_journey.current_category if user_journey else None,
            "status": user_journey.status if user_journey else "not_started"
        } if user_journey else None,
        "assessments": [
            {
                "id": result.id,
                "total_score": result.total_score,
                "growth_focus": result.growth_focus,
                "intentional_advantage": result.intentional_advantage,
                "created_at": result.created_at
            }
            for result in assessment_results
        ]
    }
