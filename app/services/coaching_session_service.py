"""
Coaching Session Service — orchestrates the 14-screen flow (BRD v2 Section 3).

The service is the single writer for CoachingSession state. Screen
progression and diagnosis rules live in app/services/decision_tree.py.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.coaching_session import (
    CoachingSession,
    CoachingScreen,
    SessionStatus,
    ScenarioType,
    IssueDuration,
    ActionTiming,
    SessionOutcome,
)
from app.models.daily_lesson import DailyLesson
from app.models.week import Week
from app.services import decision_tree
from app.utils.response import APIException


# Screens the user answers with data; everything else is display-only.
_DISPLAY_ONLY_SCREENS = {
    CoachingScreen.S6_DIAGNOSIS,
    CoachingScreen.S7_GUIDANCE,
    CoachingScreen.S8_CONVERSATION_BUILDER,
    CoachingScreen.S9_CONVERSATION_STEPS,
}


class CoachingSessionService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start_or_resume_session(self, user_id: int) -> CoachingSession:
        """
        BRD: S1 appears every time the app is opened, but if the user left
        mid-flow they return to where they left off — never restart.
        """
        active = self.get_in_progress_session(user_id)
        if active:
            return active

        session = CoachingSession(user_id=user_id)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_in_progress_session(self, user_id: int) -> Optional[CoachingSession]:
        return (
            self.db.query(CoachingSession)
            .filter(
                CoachingSession.user_id == user_id,
                CoachingSession.status == SessionStatus.IN_PROGRESS,
            )
            .order_by(CoachingSession.created_at.desc())
            .first()
        )

    def get_session(self, user_id: int, session_id: int) -> CoachingSession:
        session = (
            self.db.query(CoachingSession)
            .filter(
                CoachingSession.id == session_id,
                CoachingSession.user_id == user_id,
            )
            .first()
        )
        if not session:
            raise APIException(status_code=404, message="Coaching session not found")
        return session

    # ------------------------------------------------------------------
    # State machine: answering the current screen
    # ------------------------------------------------------------------

    def submit_answer(
        self,
        user_id: int,
        session_id: int,
        option: Optional[str],
        free_text: Optional[str],
    ) -> CoachingSession:
        session = self.get_session(user_id, session_id)

        if session.status != SessionStatus.IN_PROGRESS:
            raise APIException(
                status_code=400,
                message="This session is no longer in progress. "
                        "Use the check-in endpoint after your follow-up notification.",
            )

        handlers = {
            CoachingScreen.S1_ENTRY: self._answer_s1,
            CoachingScreen.S2_USER_INPUT: self._answer_s2,
            CoachingScreen.S3_SPECIFICS: self._answer_s3,
            CoachingScreen.S4_DURATION: self._answer_s4,
            CoachingScreen.S5_ACCOUNTABILITY: self._answer_s5,
            CoachingScreen.S10_COMMITMENT: self._answer_s10,
        }

        screen = session.current_screen
        if screen in _DISPLAY_ONLY_SCREENS:
            # Display screens just advance on tap (BRD: always forward movement).
            session.current_screen = decision_tree.next_screen(screen)
            self._prepare_guidance_if_needed(session)
        elif screen in handlers:
            handlers[screen](session, option, free_text)
        else:
            raise APIException(
                status_code=400,
                message=f"Screen '{screen.value}' does not accept answers.",
            )

        self.db.commit()
        self.db.refresh(session)
        return session

    def go_back(self, user_id: int, session_id: int) -> CoachingSession:
        """
        Move one screen backward (S2–S11). Does not change answers — only
        current_screen. Re-submitting an input screen clears downstream fields.
        """
        session = self.get_session(user_id, session_id)
        screen = session.current_screen

        if screen == CoachingScreen.S1_ENTRY:
            raise APIException(status_code=400, message="Cannot go back from the first screen.")

        if screen in {
            CoachingScreen.S12_CHECK_IN,
            CoachingScreen.S13_REFLECTION,
            CoachingScreen.S14_LEARNING,
        }:
            raise APIException(
                status_code=400,
                message="Back navigation is not available after the commitment step.",
            )

        if session.status == SessionStatus.AWAITING_ACTION:
            if screen != CoachingScreen.S11_FOLLOW_UP_SCHEDULED:
                raise APIException(
                    status_code=400,
                    message="Use the check-in endpoint during the follow-up period.",
                )
        elif session.status != SessionStatus.IN_PROGRESS:
            raise APIException(status_code=400, message="This session cannot navigate backward.")

        previous = decision_tree.prev_screen(screen)
        if previous is None:
            raise APIException(status_code=400, message="Cannot go back further.")

        if screen == CoachingScreen.S11_FOLLOW_UP_SCHEDULED:
            session.status = SessionStatus.IN_PROGRESS
            session.follow_up_scheduled_at = None

        session.current_screen = previous
        self.db.commit()
        self.db.refresh(session)
        return session

    # --- Per-screen handlers ------------------------------------------

    def _answer_s1(self, session: CoachingSession, option: Optional[str], free_text: Optional[str]):
        """S1: pick a scenario OR type free text. Both must work."""
        if option:
            self._invalidate_from_raw_input(session)
            session.scenario_type = self._parse_enum(ScenarioType, option, "scenario")
            session.current_screen = CoachingScreen.S2_USER_INPUT
        elif free_text:
            self._invalidate_from_problem_detail(session)
            session.raw_input_text = free_text
            session.scenario_type = decision_tree.classify_scenario(free_text)
            session.current_screen = CoachingScreen.S3_SPECIFICS
        else:
            raise APIException(status_code=400, message="Select a scenario or describe what's going on.")

    def _answer_s2(self, session: CoachingSession, option: Optional[str], free_text: Optional[str]):
        """S2: the issue in the user's own words."""
        text = free_text or option
        if not text:
            raise APIException(status_code=400, message="Please describe what's happening.")
        self._invalidate_from_problem_detail(session)
        session.raw_input_text = text
        if session.scenario_type is None:
            session.scenario_type = decision_tree.classify_scenario(text)
        session.current_screen = CoachingScreen.S3_SPECIFICS

    def _answer_s3(self, session: CoachingSession, option: Optional[str], free_text: Optional[str]):
        """S3: open text only — make them articulate it (BRD)."""
        text = free_text or option
        if not text:
            raise APIException(status_code=400, message="Please describe what specifically isn't happening.")
        self._invalidate_from_duration(session)
        session.problem_detail = text
        session.current_screen = CoachingScreen.S4_DURATION

    def _answer_s4(self, session: CoachingSession, option: Optional[str], free_text: Optional[str]):
        """S4: duration — option tap, but free text also accepted."""
        value = option or self._duration_from_text(free_text)
        if not value:
            raise APIException(status_code=400, message="Please tell me how long this has been happening.")
        self._invalidate_from_accountability(session)
        session.duration = self._parse_enum(IssueDuration, value, "duration")
        session.current_screen = CoachingScreen.S5_ACCOUNTABILITY

    def _answer_s5(self, session: CoachingSession, option: Optional[str], free_text: Optional[str]):
        """
        S5: accountability check. NO -> avoidance flag (not a detour, same path),
        with follow-up intervals halved later. Then diagnosis runs immediately.
        """
        answer = self._parse_yes_no(option or free_text)
        self._invalidate_commitment(session)
        session.generated_guidance = None
        session.accountability_flag = answer
        session.is_avoidance_case = not answer
        session.diagnosis_type = decision_tree.diagnose(session)
        session.current_screen = CoachingScreen.S6_DIAGNOSIS

    def _prepare_guidance_if_needed(self, session: CoachingSession):
        """
        Generate S7 guidance once, when the user is about to see it.
        RAG pipeline (retrieve + LLM) with the result cached on the session;
        any failure leaves it None and S7 content is omitted.
        """
        if session.current_screen != CoachingScreen.S7_GUIDANCE:
            return
        if session.generated_guidance is not None:
            return
        from app.services import rag_service
        session.generated_guidance = rag_service.build_guidance_for_session(self.db, session)

    def _answer_s10(self, session: CoachingSession, option: Optional[str], free_text: Optional[str]):
        """S10: commitment — required, cannot skip. Triggers follow-up schedule."""
        value = option or self._timing_from_text(free_text)
        if not value:
            raise APIException(status_code=400, message="Please choose when you'll have this conversation.")
        session.action_timing = self._parse_enum(ActionTiming, value, "timing")
        session.follow_up_scheduled_at = decision_tree.calculate_follow_up_time(
            session.action_timing, session.is_avoidance_case
        )
        session.status = SessionStatus.AWAITING_ACTION
        session.current_screen = CoachingScreen.S11_FOLLOW_UP_SCHEDULED

    # ------------------------------------------------------------------
    # Follow-up: check-in (S12) and reflection (S13)
    # ------------------------------------------------------------------

    def check_in(
        self,
        user_id: int,
        session_id: int,
        completed: bool,
        reschedule_timing: Optional[ActionTiming] = None,
    ) -> CoachingSession:
        session = self.get_session(user_id, session_id)

        if session.status != SessionStatus.AWAITING_ACTION:
            raise APIException(status_code=400, message="This session is not awaiting a check-in.")

        session.completion_status = completed

        if completed:
            session.current_screen = CoachingScreen.S13_REFLECTION
        else:
            # BRD S12: offer to reschedule. The session stays open.
            timing = reschedule_timing or session.action_timing
            session.action_timing = timing
            session.follow_up_scheduled_at = decision_tree.calculate_follow_up_time(
                timing, session.is_avoidance_case
            )
            session.follow_up_sent_at = None
            session.reminder_sent_at = None
            session.current_screen = CoachingScreen.S12_CHECK_IN

        self.db.commit()
        self.db.refresh(session)
        return session

    def reflect(self, user_id: int, session_id: int, outcome: SessionOutcome) -> CoachingSession:
        session = self.get_session(user_id, session_id)

        if session.current_screen != CoachingScreen.S13_REFLECTION:
            raise APIException(status_code=400, message="This session is not at the reflection step.")

        session.outcome = outcome
        session.status = SessionStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        # S14 only shows when the user actually acted (BRD: no exceptions).
        if session.completion_status:
            session.current_screen = CoachingScreen.S14_LEARNING

        self.db.commit()
        self.db.refresh(session)
        return session

    # ------------------------------------------------------------------
    # S14: learning recommendations (deterministic v1; RAG replaces ranking later)
    # ------------------------------------------------------------------

    def get_recommendations(self, user_id: int, session_id: int, limit: int = 2) -> List[DailyLesson]:
        session = self.get_session(user_id, session_id)

        if not session.completion_status:
            # BRD rule: learning after action only.
            raise APIException(
                status_code=400,
                message="Learning content unlocks after you've had the conversation.",
            )
        if not session.diagnosis_type:
            raise APIException(status_code=400, message="This session has no diagnosis yet.")

        categories = decision_tree.DIAGNOSIS_CATEGORY_MAP[session.diagnosis_type]
        candidates = (
            self.db.query(DailyLesson)
            .join(Week, DailyLesson.week_id == Week.id)
            .filter(Week.topic.in_(categories))
            .order_by(Week.week_number, DailyLesson.day_number)
            .all()
        )
        print(f"Candidates: {len(candidates)}")

        # Semantic ranking: order candidates by how well their content matches
        # the user's actual problem. Falls back to tag/week order when RAG
        # isn't available (no API key, no chunks yet).
        from app.services import rag_service
        ranked_ids = rag_service.rank_lessons_semantically(
            self.db, session.problem_detail or "", [c.id for c in candidates]
        )
        print(f"Ranked IDs: {ranked_ids}")
        if ranked_ids:
            position = {lesson_id: i for i, lesson_id in enumerate(ranked_ids)}
            candidates.sort(key=lambda l: position.get(l.id, len(position)))
            return candidates[:limit]

        # Fallback ordering: prefer lessons explicitly tagged with this diagnosis.
        tag = session.diagnosis_type.value
        tagged = [l for l in candidates if l.diagnosis_tags and tag in l.diagnosis_tags]
        untagged = [l for l in candidates if l not in tagged]
        return (tagged + untagged)[:limit]

    def count_scenario_occurrences(self, user_id: int, scenario_type: ScenarioType) -> int:
        """BRD pattern logic: same scenario_type 3+ times -> targeted recommendation."""
        return (
            self.db.query(CoachingSession)
            .filter(
                CoachingSession.user_id == user_id,
                CoachingSession.scenario_type == scenario_type,
            )
            .count()
        )

    # ------------------------------------------------------------------
    # Screen payload: what the client should render right now
    # ------------------------------------------------------------------

    def get_screen_payload(self, session: CoachingSession) -> dict:
        screen = session.current_screen
        definition = decision_tree.SCREEN_DEFINITIONS[screen]
        payload = {
            "screen": screen,
            "prompt": definition["prompt"],
            "options": definition["options"],
            "content": None,
            "previous_answer": self._previous_answer_for_screen(session, screen),
        }

        if screen == CoachingScreen.S6_DIAGNOSIS and session.diagnosis_type:
            payload["content"] = {
                "diagnosis": session.diagnosis_type.value,
                "statement": decision_tree.DIAGNOSIS_STATEMENTS[session.diagnosis_type],
            }
        elif screen == CoachingScreen.S7_GUIDANCE and session.diagnosis_type:
            payload["content"] = session.generated_guidance
        elif screen == CoachingScreen.S8_CONVERSATION_BUILDER:
            payload["content"] = {"script": decision_tree.build_opening_script(session)}
        elif screen == CoachingScreen.S9_CONVERSATION_STEPS:
            payload["content"] = {"steps": decision_tree.CONVERSATION_STEPS}
        elif screen == CoachingScreen.S11_FOLLOW_UP_SCHEDULED:
            timing_labels = {
                ActionTiming.TODAY: "later today",
                ActionTiming.TOMORROW: "tomorrow morning",
                ActionTiming.THIS_WEEK: "in a couple of days",
            }
            payload["content"] = {
                "message": f"Got it. I'll check back {timing_labels.get(session.action_timing, 'soon')}.",
                "follow_up_scheduled_at": (
                    session.follow_up_scheduled_at.isoformat()
                    if session.follow_up_scheduled_at else None
                ),
            }

        return payload

    def _previous_answer_for_screen(
        self, session: CoachingSession, screen: CoachingScreen
    ) -> Optional[Dict[str, Any]]:
        """Pre-fill hint for the client when the user navigates back."""
        if screen == CoachingScreen.S1_ENTRY:
            if session.scenario_type:
                return {"option": session.scenario_type.value}
            if session.raw_input_text:
                return {"free_text": session.raw_input_text}
            return None
        if screen == CoachingScreen.S2_USER_INPUT:
            return {"free_text": session.raw_input_text} if session.raw_input_text else None
        if screen == CoachingScreen.S3_SPECIFICS:
            return {"free_text": session.problem_detail} if session.problem_detail else None
        if screen == CoachingScreen.S4_DURATION:
            return {"option": session.duration.value} if session.duration else None
        if screen == CoachingScreen.S5_ACCOUNTABILITY:
            if session.accountability_flag is None:
                return None
            return {"option": "yes" if session.accountability_flag else "no"}
        if screen == CoachingScreen.S10_COMMITMENT:
            return {"option": session.action_timing.value} if session.action_timing else None
        return None

    def _invalidate_from_raw_input(self, session: CoachingSession) -> None:
        session.raw_input_text = None
        self._invalidate_from_problem_detail(session)

    def _invalidate_from_problem_detail(self, session: CoachingSession) -> None:
        session.problem_detail = None
        self._invalidate_from_duration(session)

    def _invalidate_from_duration(self, session: CoachingSession) -> None:
        session.duration = None
        self._invalidate_from_accountability(session)

    def _invalidate_from_accountability(self, session: CoachingSession) -> None:
        session.accountability_flag = None
        session.is_avoidance_case = False
        session.diagnosis_type = None
        session.generated_guidance = None
        self._invalidate_commitment(session)

    def _invalidate_commitment(self, session: CoachingSession) -> None:
        session.action_timing = None
        session.follow_up_scheduled_at = None
        if session.status == SessionStatus.AWAITING_ACTION:
            session.status = SessionStatus.IN_PROGRESS

    # ------------------------------------------------------------------
    # Input parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_enum(enum_cls, value: str, label: str):
        try:
            return enum_cls(value.strip().lower())
        except ValueError:
            valid = ", ".join(e.value for e in enum_cls)
            raise APIException(status_code=400, message=f"Invalid {label} '{value}'. Valid values: {valid}")

    @staticmethod
    def _parse_yes_no(value: Optional[str]) -> bool:
        if value:
            lowered = value.strip().lower()
            if lowered in ("yes", "y", "true", "yeah", "yep", "i have", "i did"):
                return True
            if lowered in ("no", "n", "false", "nope", "not yet", "i haven't"):
                return False
        raise APIException(status_code=400, message="Please answer yes or no.")

    @staticmethod
    def _duration_from_text(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        lowered = text.lower()
        if any(kw in lowered for kw in ("year", "long", "always", "forever")):
            return IssueDuration.LONG_TIME.value
        if "month" in lowered:
            return IssueDuration.MONTHS.value
        if "week" in lowered:
            return IssueDuration.WEEKS.value
        if any(kw in lowered for kw in ("just", "day", "recent", "new")):
            return IssueDuration.JUST_STARTED.value
        return None

    @staticmethod
    def _timing_from_text(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        lowered = text.lower()
        if "today" in lowered or "now" in lowered or "tonight" in lowered:
            return ActionTiming.TODAY.value
        if "tomorrow" in lowered:
            return ActionTiming.TOMORROW.value
        if "week" in lowered:
            return ActionTiming.THIS_WEEK.value
        return None
