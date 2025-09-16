from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta

from app.models.user import User
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


def search_users(db: Session, search_request: UserSearchRequest) -> List[UserWithTrack]:
    """Search users with pagination and filters"""
    query = db.query(User)
    
    # Apply filters
    if search_request.email:
        query = query.filter(User.email.ilike(f"%{search_request.email}%"))
    
    if search_request.username:
        query = query.filter(User.username.ilike(f"%{search_request.username}%"))
    
    if search_request.role:
        query = query.filter(User.role == search_request.role)
    
    if search_request.is_active is not None:
        query = query.filter(User.is_active == search_request.is_active)
    
    if search_request.is_email_verified is not None:
        query = query.filter(User.is_email_verified == search_request.is_email_verified)
    
    # Apply pagination
    offset = (search_request.page - 1) * search_request.per_page
    users = query.offset(offset).limit(search_request.per_page).all()
    
    # Convert to UserWithTrack format
    result = []
    for user in users:
        # Since we removed UserAssessment, we'll set default values
        assessment_count = 0
        last_assessment_date = None
        
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


def create_user(db: Session, user_data: AdminUserCreate) -> User:
    """Create a new user (Admin only)"""
    # Check if user with same email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise ValueError("User with this email already exists")
    
    # Check if user with same username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise ValueError("User with this username already exists")
    
    # Create new user
    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        mobile_number=user_data.mobile_number,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        is_active=user_data.is_active,
        is_email_verified=user_data.is_email_verified
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, user_data: AdminUserUpdate) -> User:
    """Update user information (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    
    # Update fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password" and value:
            setattr(user, "hashed_password", get_password_hash(value))
        else:
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


def get_user_leaderboard(db: Session, limit: int = 10) -> List[UserWithTrack]:
    """Get user leaderboard based on assessment performance"""
    # Since we removed UserAssessment, we'll return users ordered by creation date
    users = db.query(User).filter(
        User.is_active == True,
        User.is_email_verified == True
    ).order_by(User.created_at.desc()).limit(limit).all()
    
    result = []
    for user in users:
        # Set default values since we removed assessment tracking
        assessment_count = 0
        last_assessment_date = None
        
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