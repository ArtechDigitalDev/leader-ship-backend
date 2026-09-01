from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator

from app.models.coaching_session import (
    ScenarioType,
    IssueDuration,
    DiagnosisType,
    ActionTiming,
    SessionOutcome,
    SessionStatus,
    CoachingScreen,
)


class AnswerRequest(BaseModel):
    """
    Answer for the current screen.

    BRD rule: every screen must accept BOTH structured input (option)
    and free text. Screens that are display-only accept an empty body
    and simply advance.
    """
    option: Optional[str] = Field(None, description="Selected option value (e.g. 'underperformance', 'today')")
    free_text: Optional[str] = Field(None, max_length=5000, description="Free-typed input")

    @model_validator(mode="after")
    def strip_empty_strings(self):
        if self.option is not None and not self.option.strip():
            self.option = None
        if self.free_text is not None and not self.free_text.strip():
            self.free_text = None
        return self


class CheckInRequest(BaseModel):
    """S12 — fired from the follow-up notification"""
    completed: bool = Field(..., description="Did the user have the conversation?")
    reschedule_timing: Optional[ActionTiming] = Field(
        None, description="If not completed, optionally pick a new timing to reschedule the follow-up"
    )


class ReflectionRequest(BaseModel):
    """S13 — how did it go"""
    outcome: SessionOutcome


class CoachingSessionResponse(BaseModel):
    id: int
    user_id: int
    scenario_type: Optional[ScenarioType] = None
    raw_input_text: Optional[str] = None
    problem_detail: Optional[str] = None
    duration: Optional[IssueDuration] = None
    accountability_flag: Optional[bool] = None
    is_avoidance_case: bool = False
    diagnosis_type: Optional[DiagnosisType] = None
    action_timing: Optional[ActionTiming] = None
    follow_up_scheduled_at: Optional[datetime] = None
    completion_status: Optional[bool] = None
    outcome: Optional[SessionOutcome] = None
    current_screen: CoachingScreen
    status: SessionStatus
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScreenPayload(BaseModel):
    """
    What the client should render for the current screen:
    the prompt, available options, and any generated content
    (diagnosis statement, guidance bullets, script, etc.).
    """
    screen: CoachingScreen
    prompt: str
    options: List[Dict[str, str]] = Field(default_factory=list, description="[{value, label}] — empty for free-text-only screens")
    content: Optional[Dict[str, Any]] = Field(None, description="Screen-specific generated content")


class SessionStateResponse(BaseModel):
    """Session + what to render next. Returned by start/answer/resume endpoints."""
    session: CoachingSessionResponse
    screen_payload: Optional[ScreenPayload] = None


class LessonRecommendation(BaseModel):
    """S14 — a recommended learning module"""
    daily_lesson_id: int
    title: str
    category: str
    week_id: int
    day_number: int
