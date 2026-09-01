"""
Decision Tree Engine — BRD v2 Section 2.3 & 3.

Deterministic branching logic for the 14-screen coaching flow.
No LLM is involved here: diagnosis and screen progression are pure rules,
so they are cheap, testable and predictable.

Text classification (scenario from free text, signals in problem_detail)
currently uses keyword heuristics. These two functions are the designated
swap-points for an LLM classifier later — their signatures will not change.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.models.coaching_session import (
    ScenarioType,
    IssueDuration,
    DiagnosisType,
    ActionTiming,
    CoachingScreen,
    CoachingSession,
)


# ---------------------------------------------------------------------------
# Screen flow (BRD Section 3: "Every screen moves forward. No dead ends.")
# ---------------------------------------------------------------------------

SCREEN_ORDER: List[CoachingScreen] = [
    CoachingScreen.S1_ENTRY,
    CoachingScreen.S2_USER_INPUT,
    CoachingScreen.S3_SPECIFICS,
    CoachingScreen.S4_DURATION,
    CoachingScreen.S5_ACCOUNTABILITY,
    CoachingScreen.S6_DIAGNOSIS,
    CoachingScreen.S7_GUIDANCE,
    CoachingScreen.S8_CONVERSATION_BUILDER,
    CoachingScreen.S9_CONVERSATION_STEPS,
    CoachingScreen.S10_COMMITMENT,
    CoachingScreen.S11_FOLLOW_UP_SCHEDULED,
    CoachingScreen.S12_CHECK_IN,
    CoachingScreen.S13_REFLECTION,
    CoachingScreen.S14_LEARNING,
]


def next_screen(current: CoachingScreen) -> Optional[CoachingScreen]:
    """Return the next screen in the flow, or None if current is the last."""
    index = SCREEN_ORDER.index(current)
    if index + 1 < len(SCREEN_ORDER):
        return SCREEN_ORDER[index + 1]
    return None


# ---------------------------------------------------------------------------
# Screen definitions (prompt + options shown to the client)
# ---------------------------------------------------------------------------

SCREEN_DEFINITIONS: Dict[CoachingScreen, dict] = {
    CoachingScreen.S1_ENTRY: {
        "prompt": "What's going on right now?",
        "options": [
            {"value": ScenarioType.UNDERPERFORMANCE.value, "label": "Underperformance"},
            {"value": ScenarioType.DIFFICULT_CONVERSATION.value, "label": "Difficult conversation"},
            {"value": ScenarioType.RETENTION_RISK.value, "label": "Retention risk"},
            {"value": ScenarioType.CONFLICT.value, "label": "Conflict"},
            {"value": ScenarioType.SOMETHING_ELSE.value, "label": "Something else"},
        ],
    },
    CoachingScreen.S2_USER_INPUT: {
        "prompt": "Tell me what's happening, in your own words.",
        "options": [],
    },
    CoachingScreen.S3_SPECIFICS: {
        "prompt": "What specifically isn't happening that should be?",
        "options": [],
    },
    CoachingScreen.S4_DURATION: {
        "prompt": "How long has this been happening?",
        "options": [
            {"value": IssueDuration.JUST_STARTED.value, "label": "Just started"},
            {"value": IssueDuration.WEEKS.value, "label": "Weeks"},
            {"value": IssueDuration.MONTHS.value, "label": "Months"},
            {"value": IssueDuration.LONG_TIME.value, "label": "Long time"},
        ],
    },
    CoachingScreen.S5_ACCOUNTABILITY: {
        "prompt": "Have you spoken to this person directly about the issue?",
        "options": [
            {"value": "yes", "label": "Yes"},
            {"value": "no", "label": "No"},
        ],
    },
    CoachingScreen.S6_DIAGNOSIS: {
        "prompt": "Here's what I think is going on.",
        "options": [{"value": "continue", "label": "Continue"}],
    },
    CoachingScreen.S7_GUIDANCE: {
        "prompt": "Here's how to handle it.",
        "options": [{"value": "continue", "label": "Continue"}],
    },
    CoachingScreen.S8_CONVERSATION_BUILDER: {
        "prompt": "Here's an opening script you can use.",
        "options": [{"value": "continue", "label": "Continue"}],
    },
    CoachingScreen.S9_CONVERSATION_STEPS: {
        "prompt": "Walk through the conversation step by step.",
        "options": [{"value": "continue", "label": "Continue"}],
    },
    CoachingScreen.S10_COMMITMENT: {
        "prompt": "When will you have this conversation?",
        "options": [
            {"value": ActionTiming.TODAY.value, "label": "Today"},
            {"value": ActionTiming.TOMORROW.value, "label": "Tomorrow"},
            {"value": ActionTiming.THIS_WEEK.value, "label": "This week"},
        ],
    },
    CoachingScreen.S11_FOLLOW_UP_SCHEDULED: {
        "prompt": "Got it. I'll check back with you.",
        "options": [],
    },
    CoachingScreen.S12_CHECK_IN: {
        "prompt": "Did you have that conversation?",
        "options": [
            {"value": "yes", "label": "Yes"},
            {"value": "no", "label": "No"},
        ],
    },
    CoachingScreen.S13_REFLECTION: {
        "prompt": "How did it go?",
        "options": [
            {"value": "good", "label": "Good"},
            {"value": "mixed", "label": "Mixed"},
            {"value": "bad", "label": "Bad"},
        ],
    },
    CoachingScreen.S14_LEARNING: {
        "prompt": "Want to build this skill long-term? These modules match your situation.",
        "options": [],
    },
}


# ---------------------------------------------------------------------------
# Text classification (LLM swap-points — keyword heuristics for now)
# ---------------------------------------------------------------------------

_SCENARIO_KEYWORDS: Dict[ScenarioType, List[str]] = {
    ScenarioType.UNDERPERFORMANCE: [
        "underperform", "not performing", "poor performance", "missing deadline",
        "missed deadline", "low quality", "not delivering", "output", "productivity",
    ],
    ScenarioType.DIFFICULT_CONVERSATION: [
        "difficult conversation", "hard conversation", "awkward", "feedback",
        "confront", "tough talk", "uncomfortable",
    ],
    ScenarioType.RETENTION_RISK: [
        "quit", "leaving", "resign", "retention", "another job", "offer",
        "disengaged", "checked out",
    ],
    ScenarioType.CONFLICT: [
        "conflict", "argument", "fighting", "tension", "clash", "dispute",
        "not getting along",
    ],
}

_UNCLEAR_EXPECTATION_KEYWORDS: List[str] = [
    "unclear", "not clear", "confus", "didn't know", "doesn't know", "don't know",
    "expectation", "never told", "wasn't told", "no idea", "ambiguous",
    "misunderstood", "misunderstanding",
]

_SUDDEN_CHANGE_KEYWORDS: List[str] = [
    "sudden", "suddenly", "out of nowhere", "recently changed", "changed recently",
    "used to be", "was fine before", "all of a sudden", "overnight", "unexplained",
]


def classify_scenario(text: str) -> ScenarioType:
    """Classify free text into a scenario type (BRD S2). LLM swap-point."""
    lowered = text.lower()
    best_match = ScenarioType.SOMETHING_ELSE
    best_hits = 0
    for scenario, keywords in _SCENARIO_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in lowered)
        if hits > best_hits:
            best_hits = hits
            best_match = scenario
    return best_match


def _indicates_unclear_expectations(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in _UNCLEAR_EXPECTATION_KEYWORDS)


def _indicates_sudden_change(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in _SUDDEN_CHANGE_KEYWORDS)


# ---------------------------------------------------------------------------
# Diagnosis (BRD S6 rules — applied in priority order)
# ---------------------------------------------------------------------------

# Fallback when no rule matches: derived from the scenario the user picked.
_SCENARIO_DEFAULT_DIAGNOSIS: Dict[ScenarioType, DiagnosisType] = {
    ScenarioType.UNDERPERFORMANCE: DiagnosisType.ACCOUNTABILITY_ISSUE,
    ScenarioType.DIFFICULT_CONVERSATION: DiagnosisType.CLARITY_ISSUE,
    ScenarioType.RETENTION_RISK: DiagnosisType.CONTEXT_ISSUE,
    ScenarioType.CONFLICT: DiagnosisType.CLARITY_ISSUE,
    ScenarioType.SOMETHING_ELSE: DiagnosisType.CLARITY_ISSUE,
}

DIAGNOSIS_STATEMENTS: Dict[DiagnosisType, str] = {
    DiagnosisType.ACCOUNTABILITY_ISSUE: (
        "This looks like an accountability issue — the expectation exists, "
        "but it hasn't been directly addressed for long enough that it has become the norm."
    ),
    DiagnosisType.CLARITY_ISSUE: (
        "This looks like a clarity issue — the expectations were likely "
        "never made explicit, so the other person may not know what 'good' looks like."
    ),
    DiagnosisType.CONTEXT_ISSUE: (
        "This looks like a context issue — something changed in this person's "
        "situation, and the behaviour is a symptom of it."
    ),
}


def diagnose(session: CoachingSession) -> DiagnosisType:
    """
    BRD Section 3, S6 rules in priority order:
      1. duration = months/long time AND accountability_flag = No -> accountability_issue
      2. problem_detail indicates unclear expectations -> clarity_issue
      3. problem_detail indicates sudden behaviour change -> context_issue
      4. (fallback) default by scenario_type
    """
    long_running = session.duration in (IssueDuration.MONTHS, IssueDuration.LONG_TIME)
    if long_running and session.accountability_flag is False:
        return DiagnosisType.ACCOUNTABILITY_ISSUE

    detail = f"{session.problem_detail or ''} {session.raw_input_text or ''}"
    if _indicates_unclear_expectations(detail):
        return DiagnosisType.CLARITY_ISSUE
    if _indicates_sudden_change(detail):
        return DiagnosisType.CONTEXT_ISSUE

    scenario = session.scenario_type or ScenarioType.SOMETHING_ELSE
    return _SCENARIO_DEFAULT_DIAGNOSIS[scenario]


# ---------------------------------------------------------------------------
# Follow-up scheduling (BRD Section 2.5)
# ---------------------------------------------------------------------------

def calculate_follow_up_time(
    action_timing: ActionTiming,
    is_avoidance_case: bool,
    now: Optional[datetime] = None,
) -> datetime:
    """
    Notification schedule:
      - today      -> in 6-8 hours (we use 7h)
      - tomorrow   -> next morning 9 AM
      - this week  -> in 2-3 days (we use 2.5 days)
    Avoidance case: all intervals halved.
    """
    now = now or datetime.utcnow()

    if action_timing == ActionTiming.TODAY:
        delta = timedelta(hours=7)
    elif action_timing == ActionTiming.TOMORROW:
        next_morning = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        delta = next_morning - now
    else:  # THIS_WEEK
        delta = timedelta(days=2, hours=12)

    if is_avoidance_case:
        delta = delta / 2

    return now + delta


# ---------------------------------------------------------------------------
# Learning content mapping (BRD S14) — deterministic v1.
# The RAG layer (Phase 2) will replace category filtering with
# semantic ranking over lesson_chunks; this map stays as the pre-filter.
# ---------------------------------------------------------------------------

DIAGNOSIS_CATEGORY_MAP: Dict[DiagnosisType, List[str]] = {
    # accountability / follow-through track
    DiagnosisType.ACCOUNTABILITY_ISSUE: ["Consistency", "Courage"],
    # expectations / communication track
    DiagnosisType.CLARITY_ISSUE: ["Clarity", "Connection"],
    # situational leadership track
    DiagnosisType.CONTEXT_ISSUE: ["Curiosity", "Connection"],
}


# ---------------------------------------------------------------------------
# Placeholder guidance content (until the RAG knowledge base is live).
# BRD S7 fallback rule: never hallucinate — serve approved general content.
# ---------------------------------------------------------------------------

GUIDANCE_FALLBACK: Dict[DiagnosisType, List[str]] = {
    DiagnosisType.ACCOUNTABILITY_ISSUE: [
        "Name the pattern, not the person: describe what has been happening and for how long.",
        "Own your part: acknowledge that it hasn't been addressed directly before now.",
        "Reset the expectation clearly and agree on what changes starting today.",
        "Set a specific check-in date so the new expectation has follow-through.",
    ],
    DiagnosisType.CLARITY_ISSUE: [
        "Start by asking what they understand the expectation to be — don't assume.",
        "State the expectation in concrete, observable terms.",
        "Check for agreement: ask them to describe what success looks like.",
        "Agree on how you'll both know it's on track.",
    ],
    DiagnosisType.CONTEXT_ISSUE: [
        "Open with curiosity, not correction — something has changed for this person.",
        "Ask an open question about how things are going before raising the issue.",
        "Listen for the underlying cause before proposing any fix.",
        "Agree on support first, expectations second.",
    ],
}

CONVERSATION_STEPS: List[str] = [
    "Ask your opening question, then stop talking.",
    "Pause. Let them fill the silence — don't rescue them.",
    "Reflect back what you heard in one sentence.",
    "Align on the expectation going forward.",
    "Agree when you'll check in next.",
]


def build_opening_script(session: CoachingSession) -> str:
    """
    BRD S8: template selected by scenario_type + diagnosis_type, personalised
    with the user's own problem_detail and duration.
    Template-based v1; the RAG layer will source richer templates later.
    """
    duration_phrases = {
        IssueDuration.JUST_STARTED: "recently",
        IssueDuration.WEEKS: "over the past few weeks",
        IssueDuration.MONTHS: "over the past few months",
        IssueDuration.LONG_TIME: "for quite a while now",
    }
    duration_phrase = duration_phrases.get(session.duration, "recently")
    problem = (session.problem_detail or "the issue we need to talk about").strip().rstrip(".")

    openers = {
        DiagnosisType.ACCOUNTABILITY_ISSUE: (
            f"\"I want to talk about something I should have raised earlier. "
            f"{duration_phrase.capitalize()}, I've noticed that {problem}. "
            f"I haven't addressed it directly, and that's on me. "
            f"Can we talk about what's getting in the way?\""
        ),
        DiagnosisType.CLARITY_ISSUE: (
            f"\"I'd like to check we're on the same page. {duration_phrase.capitalize()}, "
            f"I've noticed that {problem}. I'm wondering if I've been clear about "
            f"what I'm expecting — can you tell me how you see it?\""
        ),
        DiagnosisType.CONTEXT_ISSUE: (
            f"\"I've noticed some changes {duration_phrase} — specifically, {problem}. "
            f"That's not like you, and I wanted to check in. How are things going?\""
        ),
    }
    diagnosis = session.diagnosis_type or DiagnosisType.CLARITY_ISSUE
    return openers[diagnosis]
