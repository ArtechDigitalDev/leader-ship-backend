from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.coaching_session import CoachingSession
from app.services.coaching_session_service import CoachingSessionService
from app.schemas.coaching_session import (
    AnswerRequest,
    CheckInRequest,
    ReflectionRequest,
    CoachingSessionResponse,
    LessonRecommendation,
)
from app.utils.response import APIException, APIResponse

router = APIRouter(prefix="/coaching-sessions", tags=["coaching-sessions"])


def _session_state(service: CoachingSessionService, session: CoachingSession) -> dict:
    """Session data + what the client should render next."""
    return {
        "session": CoachingSessionResponse.model_validate(session),
        "screen_payload": service.get_screen_payload(session),
    }


@router.post("/start")
async def start_coaching_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Start a new coaching session, or resume the in-progress one.
    BRD: the session must survive app close — never restart mid-flow.
    """
    service = CoachingSessionService(db)
    session = service.start_or_resume_session(current_user.id)
    resumed = session.current_screen.value != "s1_entry"

    return APIResponse(
        success=True,
        message="Session resumed" if resumed else "Session started",
        data=_session_state(service, session),
    )


@router.get("/active")
async def get_active_coaching_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get the current in-progress session (for resuming mid-flow)."""
    service = CoachingSessionService(db)
    session = service.get_in_progress_session(current_user.id)

    if not session:
        raise APIException(status_code=404, message="No in-progress coaching session found")

    return APIResponse(
        success=True,
        message="Active session retrieved successfully",
        data=_session_state(service, session),
    )


@router.post("/{session_id}/answer")
async def answer_current_screen(
    session_id: int,
    request: AnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit the answer for the session's current screen and advance the flow.
    Accepts an option value, free text, or (on display screens) an empty body.
    """
    service = CoachingSessionService(db)
    session = service.submit_answer(
        user_id=current_user.id,
        session_id=session_id,
        option=request.option,
        free_text=request.free_text,
    )

    return APIResponse(
        success=True,
        message="Answer recorded",
        data=_session_state(service, session),
    )


@router.post("/{session_id}/check-in")
async def follow_up_check_in(
    session_id: int,
    request: CheckInRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    S12 — fired from the follow-up notification: "Did you have that conversation?"
    If not completed, the follow-up is rescheduled instead of ending the session.
    """
    service = CoachingSessionService(db)
    session = service.check_in(
        user_id=current_user.id,
        session_id=session_id,
        completed=request.completed,
        reschedule_timing=request.reschedule_timing,
    )

    return APIResponse(
        success=True,
        message="Check-in recorded",
        data=_session_state(service, session),
    )


@router.post("/{session_id}/reflection")
async def session_reflection(
    session_id: int,
    request: ReflectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """S13 — "How did it go?" Completes the session."""
    service = CoachingSessionService(db)
    session = service.reflect(
        user_id=current_user.id,
        session_id=session_id,
        outcome=request.outcome,
    )

    return APIResponse(
        success=True,
        message="Reflection recorded",
        data=_session_state(service, session),
    )


@router.get("/{session_id}/recommendations")
async def get_learning_recommendations(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    S14 — recommend 1-2 learning modules matched to the session's diagnosis.
    Only available after the user confirmed they acted (completion_status = yes).
    """
    service = CoachingSessionService(db)
    lessons = service.get_recommendations(current_user.id, session_id)
    session = service.get_session(current_user.id, session_id)

    recommendations = [
        LessonRecommendation(
            daily_lesson_id=lesson.id,
            title=lesson.title,
            category=lesson.week.topic,
            week_id=lesson.week_id,
            day_number=lesson.day_number,
        )
        for lesson in lessons
    ]

    # BRD pattern logic: same scenario 3+ times -> surface it.
    recurring = (
        session.scenario_type is not None
        and service.count_scenario_occurrences(current_user.id, session.scenario_type) >= 3
    )

    return APIResponse(
        success=True,
        message="Learning recommendations retrieved successfully",
        data={
            "diagnosis_type": session.diagnosis_type.value if session.diagnosis_type else None,
            "recommendations": recommendations,
            "is_recurring_pattern": recurring,
        },
    )


@router.get("/{session_id}")
async def get_coaching_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific coaching session by id."""
    service = CoachingSessionService(db)
    session = service.get_session(current_user.id, session_id)

    return APIResponse(
        success=True,
        message="Session retrieved successfully",
        data=_session_state(service, session),
    )
