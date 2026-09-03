r"""Smoke tests for coaching back navigation (no DB).

Usage: venv\Scripts\python.exe scripts\test_coaching_navigation.py
"""
import os
import sys
from datetime import datetime
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.coaching_session import (
    ActionTiming,
    CoachingScreen,
    CoachingSession,
    DiagnosisType,
    IssueDuration,
    ScenarioType,
    SessionStatus,
)
from app.services import decision_tree as dt
from app.services.coaching_session_service import CoachingSessionService
from app.utils.response import APIException

failures = []


def check(name, actual, expected):
    ok = actual == expected
    print(f"{'PASS' if ok else 'FAIL'}: {name} -> {actual}")
    if not ok:
        failures.append((name, actual, expected))


# --- decision_tree prev_screen ------------------------------------------------
check("prev of S1", dt.prev_screen(CoachingScreen.S1_ENTRY), None)
check("prev of S3", dt.prev_screen(CoachingScreen.S3_SPECIFICS), CoachingScreen.S2_USER_INPUT)
check("prev of S11", dt.prev_screen(CoachingScreen.S11_FOLLOW_UP_SCHEDULED), CoachingScreen.S10_COMMITMENT)

service = CoachingSessionService(db=MagicMock())


def make_session(**kwargs):
    defaults = dict(
        user_id=1,
        status=SessionStatus.IN_PROGRESS,
        current_screen=CoachingScreen.S5_ACCOUNTABILITY,
    )
    defaults.update(kwargs)
    return CoachingSession(**defaults)


# --- start resumes open sessions (in_progress + awaiting_action) --------------
awaiting = make_session(
    current_screen=CoachingScreen.S11_FOLLOW_UP_SCHEDULED,
    status=SessionStatus.AWAITING_ACTION,
)
service.get_open_session = MagicMock(return_value=awaiting)
session, created = service.start_or_resume_session(1)
check("start resumes awaiting_action", session.current_screen, CoachingScreen.S11_FOLLOW_UP_SCHEDULED)
check("start does not create when awaiting", created, False)
service.db.add.assert_not_called()

in_prog = make_session(current_screen=CoachingScreen.S4_DURATION)
service.get_open_session = MagicMock(return_value=in_prog)
session, created = service.start_or_resume_session(1)
check("start resumes in_progress", session.current_screen, CoachingScreen.S4_DURATION)
check("start does not create when in_progress", created, False)

service.get_open_session = MagicMock(return_value=None)
service.db.add = MagicMock()
service.db.commit = MagicMock()
service.db.refresh = MagicMock()
session, created = service.start_or_resume_session(1)
check("start creates when no open session", created, True)
check("new session starts at S1", session.current_screen, CoachingScreen.S1_ENTRY)
service.db.add.assert_called_once()


# --- go_back one step ---------------------------------------------------------
session = make_session(current_screen=CoachingScreen.S5_ACCOUNTABILITY)
service.get_session = MagicMock(return_value=session)
service.go_back(1, 99)
check("back S5 -> S4", session.current_screen, CoachingScreen.S4_DURATION)

# --- go_back S11 resets commitment state --------------------------------------
session = make_session(
    current_screen=CoachingScreen.S11_FOLLOW_UP_SCHEDULED,
    status=SessionStatus.AWAITING_ACTION,
    action_timing=ActionTiming.TODAY,
    follow_up_scheduled_at=datetime.utcnow(),
)
service.get_session = MagicMock(return_value=session)
service.go_back(1, 99)
check("back S11 -> S10", session.current_screen, CoachingScreen.S10_COMMITMENT)
check("back S11 status", session.status, SessionStatus.IN_PROGRESS)
check("back S11 clears follow_up", session.follow_up_scheduled_at, None)

# --- go_back blocked on S1 ----------------------------------------------------
session = make_session(current_screen=CoachingScreen.S1_ENTRY)
service.get_session = MagicMock(return_value=session)
try:
    service.go_back(1, 99)
    check("back from S1 raises", False, True)
except APIException:
    check("back from S1 raises", True, True)

# --- S3 re-save clears downstream ---------------------------------------------
session = make_session(
    current_screen=CoachingScreen.S3_SPECIFICS,
    raw_input_text="issue",
    problem_detail="old detail",
    duration=IssueDuration.MONTHS,
    accountability_flag=False,
    is_avoidance_case=True,
    diagnosis_type=DiagnosisType.ACCOUNTABILITY_ISSUE,
    generated_guidance={"bullets": ["old"]},
    action_timing=ActionTiming.TODAY,
)
service._answer_s3(session, None, "new detail")
check("S3 clears duration", session.duration, None)
check("S3 clears diagnosis", session.diagnosis_type, None)
check("S3 clears guidance", session.generated_guidance, None)
check("S3 clears avoidance", session.is_avoidance_case, False)
check("S3 saves detail", session.problem_detail, "new detail")
check("S3 -> S4", session.current_screen, CoachingScreen.S4_DURATION)

# --- S5 re-save resets avoidance + diagnosis ----------------------------------
session = make_session(
    current_screen=CoachingScreen.S5_ACCOUNTABILITY,
    duration=IssueDuration.MONTHS,
    problem_detail="unclear expectations",
    accountability_flag=False,
    is_avoidance_case=True,
    diagnosis_type=DiagnosisType.ACCOUNTABILITY_ISSUE,
    generated_guidance={"bullets": ["old"]},
)
service._answer_s5(session, "yes", None)
check("S5 yes clears avoidance", session.is_avoidance_case, False)
check("S5 clears guidance", session.generated_guidance, None)
check("S5 re-diagnose", session.diagnosis_type, DiagnosisType.CLARITY_ISSUE)

# --- previous_answer pre-fill -------------------------------------------------
session = make_session(
    current_screen=CoachingScreen.S4_DURATION,
    duration=IssueDuration.MONTHS,
    problem_detail="reports late",
)
payload = service._previous_answer_for_screen(session, CoachingScreen.S3_SPECIFICS)
check("previous S3", payload, {"free_text": "reports late"})

print()
if failures:
    print(f"{len(failures)} FAILURES")
    sys.exit(1)
print("ALL PASSED")
