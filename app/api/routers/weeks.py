from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services import week_service as crud
from app.api import deps
from app.schemas.week import WeekCreate, WeekResponse, WeekUpdate
from app.models.user import User
from app.utils.response import APIResponse

router = APIRouter()


@router.post("/", response_model=APIResponse)
def create_week(
    *,
    db: Session = Depends(deps.get_db),
    week_in: WeekCreate,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Create new week (Admin only).
    """
    # Check if week already exists for this topic and week number
    existing_week = crud.get_week_by_topic_and_number(
        db, topic=week_in.topic, week_number=week_in.week_number
    )
    if existing_week:
        return APIResponse(
            success=False,
            message=f"Week {week_in.week_number} already exists for topic '{week_in.topic}'",
            data=None
        )
    
    week = crud.create_week(db, obj_in=week_in)
    return APIResponse(
        success=True,
        message="Week created successfully",
        data={
            "id": week.id,
            "topic": week.topic,
            "week_number": week.week_number,
            "title": week.title,
            "intro": week.intro,
            "weekly_challenge": week.weekly_challenge,
            "created_at": week.created_at
        }
    )


@router.get("/", response_model=APIResponse)
def get_all_weeks(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Get all weeks sorted by topic and week number (Admin only).
    """
    weeks = crud.get_all_weeks(db)
    
    weeks_data = []
    for week in weeks:
        weeks_data.append({
            "id": week.id,
            "topic": week.topic,
            "week_number": week.week_number,
            "title": week.title,
            "intro": week.intro,
            "weekly_challenge": week.weekly_challenge,
            "created_at": week.created_at,
            "updated_at": week.updated_at
        })
    
    return APIResponse(
        success=True,
        message="All weeks retrieved successfully",
        data=weeks_data
    )


@router.get("/topic/{topic}", response_model=APIResponse)
def get_weeks_by_topic(
    *,
    db: Session = Depends(deps.get_db),
    topic: str,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Get all weeks for a specific topic (Admin only).
    """
    weeks = crud.get_weeks_by_topic(db, topic=topic)
    
    if not weeks:
        return APIResponse(
            success=False,
            message=f"No weeks found for topic '{topic}'",
            data=None
        )
    
    weeks_data = []
    for week in weeks:
        weeks_data.append({
            "id": week.id,
            "topic": week.topic,
            "week_number": week.week_number,
            "title": week.title,
            "intro": week.intro,
            "weekly_challenge": week.weekly_challenge,
            "created_at": week.created_at,
            "updated_at": week.updated_at
        })
    
    return APIResponse(
        success=True,
        message=f"Weeks for topic '{topic}' retrieved successfully",
        data=weeks_data
    )


@router.get("/{week_id}", response_model=APIResponse)
def get_week(
    *,
    db: Session = Depends(deps.get_db),
    week_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Get week by ID (Admin only).
    """
    week = crud.get_week(db, week_id=week_id)
    if not week:
        return APIResponse(
            success=False,
            message="Week not found",
            data=None
        )
    
    return APIResponse(
        success=True,
        message="Week retrieved successfully",
        data={
            "id": week.id,
            "topic": week.topic,
            "week_number": week.week_number,
            "title": week.title,
            "intro": week.intro,
            "weekly_challenge": week.weekly_challenge,
            "created_at": week.created_at,
            "updated_at": week.updated_at
        }
    )


@router.put("/{week_id}", response_model=APIResponse)
def update_week(
    *,
    db: Session = Depends(deps.get_db),
    week_id: int,
    week_in: WeekUpdate,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Update week (Admin only).
    """
    week = crud.get_week(db, week_id=week_id)
    if not week:
        return APIResponse(
            success=False,
            message="Week not found",
            data=None
        )
    
    # Check if updating to a topic/week_number combination that already exists
    if week_in.topic and week_in.week_number:
        existing_week = crud.get_week_by_topic_and_number(
            db, topic=week_in.topic, week_number=week_in.week_number
        )
        if existing_week and existing_week.id != week_id:
            return APIResponse(
                success=False,
                message=f"Week {week_in.week_number} already exists for topic '{week_in.topic}'",
                data=None
            )
    
    updated_week = crud.update_week(db, db_obj=week, obj_in=week_in)
    return APIResponse(
        success=True,
        message="Week updated successfully",
        data={
            "id": updated_week.id,
            "topic": updated_week.topic,
            "week_number": updated_week.week_number,
            "title": updated_week.title,
            "intro": updated_week.intro,
            "weekly_challenge": updated_week.weekly_challenge,
            "created_at": updated_week.created_at,
            "updated_at": updated_week.updated_at
        }
    )


@router.delete("/{week_id}", response_model=APIResponse)
def delete_week(
    *,
    db: Session = Depends(deps.get_db),
    week_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Delete week (Admin only).
    """
    success = crud.delete_week(db, week_id=week_id)
    if not success:
        return APIResponse(
            success=False,
            message="Week not found",
            data=None
        )
    
    return APIResponse(
        success=True,
        message="Week deleted successfully",
        data={"deleted_id": week_id}
    )
