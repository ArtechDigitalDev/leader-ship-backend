r"""Manual smoke test for the coaching decision tree engine (no DB needed).

Usage: venv\Scripts\python.exe scripts\test_decision_tree.py
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.coaching_session import (
    CoachingSession, ScenarioType, IssueDuration, DiagnosisType, ActionTiming, CoachingScreen,
)
from app.services import decision_tree as dt

failures = []

def check(name, actual, expected):
    ok = actual == expected
    print(f"{'PASS' if ok else 'FAIL'}: {name} -> {actual}")
    if not ok:
        failures.append((name, actual, expected))

# Rule 1: long duration + not addressed -> accountability
s = CoachingSession(duration=IssueDuration.MONTHS, accountability_flag=False,
                    problem_detail="he keeps missing targets", scenario_type=ScenarioType.CONFLICT)
check("rule1 accountability", dt.diagnose(s), DiagnosisType.ACCOUNTABILITY_ISSUE)

# Rule 2: unclear expectations -> clarity (even if addressed)
s = CoachingSession(duration=IssueDuration.WEEKS, accountability_flag=True,
                    problem_detail="I think the expectations were never clear to her",
                    scenario_type=ScenarioType.UNDERPERFORMANCE)
check("rule2 clarity", dt.diagnose(s), DiagnosisType.CLARITY_ISSUE)

# Rule 3: sudden change -> context
s = CoachingSession(duration=IssueDuration.JUST_STARTED, accountability_flag=True,
                    problem_detail="he suddenly stopped participating in meetings",
                    scenario_type=ScenarioType.UNDERPERFORMANCE)
check("rule3 context", dt.diagnose(s), DiagnosisType.CONTEXT_ISSUE)

# Fallback: scenario default
s = CoachingSession(duration=IssueDuration.WEEKS, accountability_flag=True,
                    problem_detail="output is low", scenario_type=ScenarioType.UNDERPERFORMANCE)
check("fallback underperformance", dt.diagnose(s), DiagnosisType.ACCOUNTABILITY_ISSUE)

# Scenario classification
check("classify retention", dt.classify_scenario("I think she is about to quit and has another job offer"),
      ScenarioType.RETENTION_RISK)
check("classify unknown", dt.classify_scenario("xyz gibberish"), ScenarioType.SOMETHING_ELSE)

# Screen order: 14 screens, forward only
check("screen count", len(dt.SCREEN_ORDER), 14)
check("next of S1", dt.next_screen(CoachingScreen.S1_ENTRY), CoachingScreen.S2_USER_INPUT)
check("next of S14", dt.next_screen(CoachingScreen.S14_LEARNING), None)

# Follow-up scheduling
now = datetime(2026, 9, 1, 12, 0, 0)
t = dt.calculate_follow_up_time(ActionTiming.TODAY, False, now)
check("today +7h", (t - now).total_seconds() / 3600, 7.0)
t = dt.calculate_follow_up_time(ActionTiming.TODAY, True, now)
check("today avoidance +3.5h", (t - now).total_seconds() / 3600, 3.5)
t = dt.calculate_follow_up_time(ActionTiming.TOMORROW, False, now)
check("tomorrow 9am", (t.day, t.hour), (2, 9))
t = dt.calculate_follow_up_time(ActionTiming.THIS_WEEK, False, now)
check("this week +2.5d", (t - now).total_seconds() / 3600, 60.0)
t = dt.calculate_follow_up_time(ActionTiming.THIS_WEEK, True, now)
check("this week avoidance +1.25d", (t - now).total_seconds() / 3600, 30.0)

# Script personalisation
s = CoachingSession(duration=IssueDuration.MONTHS, problem_detail="reports are late every week",
                    diagnosis_type=DiagnosisType.ACCOUNTABILITY_ISSUE)
script = dt.build_opening_script(s)
check("script includes problem", "reports are late every week" in script, True)
check("script includes duration", "past few months" in script, True)

# All diagnoses have statements + category mapping
for d in DiagnosisType:
    check(f"statement for {d.value}", bool(dt.DIAGNOSIS_STATEMENTS[d]), True)
    check(f"categories for {d.value}", len(dt.DIAGNOSIS_CATEGORY_MAP[d]) > 0, True)

print()
if failures:
    print(f"{len(failures)} FAILURES")
    sys.exit(1)
print("ALL PASSED")
