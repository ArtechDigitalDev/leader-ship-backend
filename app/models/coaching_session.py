from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class ScenarioType(str, enum.Enum):
    """S1 — what kind of situation the manager is facing"""
    UNDERPERFORMANCE = "underperformance"
    DIFFICULT_CONVERSATION = "difficult_conversation"
    RETENTION_RISK = "retention_risk"
    CONFLICT = "conflict"
    SOMETHING_ELSE = "something_else"


class IssueDuration(str, enum.Enum):
    """S4 — how long the issue has existed"""
    JUST_STARTED = "just_started"
    WEEKS = "weeks"
    MONTHS = "months"
    LONG_TIME = "long_time"


class DiagnosisType(str, enum.Enum):
    """S6 — system-assigned root cause (BRD Section 2.3)"""
    ACCOUNTABILITY_ISSUE = "accountability_issue"
    CLARITY_ISSUE = "clarity_issue"
    CONTEXT_ISSUE = "context_issue"


class ActionTiming(str, enum.Enum):
    """S10 — when the user commits to act"""
    TODAY = "today"
    TOMORROW = "tomorrow"
    THIS_WEEK = "this_week"


class SessionOutcome(str, enum.Enum):
    """S13 — how the conversation went"""
    GOOD = "good"
    MIXED = "mixed"
    BAD = "bad"


class SessionStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"          # user is inside the S1-S10 flow
    AWAITING_ACTION = "awaiting_action"  # commitment made, follow-up scheduled (S11)
    COMPLETED = "completed"              # check-in + reflection done (S13/S14)
    ABANDONED = "abandoned"


class CoachingScreen(str, enum.Enum):
    """The 14 screens of the coaching flow (BRD Section 3)"""
    S1_ENTRY = "s1_entry"
    S2_USER_INPUT = "s2_user_input"
    S3_SPECIFICS = "s3_specifics"
    S4_DURATION = "s4_duration"
    S5_ACCOUNTABILITY = "s5_accountability"
    S6_DIAGNOSIS = "s6_diagnosis"
    S7_GUIDANCE = "s7_guidance"
    S8_CONVERSATION_BUILDER = "s8_conversation_builder"
    S9_CONVERSATION_STEPS = "s9_conversation_steps"
    S10_COMMITMENT = "s10_commitment"
    S11_FOLLOW_UP_SCHEDULED = "s11_follow_up_scheduled"
    S12_CHECK_IN = "s12_check_in"
    S13_REFLECTION = "s13_reflection"
    S14_LEARNING = "s14_learning"


class CoachingSession(Base):
    """One AI coaching session — fields per BRD Section 2.4"""
    __tablename__ = "coaching_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Conversation data (stored screen by screen)
    scenario_type = Column(Enum(ScenarioType), nullable=True)         # S1
    raw_input_text = Column(Text, nullable=True)                      # S2
    problem_detail = Column(Text, nullable=True)                      # S3
    duration = Column(Enum(IssueDuration), nullable=True)            # S4
    accountability_flag = Column(Boolean, nullable=True)              # S5 (True = has addressed it)
    is_avoidance_case = Column(Boolean, default=False, nullable=False)
    diagnosis_type = Column(Enum(DiagnosisType), nullable=True)       # S6

    # Commitment & follow-up
    action_timing = Column(Enum(ActionTiming), nullable=True)         # S10
    follow_up_scheduled_at = Column(DateTime(timezone=True), nullable=True)
    follow_up_sent_at = Column(DateTime(timezone=True), nullable=True)
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)

    # Outcome
    completion_status = Column(Boolean, nullable=True)                # S12 (did they act)
    outcome = Column(Enum(SessionOutcome), nullable=True)             # S13

    # S7 guidance generated once by the RAG pipeline and cached here, so
    # resuming the session doesn't re-run retrieval/LLM calls.
    # {"bullets": [...], "source": "rag"|"fallback", "chunk_ids": [...]}
    generated_guidance = Column(JSON, nullable=True)

    # State machine — allows resuming mid-flow after app close
    current_screen = Column(Enum(CoachingScreen), default=CoachingScreen.S1_ENTRY, nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.IN_PROGRESS, nullable=False, index=True)

    # Timestamps (BRD: minimum 12-month retention)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="coaching_sessions")

    def __repr__(self):
        return (
            f"<CoachingSession(id={self.id}, user_id={self.user_id}, "
            f"screen={self.current_screen}, status={self.status})>"
        )
