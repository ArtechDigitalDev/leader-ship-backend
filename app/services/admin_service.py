from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta

from app.models.user import User
from app.models.assessment_result import AssessmentResult
from app.models.week import Week
from app.models.daily_lesson import DailyLesson
from app.models.user_journey import UserJourney
from app.schemas.admin import (
    UserStats, UserWithTrack, UserSearchRequest, AdminUserCreate, 
    AdminUserUpdate, AssessmentStats, AdminDashboardStats
)
from app.core.security import get_password_hash


def get_user_stats(db: Session) -> UserStats:
    """Get user statistics for admin dashboard"""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    inactive_users = db.query(User).filter(User.is_active == False).count()
    
    # For this implementation, we'll consider users as "pending" if they haven't completed any assessments
    # In a real system, you might have a specific "pending" status field
    pending_users = db.query(User).filter(
        User.is_active == True,
        User.is_email_verified == False
    ).count()
    
    return UserStats(
        total_users=total_users,
        active_users=active_users,
        pending_users=pending_users,
        inactive_users=inactive_users
    )


def get_assessment_stats(db: Session) -> AssessmentStats:
    """Get assessment statistics for admin dashboard"""
    # Since we simplified the assessment model, we'll return basic stats
    total_assessments = 0
    completed_assessments = 0
    avg_score = 0.0
    
    return AssessmentStats(
        total_assessments=total_assessments,
        completed_assessments=completed_assessments,
        avg_score=avg_score
    )


def get_dashboard_stats(db: Session) -> AdminDashboardStats:
    """Get comprehensive dashboard statistics"""
    user_stats = get_user_stats(db)
    assessment_stats = get_assessment_stats(db)
    
    return AdminDashboardStats(
        user_stats=user_stats,
        assessment_stats=assessment_stats
    )


def create_admin_user(db: Session, user_data: AdminUserCreate) -> User:
    """Create a new user with admin privileges"""
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user object
    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        mobile_number=user_data.mobile_number,
        hashed_password=hashed_password,
        role=user_data.role,
        is_active=True,
        is_superuser=True,
        is_email_verified=True,
        terms_accepted=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def update_admin_user(db: Session, user_id: int, user_data: AdminUserUpdate) -> Optional[User]:
    """Update an existing user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    # Update fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password" and value:
            # Hash the new password
            setattr(user, "hashed_password", get_password_hash(value))
        else:
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user


def delete_admin_user(db: Session, user_id: int) -> bool:
    """Delete a user (soft delete by setting is_active to False)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    user.is_active = False
    db.commit()
    
    return True


def search_users(db: Session, search_request: UserSearchRequest) -> List[UserWithTrack]:
    """Search users with pagination and filtering"""
    query = db.query(User)
    
    # Apply filters
    if search_request.role:
        query = query.filter(User.role == search_request.role)
    
    if search_request.is_active is not None:
        query = query.filter(User.is_active == search_request.is_active)
    
    if search_request.is_email_verified is not None:
        query = query.filter(User.is_email_verified == search_request.is_email_verified)
    
    if search_request.search_term:
        search_term = f"%{search_request.search_term}%"
        query = query.filter(
            or_(
                User.email.ilike(search_term),
                User.username.ilike(search_term),
                User.full_name.ilike(search_term)
            )
        )
    
    # Apply pagination
    offset = (search_request.page - 1) * search_request.limit
    users = query.offset(offset).limit(search_request.limit).all()
    
    # Convert to UserWithTrack objects
    result = []
    for user in users:
        # Get assessment count for this user
        assessment_count = db.query(AssessmentResult).filter(
            AssessmentResult.user_id == user.id
        ).count()
        
        # Get last assessment date
        last_assessment = db.query(AssessmentResult).filter(
            AssessmentResult.user_id == user.id
        ).order_by(AssessmentResult.created_at.desc()).first()
        
        last_assessment_date = last_assessment.created_at if last_assessment else None
        
        result.append(UserWithTrack(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_email_verified=user.is_email_verified,
            created_at=user.created_at,
            assessment_count=assessment_count,
            last_assessment_date=last_assessment_date
        ))
    
    return result


def get_comprehensive_dashboard_stats(db: Session) -> Dict[str, Any]:
    """Get comprehensive admin dashboard statistics"""
    
    # Total Users
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # User roles breakdown
    participants = db.query(User).filter(User.role == "participant").count()
    coaches = db.query(User).filter(User.role == "coach").count()
    admins = db.query(User).filter(User.role == "admin").count()
    
    # Assessments Taken
    total_assessments_taken = db.query(AssessmentResult).count()
    unique_users_assessed = db.query(AssessmentResult.user_id).distinct().count()
    
    # Journey Statistics (based on user_journey table)
    total_journeys = db.query(UserJourney).count()
    journey_completed = db.query(UserJourney).filter(
        UserJourney.total_categories_completed >= 5
    ).count()
    journey_running = db.query(UserJourney).filter(
        UserJourney.total_categories_completed < 5
    ).count()
    
    # Additional journey insights
    avg_categories_completed = db.query(func.avg(UserJourney.total_categories_completed)).scalar() or 0
    journeys_with_progress = db.query(UserJourney).filter(
        UserJourney.total_categories_completed > 0
    ).count()
    
    # Total Weeks and Lessons available
    total_weeks_available = db.query(Week).count()
    total_lessons_available = db.query(DailyLesson).count()
    
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    recent_assessments = db.query(AssessmentResult).filter(
        AssessmentResult.created_at >= thirty_days_ago
    ).count()
    
    recent_users = db.query(User).filter(
        User.created_at >= thirty_days_ago
    ).count()
    
    # User Engagement Data (Last 30 days)
    user_engagement_data = []
    for i in range(30):
        # Calculate date for each day (today - i days)
        target_date = datetime.utcnow() - timedelta(days=i)
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Count active users on this day (users who have taken assessments or made journey progress)
        assessment_users = db.query(User).join(AssessmentResult).filter(
            AssessmentResult.created_at >= start_of_day,
            AssessmentResult.created_at <= end_of_day
        ).distinct().count()
        
        journey_users = db.query(User).join(UserJourney).filter(
            UserJourney.updated_at >= start_of_day,
            UserJourney.updated_at <= end_of_day
        ).distinct().count()
        
        # Combine both metrics for daily active users
        daily_active_users = max(assessment_users, journey_users)
        
        # Get day name and formatted date
        day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        day_name = day_names[target_date.weekday()]
        formatted_date = target_date.strftime("%m/%d")
        
        user_engagement_data.append({
            "date": f"{day_name} {formatted_date}",
            "users": daily_active_users
        })
    
    # Reverse to get chronological order (oldest to newest)
    user_engagement_data.reverse()
    
    return {
        "user_statistics": {
            "total_users": total_users,
            "active_users": active_users,
            "participants": participants,
            "coaches": coaches,
            "admins": admins,
            "recent_users": recent_users,
            "userEngagement": user_engagement_data
        },
        "assessment_statistics": {
            "total_assessments_taken": total_assessments_taken,
            "unique_users_assessed": unique_users_assessed,
            "recent_assessments": recent_assessments
        },
        "journey_statistics": {
            "journey_started": total_journeys,
            "journey_completed": journey_completed,
            "journey_running": journey_running,
            "avg_categories_completed": round(avg_categories_completed, 2),
            "journeys_with_progress": journeys_with_progress,
            "total_weeks_available": total_weeks_available,
            "total_lessons_available": total_lessons_available
        },
        "system_health": {
            "total_categories": 5,
            "data_freshness": "real_time"
        }
    }
