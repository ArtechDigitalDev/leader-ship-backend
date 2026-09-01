"""
Lesson chunking — breaks a DailyLesson into retrievable pieces aligned with
DailyLessonBase (app/schemas/daily_lesson.py).

Each major lesson section maps to one or more chunks:
  daily_tip       → 1 chunk
  swipe_cards[]   → 1 chunk per card (The Trap / The Shift / The Tool / The Reminder)
  scenario        → 1 chunk (story + choices + explanation)
  go_deeper[]     → 1 chunk per resource (type, title, description, link)
  reflection      → 1 chunk
  leader_win      → 1 chunk
"""
from typing import Any, Dict, List, Optional

from app.models.daily_lesson import DailyLesson


def _as_text(value) -> str:
    """SwipeCard.content may be a string or a list of strings."""
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value) if value else ""


def _pick(data: Dict[str, Any], *keys: str) -> str:
    """Read a JSON field supporting both snake_case (API schema) and legacy camelCase."""
    for key in keys:
        value = data.get(key)
        if value:
            return str(value)
    return ""


def _format_go_deeper_item(item: Dict[str, Any]) -> Optional[str]:
    """
    Build searchable text for one GoDeeper resource.
    Title often carries the full summary even when description is empty.
    """
    resource_type = (item.get("type") or "resource").strip().title()
    title = (item.get("title") or "").strip()
    description = (item.get("description") or "").strip()
    link = (item.get("link") or "").strip()

    if not title and not description and not link:
        return None

    parts = [f"[{resource_type}]"]
    if title:
        parts.append(title)
    if description:
        parts.append(f"Summary: {description}")
    if link:
        parts.append(f"Link: {link}")

    return " | ".join(parts)


def _chunk(chunk_type: str, content: Optional[str]) -> Optional[dict]:
    if not content:
        return None
    content = " ".join(content.split())
    if len(content) < 20:
        return None
    return {"chunk_type": chunk_type, "content": content}


def build_chunks_for_lesson(lesson: DailyLesson) -> List[dict]:
    """
    Returns [{"chunk_type", "content", "metadata"}] for one lesson.
    Typically 8-10 chunks per lesson (4 swipe cards + other sections).
    """
    chunks: List[dict] = []

    # --- daily_tip (DailyTip) -----------------------------------------------
    tip = lesson.daily_tip or {}
    chunks.append(_chunk(
        "daily_tip",
        f"{lesson.title}. When to use: {_pick(tip, 'when_to_use', 'whenToUse')} "
        f"Top takeaway: {_pick(tip, 'top_takeaway', 'topTakeaway')}",
    ))

    # --- swipe_cards (List[SwipeCard]) — one chunk per card -------------------
    for card in (lesson.swipe_cards or []):
        title = card.get("title", "")
        body = _as_text(card.get("content"))
        chunks.append(_chunk("swipe_card", f"{title}: {body}" if title else body))

    # --- scenario (Scenario) — story, choices, and explanation together -------
    scenario = lesson.scenario or {}
    choice_lines = [
        f"{c.get('label', '')}: {c.get('text', '')}"
        for c in (scenario.get("choices") or [])
        if c.get("text")
    ]
    chunks.append(_chunk(
        "scenario",
        f"Scenario: {scenario.get('story', '')} "
        f"Choices: {' | '.join(choice_lines)} "
        f"Best approach: {scenario.get('explanation', '')}",
    ))

    # --- reflection_prompt ----------------------------------------------------
    chunks.append(_chunk("reflection", f"Reflection: {lesson.reflection_prompt or ''}"))

    # --- leader_win -----------------------------------------------------------
    chunks.append(_chunk("leader_win", f"Leader win: {lesson.leader_win or ''}"))

    # --- go_deeper (List[GoDeeper]) — one chunk per resource ------------------
    for item in (lesson.go_deeper or []):
        chunks.append(_chunk("go_deeper", _format_go_deeper_item(item)))

    metadata = {
        "lesson_id": lesson.id,
        "lesson_title": lesson.title,
        "category": lesson.week.topic if lesson.week else None,
        "week_id": lesson.week_id,
        "diagnosis_tags": lesson.diagnosis_tags or [],
    }

    result = []
    for chunk in chunks:
        if chunk is not None:
            chunk["metadata"] = metadata
            result.append(chunk)
    return result
