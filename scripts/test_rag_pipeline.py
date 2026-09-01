"""
Manual smoke test for the RAG pipeline (no DB, no API key needed).

Verifies chunking, cosine math, and that every RAG entry point degrades
gracefully to fallback behaviour when OPENAI_API_KEY is not configured.

Usage: venv\\Scripts\\python.exe scripts\\test_rag_pipeline.py
"""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

failures = []


def check(name, actual, expected):
    ok = actual == expected
    print(f"{'PASS' if ok else 'FAIL'}: {name} -> {actual}")
    if not ok:
        failures.append((name, actual, expected))


# --- Chunking ---------------------------------------------------------------
from app.services.lesson_chunking import build_chunks_for_lesson

fake_lesson = SimpleNamespace(
    id=42,
    title="Following Through on Expectations",
    week_id=3,
    week=SimpleNamespace(topic="Consistency"),
    diagnosis_tags=["accountability_issue"],
    daily_tip={"whenToUse": "When a commitment keeps slipping.", "topTakeaway": "Address it within 48 hours."},
    swipe_cards=[
        {"title": "Name the pattern", "content": "Describe what has been happening and for how long."},
        {"title": "Own your part", "content": ["Acknowledge the delay.", "Say it plainly."]},
        {"title": "Tiny", "content": "x"},  # too short -> should be dropped
    ],
    scenario={"story": "A team member misses three deadlines in a row without explanation.",
              "explanation": "Address the pattern directly and reset the expectation together."},
    go_deeper=[{"type": "article", "title": "Follow-through", "description": "Why consistency beats intensity in leadership."}],
    reflection_prompt="Where have you let a missed commitment slide this week?",
    leader_win="One clear expectation reset today.",
)

chunks = build_chunks_for_lesson(fake_lesson)
# daily_tip + 2 valid swipe cards (tiny one dropped) + scenario + reflection + go_deeper
check("chunk count (tiny card dropped)", len(chunks), 6)
check("chunk types", sorted({c["chunk_type"] for c in chunks}),
      ["daily_tip", "go_deeper", "reflection", "scenario", "swipe_card"])
check("metadata category", chunks[0]["metadata"]["category"], "Consistency")
check("metadata tags", chunks[0]["metadata"]["diagnosis_tags"], ["accountability_issue"])
check("list content flattened", any("Acknowledge the delay. Say it plainly." in c["content"] for c in chunks), True)

# --- Cosine similarity ------------------------------------------------------
from app.services.rag_service import _cosine_similarity

check("cosine identical", round(_cosine_similarity([1, 2, 3], [1, 2, 3]), 6), 1.0)
check("cosine orthogonal", _cosine_similarity([1, 0], [0, 1]), 0.0)
check("cosine opposite", round(_cosine_similarity([1, 0], [-1, 0]), 6), -1.0)
check("cosine zero vector", _cosine_similarity([0, 0], [1, 1]), 0.0)

# --- Graceful degradation without API key -----------------------------------
from app.core.config import settings
from app.services import rag_service
from app.services.embedding_service import is_configured

saved_key = settings.OPENAI_API_KEY
settings.OPENAI_API_KEY = None
try:
    check("is_configured without key", is_configured(), False)

    fake_session = SimpleNamespace(problem_detail="reports are late", raw_input_text="", diagnosis_type=None)
    check("guidance -> None without key", rag_service.build_guidance_for_session(None, fake_session), None)
    check("ranking -> None without key", rag_service.rank_lessons_semantically(None, "late reports", [1, 2]), None)
finally:
    settings.OPENAI_API_KEY = saved_key

# --- S7 payload falls back when no generated guidance ------------------------
from app.services.coaching_session_service import CoachingSessionService
from app.models.coaching_session import CoachingScreen, DiagnosisType, ActionTiming

service = CoachingSessionService(db=None)
fake_cs = SimpleNamespace(
    current_screen=CoachingScreen.S7_GUIDANCE,
    diagnosis_type=DiagnosisType.ACCOUNTABILITY_ISSUE,
    generated_guidance=None,
    action_timing=ActionTiming.TODAY,
    follow_up_scheduled_at=None,
    problem_detail="reports late",
    duration=None,
    raw_input_text="",
)
payload = service.get_screen_payload(fake_cs)
check("S7 fallback source", payload["content"]["source"], "fallback")
check("S7 fallback bullets", len(payload["content"]["bullets"]) >= 3, True)

# RAG-cached guidance is served when present
fake_cs.generated_guidance = {"bullets": ["a", "b", "c"], "source": "rag", "chunk_ids": [1]}
payload = service.get_screen_payload(fake_cs)
check("S7 rag source when cached", payload["content"]["source"], "rag")

print()
if failures:
    print(f"{len(failures)} FAILURES")
    sys.exit(1)
print("ALL PASSED")
