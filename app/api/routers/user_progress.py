from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.user_progress_service import UserProgressService
from app.schemas.user_progress import (
    UserProgress,
    UserProgressWithStats,
    UserProgressUpdate,
    ProgressUpdateRequest
)
from app.utils.response import APIException, APIResponse

router = APIRouter(prefix="/user-progress", tags=["user-progress"])


@router.get("/")
async def get_user_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user progress"""
    service = UserProgressService(db)
    progress = service.get_user_progress(current_user.id)
    
    if not progress:
        raise APIException(
            status_code=404,
            message="User progress not found. Start a journey first.",
            success=False
        )
    
    return APIResponse(
        success=True,
        message="User progress retrieved successfully",
        data=progress
    )


@router.get("/stats")
async def get_user_progress_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed user progress statistics"""
    service = UserProgressService(db)
    stats = service.get_progress_stats(current_user.id)
    
    if not stats:
        raise APIException(
            status_code=404,
            message="User progress not found. Start a journey first.",
            success=False
        )
    
    return APIResponse(
        success=True,
        message="User progress stats retrieved successfully",
        data=stats
    )


@router.put("/", response_model=UserProgress)
async def update_user_progress(
    update_data: UserProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update user progress settings"""
    service = UserProgressService(db)
    progress = service.update_user_progress(current_user.id, update_data)
    
    if not progress:
        raise APIException(
            status_code=404,
            message="User progress not found",
            success=False
        )
    
    return progress


@router.post("/lesson-completed")
async def update_progress_on_lesson_completion(
    points_earned: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update progress when a lesson is completed (internal use)"""
    if points_earned < 0 or points_earned > 25:
        raise APIException(
            status_code=400,
            message="Points earned must be between 0 and 25",
            success=False
        )
    
    service = UserProgressService(db)
    progress = service.update_progress_on_lesson_completion(current_user.id, points_earned)
    
    if not progress:
        raise APIException(
            status_code=404,
            message="User progress not found",
            success=False
        )
    
    return {
        "message": "Progress updated successfully",
        "new_total_points": progress.total_points_earned,
        "new_total_lessons": progress.total_lessons_completed,
        "success": True
    }


@router.post("/week-completed")
async def update_progress_on_week_completion(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update progress when a week is completed (internal use)"""
    service = UserProgressService(db)
    progress = service.update_progress_on_week_completion(current_user.id)
    
    if not progress:
        raise APIException(
            status_code=404,
            message="User progress not found",
            success=False
        )
    
    return {
        "message": "Week completion recorded",
        "new_total_weeks": progress.total_weeks_completed,
        "current_week_number": progress.current_week_number,
        "success": True
    }


@router.post("/category-completed")
async def update_progress_on_category_completion(
    next_category: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update progress when a category is completed (internal use)"""
    service = UserProgressService(db)
    progress = service.update_progress_on_category_completion(current_user.id, next_category)
    
    if not progress:
        raise APIException(
            status_code=404,
            message="User progress not found",
            success=False
        )
    
    return {
        "message": "Category completion recorded",
        "new_total_categories": progress.total_categories_completed,
        "current_category": progress.current_category,
        "success": True
    }


@router.post("/reset-streak")
async def reset_streak_if_broken(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Reset streak if user hasn't been active for more than 1 day"""
    service = UserProgressService(db)
    progress = service.reset_streak_if_broken(current_user.id)
    
    if not progress:
        raise APIException(
            status_code=404,
            message="User progress not found",
            success=False
        )
    
    return {
        "message": "Streak status checked and updated",
        "current_streak_days": progress.current_streak_days,
        "longest_streak_days": progress.longest_streak_days,
        "success": True
    }


@router.get("/milestones", response_model=Dict[str, Any])
async def get_user_milestones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user milestones and achievements"""
    service = UserProgressService(db)
    progress = service.get_user_progress(current_user.id)
    
    if not progress:
        raise APIException(
            status_code=404,
            message="User progress not found. Start a journey first.",
            success=False
        )
    
    milestones = {
        "achievements": [],
        "next_milestones": []
    }
    
    # Check achievements
    if progress.total_lessons_completed >= 1:
        milestones["achievements"].append({
            "name": "First Lesson",
            "description": "Completed your first lesson",
            "earned": True
        })
    
    if progress.total_lessons_completed >= 5:
        milestones["achievements"].append({
            "name": "5 Lessons Complete",
            "description": "Completed 5 lessons",
            "earned": True
        })
    
    if progress.total_weeks_completed >= 1:
        milestones["achievements"].append({
            "name": "Week Warrior",
            "description": "Completed your first week",
            "earned": True
        })
    
    if progress.current_streak_days >= 7:
        milestones["achievements"].append({
            "name": "7-Day Streak",
            "description": "Maintained a 7-day learning streak",
            "earned": True
        })
    
    # Next milestones
    if progress.total_lessons_completed < 1:
        milestones["next_milestones"].append({
            "name": "First Lesson",
            "description": "Complete your first lesson",
            "target": 1,
            "current": progress.total_lessons_completed
        })
    elif progress.total_lessons_completed < 5:
        milestones["next_milestones"].append({
            "name": "5 Lessons Complete",
            "description": "Complete 5 lessons",
            "target": 5,
            "current": progress.total_lessons_completed
        })
    elif progress.current_streak_days < 7:
        milestones["next_milestones"].append({
            "name": "7-Day Streak",
            "description": "Build a 7-day learning streak",
            "target": 7,
            "current": progress.current_streak_days
        })
    
    return milestones
