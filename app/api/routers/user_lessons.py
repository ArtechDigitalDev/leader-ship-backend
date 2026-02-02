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
    LessonCommitRequest,
    LessonUnlockRequest,
    UserLessonUpdate
)
from app.utils.response import APIException, APIResponse

router = APIRouter(prefix="/user-lessons", tags=["user-lessons"])


@router.get("/available")
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
    
    return APIResponse(
        success=True,
        message="Available lessons retrieved successfully",
        data=enhanced_lessons
    )


@router.get("/category")
async def get_user_lessons_by_growth_focus_category(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all user lessons for the growth focus category from user journey"""
    from app.services.user_journey_service import UserJourneyService
    
    try:
        # Get user journey to find growth_focus_category
        journey_service = UserJourneyService(db)
        user_journey = journey_service.get_user_journey_by_user_id(current_user.id)
        
        if not user_journey:
            raise APIException(
                status_code=404,
                message="No journey found for user",
                success=False
            )
        
        # Use growth_focus_category from user journey
        target_category = user_journey.growth_focus_category
        if not target_category:
            raise APIException(
                status_code=400,
                message="No growth focus category found in user journey",
                success=False
            )
        
        # Get lessons for the growth_focus_category
        service = UserLessonService(db)
        lessons = service.get_user_lessons_by_category(current_user.id, target_category)
        
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
        
        return APIResponse(
            success=True,
            message=f"User lessons for growth focus category '{target_category}' retrieved successfully",
            data=enhanced_lessons
        )
        
    except APIException as e:
        raise e
    except Exception as e:
        raise APIException(
            status_code=500,
            message="Failed to retrieve user lessons by category",
            success=False
        )


@router.get("/{lesson_id}")
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
    
    return APIResponse(
        success=True,
        message="User lesson retrieved successfully",
        data=lesson_with_details
    )


@router.post("/{lesson_id}/start")
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
    
    # Convert to Pydantic schema
    lesson_schema = UserLesson.model_validate(lesson)
    
    return APIResponse(
        success=True,
        message="Lesson started successfully",
        data=lesson_schema
    )


@router.post("/{lesson_id}/commit")
async def commit_to_lesson(
    lesson_id: int,
    data: LessonCommitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Commit to complete this lesson within 5, 7, 10, or 14 days. Optional commit_text. Separate from complete."""
    service = UserLessonService(db)
    lesson = service.commit_to_lesson(current_user.id, lesson_id, data)

    lesson_schema = UserLesson.model_validate(lesson)
    return APIResponse(
        success=True,
        message="Commit saved successfully",
        data=lesson_schema
    )


@router.post("/{lesson_id}/complete")
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
    
    # Convert to Pydantic schema
    lesson_schema = UserLesson.model_validate(lesson)
    
    return APIResponse(
        success=True,
        message="Lesson completed successfully",
        data=lesson_schema
    )


@router.put("/{lesson_id}/unlock")
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
    
    # Convert to Pydantic schema
    lesson_schema = UserLesson.model_validate(lesson)
    
    return APIResponse(
        success=True,
        message="Lesson unlocked successfully",
        data=lesson_schema
    )


@router.put("/{lesson_id}/settings")
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
    
    # Convert to Pydantic schema
    lesson_schema = UserLesson.model_validate(lesson)
    
    return APIResponse(
        success=True,
        message="Lesson settings updated successfully",
        data=lesson_schema
    )


@router.post("/unlock-due")
async def unlock_due_lessons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Manually trigger unlocking of due lessons (for testing or admin use)"""
    service = UserLessonService(db)
    unlocked_count = service.unlock_due_lessons()
    
    return APIResponse(
        success=True,
        message=f"Unlocked {unlocked_count} lessons",
        data={"unlocked_count": unlocked_count}
    )


@router.get("/due/unlock")
async def get_lessons_due_for_unlock(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get lessons that are due to be unlocked (for admin/debugging)"""
    service = UserLessonService(db)
    lessons = service.get_lessons_due_for_unlock()
    
    # Filter to only current user's lessons
    user_lessons = [lesson for lesson in lessons if lesson.user_id == current_user.id]
    
    # Convert to Pydantic schemas
    lesson_schemas = [UserLesson.from_orm(lesson) for lesson in user_lessons]
    
    return APIResponse(
        success=True,
        message="Lessons due for unlock retrieved successfully",
        data=lesson_schemas
    )
