"""
Lesson chunking — breaks a DailyLesson into small retrievable text pieces.

Each chunk is one coherent idea (a swipe card, the daily tip, the scenario...)
so RAG retrieval can match the user's problem to a specific piece of advice
instead of a whole lesson. Chunk dicts are consumed by rag_service.ingest_lesson.
"""
from typing import List, Optional

from app.models.daily_lesson import DailyLesson


def _as_text(value) -> str:
    """swipe_card content may be a string or a list of strings."""
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value) if value else ""


def _chunk(chunk_type: str, content: str) -> Optional[dict]:
    content = " ".join(content.split())  # collapse whitespace
    if len(content) < 20:  # too short to be a meaningful retrieval unit
        return None
    return {"chunk_type": chunk_type, "content": content}


def build_chunks_for_lesson(lesson: DailyLesson) -> List[dict]:
    """
    Returns [{"chunk_type", "content", "metadata"}] for one lesson.
    Typically 5-9 chunks per lesson.
    """
    chunks: List[dict] = []

    # Daily tip: whenToUse + topTakeaway together form one idea
    tip = lesson.daily_tip or {}
    chunks.append(_chunk(
        "daily_tip",
        f"{lesson.title}. When to use: {tip.get('whenToUse', '')} "
        f"Top takeaway: {tip.get('topTakeaway', '')}",
    ))

    # Each swipe card is its own retrieval unit
    for card in (lesson.swipe_cards or []):
        title = card.get("title", "")
        body = _as_text(card.get("content"))
        chunks.append(_chunk("swipe_card", f"{title}: {body}" if title else body))

    # Scenario: the story plus the explanation of the right choice
    scenario = lesson.scenario or {}
    chunks.append(_chunk(
        "scenario",
        f"Scenario: {scenario.get('story', '')} "
        f"What works: {scenario.get('explanation', '')}",
    ))

    # Reflection prompt + leader win as one reflective chunk
    chunks.append(_chunk(
        "reflection",
        f"Reflection: {lesson.reflection_prompt or ''} Leader win: {lesson.leader_win or ''}",
    ))

    # Go-deeper descriptions (links themselves aren't useful text)
    deeper_texts = [
        f"{item.get('title', '')}: {item.get('description', '')}"
        for item in (lesson.go_deeper or [])
        if item.get("description")
    ]
    if deeper_texts:
        chunks.append(_chunk("go_deeper", " | ".join(deeper_texts)))

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
