from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.user_lesson_service import UserLessonService
from app.schemas.user_lesson import (
    UserLesson,
    UserLessonWithDetails,
    LessonCompletionRequest,
    LessonUnlockRequest,
    UserLessonUpdate
)
from app.utils.response import APIException

router = APIRouter(prefix="/user-lessons", tags=["user-lessons"])


@router.get("/available", response_model=List[UserLessonWithDetails])
async def get_available_lessons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all available lessons for the current user"""
    service = UserLessonService(db)
    lessons = service.get_available_lessons(current_user.id)
    
    # Enhance with lesson details
    enhanced_lessons = []
    for lesson in lessons:
        lesson_with_details = UserLessonWithDetails(
            **lesson.__dict__,
            daily_lesson_title=lesson.daily_lesson.title if lesson.daily_lesson else None,
            daily_lesson_day_number=lesson.daily_lesson.day_number if lesson.daily_lesson else None,
            week_topic=lesson.daily_lesson.week.topic if lesson.daily_lesson and lesson.daily_lesson.week else None,
            week_number=lesson.daily_lesson.week.week_number if lesson.daily_lesson and lesson.daily_lesson.week else None
        )
        enhanced_lessons.append(lesson_with_details)
    
    return enhanced_lessons


@router.get("/category/{category}", response_model=List[UserLessonWithDetails])
async def get_user_lessons_by_category(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all user lessons for a specific category"""
    service = UserLessonService(db)
    lessons = service.get_user_lessons_by_category(current_user.id, category.capitalize())
    
    # Enhance with lesson details
    enhanced_lessons = []
    for lesson in lessons:
        lesson_with_details = UserLessonWithDetails(
            **lesson.__dict__,
            daily_lesson_title=lesson.daily_lesson.title if lesson.daily_lesson else None,
            daily_lesson_day_number=lesson.daily_lesson.day_number if lesson.daily_lesson else None,
            week_topic=lesson.daily_lesson.week.topic if lesson.daily_lesson and lesson.daily_lesson.week else None,
            week_number=lesson.daily_lesson.week.week_number if lesson.daily_lesson and lesson.daily_lesson.week else None
        )
        enhanced_lessons.append(lesson_with_details)
    
    return enhanced_lessons


@router.get("/{lesson_id}", response_model=UserLessonWithDetails)
async def get_user_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific user lesson with details"""
    service = UserLessonService(db)
    lesson = service.get_user_lesson(current_user.id, lesson_id)
    
    if not lesson:
        raise APIException(
            status_code=404,
            message="Lesson not found",
            success=False
        )
    
    # Enhance with lesson details
    lesson_with_details = UserLessonWithDetails(
        **lesson.__dict__,
        daily_lesson_title=lesson.daily_lesson.title if lesson.daily_lesson else None,
        daily_lesson_day_number=lesson.daily_lesson.day_number if lesson.daily_lesson else None,
        week_topic=lesson.daily_lesson.week.topic if lesson.daily_lesson and lesson.daily_lesson.week else None,
        week_number=lesson.daily_lesson.week.week_number if lesson.daily_lesson and lesson.daily_lesson.week else None
    )
    
    return lesson_with_details


@router.post("/{lesson_id}/start", response_model=UserLesson)
async def start_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Start a lesson"""
    service = UserLessonService(db)
    lesson = service.start_lesson(current_user.id, lesson_id)
    
    if not lesson:
        raise APIException(
            status_code=400,
            message="Lesson not available or already started",
            success=False
        )
    
    return lesson


@router.post("/{lesson_id}/complete", response_model=UserLesson)
async def complete_lesson(
    lesson_id: int,
    completion_data: LessonCompletionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Complete a lesson and award points"""
    service = UserLessonService(db)
    lesson = service.complete_lesson(current_user.id, lesson_id, completion_data)
    
    if not lesson:
        raise APIException(
            status_code=400,
            message="Lesson not found or already completed",
            success=False
        )
    
    return lesson


@router.put("/{lesson_id}/unlock", response_model=UserLesson)
async def unlock_lesson_manually(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Manually unlock a lesson"""
    service = UserLessonService(db)
    lesson = service.unlock_lesson_manually(current_user.id, lesson_id)
    
    if not lesson:
        raise APIException(
            status_code=400,
            message="Lesson not found or already unlocked",
            success=False
        )
    
    return lesson


@router.put("/{lesson_id}/settings", response_model=UserLesson)
async def update_lesson_settings(
    lesson_id: int,
    days_between_lessons: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update lesson progression settings"""
    if days_between_lessons < 0 or days_between_lessons > 7:
        raise APIException(
            status_code=400,
            message="Days between lessons must be between 0 and 7",
            success=False
        )
    
    service = UserLessonService(db)
    lesson = service.update_lesson_settings(current_user.id, lesson_id, days_between_lessons)
    
    if not lesson:
        raise APIException(
            status_code=404,
            message="Lesson not found",
            success=False
        )
    
    return lesson


@router.post("/unlock-due", response_model=dict)
async def unlock_due_lessons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Manually trigger unlocking of due lessons (for testing or admin use)"""
    service = UserLessonService(db)
    unlocked_count = service.unlock_due_lessons()
    
    return {
        "message": f"Unlocked {unlocked_count} lessons",
        "unlocked_count": unlocked_count,
        "success": True
    }


@router.get("/due/unlock", response_model=List[UserLesson])
async def get_lessons_due_for_unlock(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get lessons that are due to be unlocked (for admin/debugging)"""
    service = UserLessonService(db)
    lessons = service.get_lessons_due_for_unlock()
    
    # Filter to only current user's lessons
    user_lessons = [lesson for lesson in lessons if lesson.user_id == current_user.id]
    
    return user_lessons
