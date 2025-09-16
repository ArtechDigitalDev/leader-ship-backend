from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta

from app.models.user import User
from app.models.assessment import UserAssessment
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
        ~User.id.in_(
            db.query(UserAssessment.user_id).filter(
                UserAssessment.status == "completed"
            )
        )
    ).count()
    
    return UserStats(
        total_users=total_users,
        active_users=active_users,
        pending_users=pending_users,
        inactive_users=inactive_users
    )


def get_assessment_stats(db: Session) -> AssessmentStats:
    """Get assessment statistics for admin dashboard"""
    total_assessments = db.query(UserAssessment).count()
    completed_assessments = db.query(UserAssessment).filter(
        UserAssessment.status == "completed"
    ).count()
    
    # Calculate average score
    avg_score_result = db.query(func.avg(UserAssessment.total_score)).filter(
        UserAssessment.status == "completed"
    ).scalar()
    average_score = round(avg_score_result or 0, 2)
    
    # For now, we'll use a placeholder for most common profile
    # In a real implementation, you'd query the profile determination results
    most_common_profile = "Collaborative Leader"
    
    return AssessmentStats(
        total_assessments=total_assessments,
        completed_assessments=completed_assessments,
        average_score=average_score,
        most_common_profile=most_common_profile
    )


def get_users_with_tracks(
    db: Session, 
    search_request: UserSearchRequest
) -> Tuple[List[UserWithTrack], int]:
    """Get users with learning track information and search/filter capabilities"""
    
    # Base query
    query = db.query(User)
    
    # Apply filters
    if search_request.status:
        if search_request.status == "active":
            query = query.filter(User.is_active == True)
        elif search_request.status == "inactive":
            query = query.filter(User.is_active == False)
        elif search_request.status == "pending":
            # Users who haven't completed assessments
            query = query.filter(
                User.is_active == True,
                ~User.id.in_(
                    db.query(UserAssessment.user_id).filter(
                        UserAssessment.status == "completed"
                    )
                )
            )
    
    # Apply search
    if search_request.query:
        search_term = f"%{search_request.query}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                User.username.ilike(search_term)
            )
        )
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    offset = (search_request.page - 1) * search_request.per_page
    users = query.offset(offset).limit(search_request.per_page).all()
    
    # Convert to UserWithTrack objects
    users_with_tracks = []
    for user in users:
        # Get assessment count
        assessment_count = db.query(UserAssessment).filter(
            UserAssessment.user_id == user.id,
            UserAssessment.status == "completed"
        ).count()
        
        # Get last assessment date
        last_assessment = db.query(UserAssessment).filter(
            UserAssessment.user_id == user.id,
            UserAssessment.status == "completed"
        ).order_by(UserAssessment.completed_at.desc()).first()
        
        last_assessment_date = last_assessment.completed_at if last_assessment else None
        
        # For now, we'll use a placeholder for learning track
        # In a real implementation, you'd get this from profile determination results
        learning_track = "Strategic Vision" if assessment_count > 0 else None
        
        user_with_track = UserWithTrack(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            mobile_number=user.mobile_number,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            learning_track=learning_track,
            assessment_count=assessment_count,
            last_assessment_date=last_assessment_date
        )
        users_with_tracks.append(user_with_track)
    
    return users_with_tracks, total


def create_admin_user(db: Session, user_data: AdminUserCreate) -> User:
    """Create a new user by admin"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        or_(User.email == user_data.email, User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise ValueError("User with this email or username already exists")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        mobile_number=user_data.mobile_number,
        hashed_password=hashed_password,
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def update_admin_user(db: Session, user_id: int, user_data: AdminUserUpdate) -> Optional[User]:
    """Update user by admin"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return None
    
    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    return user


def delete_admin_user(db: Session, user_id: int) -> bool:
    """Delete user by admin"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return False
    
    db.delete(user)
    db.commit()
    
    return True


def get_recent_users(db: Session, limit: int = 5) -> List[UserWithTrack]:
    """Get recently registered users"""
    users = db.query(User).order_by(User.created_at.desc()).limit(limit).all()
    
    users_with_tracks = []
    for user in users:
        assessment_count = db.query(UserAssessment).filter(
            UserAssessment.user_id == user.id,
            UserAssessment.status == "completed"
        ).count()
        
        learning_track = "Strategic Vision" if assessment_count > 0 else None
        
        user_with_track = UserWithTrack(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            mobile_number=user.mobile_number,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            learning_track=learning_track,
            assessment_count=assessment_count,
            last_assessment_date=None
        )
        users_with_tracks.append(user_with_track)
    
    return users_with_tracks


def get_top_performing_users(db: Session, limit: int = 5) -> List[UserWithTrack]:
    """Get top performing users based on assessment scores"""
    # Get users with highest average assessment scores
    top_users_query = db.query(
        User,
        func.avg(UserAssessment.total_score).label('avg_score')
    ).join(
        UserAssessment, User.id == UserAssessment.user_id
    ).filter(
        UserAssessment.status == "completed"
    ).group_by(
        User.id
    ).order_by(
        func.avg(UserAssessment.total_score).desc()
    ).limit(limit).all()
    
    users_with_tracks = []
    for user, avg_score in top_users_query:
        assessment_count = db.query(UserAssessment).filter(
            UserAssessment.user_id == user.id,
            UserAssessment.status == "completed"
        ).count()
        
        learning_track = "Strategic Vision" if assessment_count > 0 else None
        
        user_with_track = UserWithTrack(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            mobile_number=user.mobile_number,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            learning_track=learning_track,
            assessment_count=assessment_count,
            last_assessment_date=None
        )
        users_with_tracks.append(user_with_track)
    
    return users_with_tracks


def get_admin_dashboard_stats(db: Session) -> AdminDashboardStats:
    """Get comprehensive dashboard statistics"""
    user_stats = get_user_stats(db)
    assessment_stats = get_assessment_stats(db)
    recent_users = get_recent_users(db)
    top_performing_users = get_top_performing_users(db)
    
    return AdminDashboardStats(
        user_stats=user_stats,
        assessment_stats=assessment_stats,
        recent_users=recent_users,
        top_performing_users=top_performing_users
    )
