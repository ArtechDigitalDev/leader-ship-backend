from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.services import daily_lesson_service as crud
from app.api import deps
from app.schemas.daily_lesson import DailyLessonCreate, DailyLessonResponse, DailyLessonUpdate
from app.models.user import User
from app.utils.response import APIResponse

router = APIRouter()


@router.post("/", response_model=APIResponse)
def create_daily_lesson(
    *,
    db: Session = Depends(deps.get_db),
    daily_lesson_in: DailyLessonCreate,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Create new daily lesson (Admin only).
    """
    try:
        daily_lesson = crud.create_daily_lesson(db, obj_in=daily_lesson_in)
        return APIResponse(
            success=True,
            message="Daily lesson created successfully",
            data={
                "id": daily_lesson.id,
                "week_id": daily_lesson.week_id,
                "day_number": daily_lesson.day_number,
                "title": daily_lesson.title,
                "created_at": daily_lesson.created_at
            }
        )
    except ValueError as e:
        return APIResponse(
            success=False,
            message=str(e),
            data=None
        )


@router.get("/", response_model=APIResponse)
def read_daily_lessons(
    db: Session = Depends(deps.get_db),
    week_id: int = Query(None, description="Filter by week ID"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve daily lessons. If week_id is provided, returns lessons for that week only.
    """
    if week_id:
        daily_lessons = crud.get_daily_lessons_by_week(db, week_id=week_id)
    else:
        daily_lessons = crud.get_daily_lessons(db)
    
    return APIResponse(
        success=True,
        message="Daily lessons retrieved successfully",
        data=[
            {
                "id": lesson.id,
                "week_id": lesson.week_id,
                "week": {
                    "id": lesson.week.id,
                    "topic": lesson.week.topic,
                    "week_number": lesson.week.week_number,
                    "title": lesson.week.title,
                    "intro": lesson.week.intro,
                    "weekly_challenge": lesson.week.weekly_challenge
                },
                "day_number": lesson.day_number,
                "title": lesson.title,
                "daily_tip": lesson.daily_tip,
                "swipe_cards": lesson.swipe_cards,
                "scenario": lesson.scenario,
                "go_deeper": lesson.go_deeper,
                "reflection_prompt": lesson.reflection_prompt,
                "leader_win": lesson.leader_win,
                "created_at": lesson.created_at,
                "updated_at": lesson.updated_at
            }
            for lesson in daily_lessons
        ]
    )


@router.get("/{daily_lesson_id}", response_model=APIResponse)
def read_daily_lesson(
    *,
    db: Session = Depends(deps.get_db),
    daily_lesson_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get a specific daily lesson by ID.
    """
    daily_lesson = crud.get_daily_lesson(db, daily_lesson_id=daily_lesson_id)
    if not daily_lesson:
        return APIResponse(
            success=False,
            message="Daily lesson not found",
            data=None
        )
    
    return APIResponse(
        success=True,
        message="Daily lesson retrieved successfully",
        data={
            "id": daily_lesson.id,
            "week_id": daily_lesson.week_id,
            "week": {
                "id": daily_lesson.week.id,
                "topic": daily_lesson.week.topic,
                "week_number": daily_lesson.week.week_number,
                "title": daily_lesson.week.title,
                "intro": daily_lesson.week.intro,
                "weekly_challenge": daily_lesson.week.weekly_challenge
            },
            "day_number": daily_lesson.day_number,
            "title": daily_lesson.title,
            "daily_tip": daily_lesson.daily_tip,
            "swipe_cards": daily_lesson.swipe_cards,
            "scenario": daily_lesson.scenario,
            "go_deeper": daily_lesson.go_deeper,
            "reflection_prompt": daily_lesson.reflection_prompt,
            "leader_win": daily_lesson.leader_win,
            "created_at": daily_lesson.created_at,
            "updated_at": daily_lesson.updated_at
        }
    )


@router.get("/week/{week_id}/day/{day_number}", response_model=APIResponse)
def read_daily_lesson_by_week_and_day(
    *,
    db: Session = Depends(deps.get_db),
    week_id: int,
    day_number: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get a specific daily lesson by week ID and day number.
    """
    daily_lesson = crud.get_daily_lesson_by_week_and_day(
        db, week_id=week_id, day_number=day_number
    )
    if not daily_lesson:
        return APIResponse(
            success=False,
            message=f"Daily lesson not found for week {week_id}, day {day_number}",
            data=None
        )
    
    return APIResponse(
        success=True,
        message="Daily lesson retrieved successfully",
        data={
            "id": daily_lesson.id,
            "week_id": daily_lesson.week_id,
            "week": {
                "id": daily_lesson.week.id,
                "topic": daily_lesson.week.topic,
                "week_number": daily_lesson.week.week_number,
                "title": daily_lesson.week.title,
                "intro": daily_lesson.week.intro,
                "weekly_challenge": daily_lesson.week.weekly_challenge
            },
            "day_number": daily_lesson.day_number,
            "title": daily_lesson.title,
            "daily_tip": daily_lesson.daily_tip,
            "swipe_cards": daily_lesson.swipe_cards,
            "scenario": daily_lesson.scenario,
            "go_deeper": daily_lesson.go_deeper,
            "reflection_prompt": daily_lesson.reflection_prompt,
            "leader_win": daily_lesson.leader_win,
            "created_at": daily_lesson.created_at,
            "updated_at": daily_lesson.updated_at
        }
    )


@router.put("/{daily_lesson_id}", response_model=APIResponse)
def update_daily_lesson(
    *,
    db: Session = Depends(deps.get_db),
    daily_lesson_id: int,
    daily_lesson_in: DailyLessonUpdate,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Update a daily lesson (Admin only).
    """
    daily_lesson = crud.get_daily_lesson(db, daily_lesson_id=daily_lesson_id)
    if not daily_lesson:
        return APIResponse(
            success=False,
            message="Daily lesson not found",
            data=None
        )
    
    daily_lesson = crud.update_daily_lesson(db, db_obj=daily_lesson, obj_in=daily_lesson_in)
    return APIResponse(
        success=True,
        message="Daily lesson updated successfully",
        data={
            "id": daily_lesson.id,
            "week_id": daily_lesson.week_id,
            "day_number": daily_lesson.day_number,
            "title": daily_lesson.title,
            "updated_at": daily_lesson.updated_at
        }
    )


@router.delete("/{daily_lesson_id}", response_model=APIResponse)
def delete_daily_lesson(
    *,
    db: Session = Depends(deps.get_db),
    daily_lesson_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Delete a daily lesson (Admin only).
    """
    daily_lesson = crud.get_daily_lesson(db, daily_lesson_id=daily_lesson_id)
    if not daily_lesson:
        return APIResponse(
            success=False,
            message="Daily lesson not found",
            data=None
        )
    
    crud.delete_daily_lesson(db, daily_lesson_id=daily_lesson_id)
    return APIResponse(
        success=True,
        message="Daily lesson deleted successfully",
        data=None
    )
