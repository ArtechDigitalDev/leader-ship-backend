from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_coach_user, get_db
from app.models.user import User
from app.utils.response import APIResponse
from app.services.coach_service import (
    get_coach_stats,
    get_participants_overview,
    get_coach_dashboard_data,
    get_coach_participant_details,
    send_email_to_participant
)
from app.schemas.coach import (
    CoachStatsResponse,
    CoachDashboardResponse,
    SendEmailToParticipant
)

router = APIRouter()


@router.get("/dashboard", response_model=APIResponse)
async def get_coach_dashboard(
    current_user: User = Depends(get_current_coach_user),
    db: Session = Depends(get_db)
):
    """Get complete coach dashboard data"""
    try:
        dashboard_data = get_coach_dashboard_data(db, current_user.id)
        return APIResponse(
            success=True,
            message="Coach dashboard data retrieved successfully",
            data=dashboard_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve coach dashboard data: {str(e)}"
        )


@router.get("/stats", response_model=APIResponse)
async def get_coach_statistics(
    current_user: User = Depends(get_current_coach_user),
    db: Session = Depends(get_db)
):
    """Get coach statistics"""
    try:
        stats = get_coach_stats(db, current_user.id)
        return APIResponse(
            success=True,
            message="Coach statistics retrieved successfully",
            data=stats
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve coach statistics: {str(e)}"
        )


@router.get("/participants", response_model=APIResponse)
async def get_participants_overview_list(
    current_user: User = Depends(get_current_coach_user),
    db: Session = Depends(get_db)
):
    """Get participants overview list"""
    try:
        participants = get_participants_overview(db)
        return APIResponse(
            success=True,
            message="Participants overview retrieved successfully",
            data=participants
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve participants overview: {str(e)}"
        )


@router.get("/participants/{user_id}", response_model=APIResponse)
async def get_participant_details(
    user_id: int,
    current_user: User = Depends(get_current_coach_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific participant"""
    try:
        participant_details = get_coach_participant_details(db, current_user.id, user_id)
        
        if "error" in participant_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=participant_details["error"]
            )
        
        return APIResponse(
            success=True,
            message="Participant details retrieved successfully",
            data=participant_details
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve participant details: {str(e)}"
        )


@router.get("/participants/{user_id}/progress", response_model=APIResponse)
async def get_participant_progress(
    user_id: int,
    current_user: User = Depends(get_current_coach_user),
    db: Session = Depends(get_db)
):
    """Get detailed progress information for a specific participant"""
    try:
        # Get participant details first
        participant_details = get_coach_participant_details(db, current_user.id, user_id)
        
        if "error" in participant_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=participant_details["error"]
            )
        
        # Get total lessons available for accurate progress calculation
        from app.models.daily_lesson import DailyLesson
        from app.models.user_progress import UserProgress
        total_lessons_available = db.query(DailyLesson).count()
        
        # Get user progress for accurate lesson completion count
        user_progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id
        ).first()
        
        # Extract progress information
        progress_data = {
            "user_info": participant_details["user"],
            "journey_progress": participant_details["journey"],
            "assessment_history": participant_details["assessments"],
            "progress_summary": {
                "completion_percentage": round(
                    (user_progress.total_lessons_completed / total_lessons_available) * 100, 2
                ) if user_progress and total_lessons_available > 0 else 0,
                "categories_completed": participant_details["journey"]["total_categories_completed"] if participant_details["journey"] else 0,
                "lessons_completed": user_progress.total_lessons_completed if user_progress else 0,
                "total_lessons_available": total_lessons_available,
                "assessments_taken": len(participant_details["assessments"])
            }
        }
        
        return APIResponse(
            success=True,
            message="Participant progress retrieved successfully",
            data=progress_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve participant progress: {str(e)}"
        )


@router.post("/send-email", response_model=APIResponse)
async def send_email_to_single_participant(
    email_data: SendEmailToParticipant,
    current_user: User = Depends(get_current_coach_user),
    db: Session = Depends(get_db)
):
    """
    Send custom email from coach to a single participant
    
    Request Body:
    - participant_email: Email address of the participant
    - subject: Email subject line
    - message: Email body content (plain text or HTML)
    """
    try:
        result = send_email_to_participant(
            db=db,
            coach_id=current_user.id,
            participant_email=email_data.participant_email,
            subject=email_data.subject,
            message=email_data.message
        )
        
        if result.success:
            return APIResponse(
                success=True,
                message=result.message,
                data={"sent_count": result.sent_count}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


