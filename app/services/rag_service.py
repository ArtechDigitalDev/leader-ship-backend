"""
RAG service — ingestion, retrieval and grounded guidance generation (BRD v2 Section 2.2).

Hard rules implemented here (BRD):
  - The agent pulls responses ONLY from the knowledge base. The LLM is given
    retrieved excerpts and instructed to use nothing else.
  - If retrieval finds nothing relevant (below RAG_MIN_SIMILARITY), we return
    None and the caller omits S7 guidance — never a hallucination.
  - Every generated response keeps chunk_ids so guidance traces back to
    approved source content.

Similarity search uses pgvector cosine distance in SQL (Neon PostgreSQL).
OpenAI embeddings are unit-normalized, so: similarity = 1 - cosine_distance.
"""
import json
import math
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.coaching_session import CoachingSession, DiagnosisType
from app.models.daily_lesson import DailyLesson
from app.models.lesson_chunk import LessonChunk
from app.services import decision_tree, lesson_chunking
from app.services.embedding_service import EmbeddingUnavailable, embed_query, embed_texts, is_configured


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

def delete_lesson_chunks(db: Session, daily_lesson_id: int) -> int:
    deleted = (
        db.query(LessonChunk)
        .filter(LessonChunk.daily_lesson_id == daily_lesson_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted


def ingest_lesson(db: Session, lesson: DailyLesson) -> int:
    """
    (Re)index one lesson: delete its old chunks, re-chunk, embed, insert.
    Raises EmbeddingUnavailable when no API key is configured.
    Returns the number of chunks created.
    """
    chunk_dicts = lesson_chunking.build_chunks_for_lesson(lesson)
    if not chunk_dicts:
        return 0

    vectors = embed_texts([c["content"] for c in chunk_dicts])

    db.query(LessonChunk).filter(LessonChunk.daily_lesson_id == lesson.id).delete(
        synchronize_session=False
    )
    for chunk_dict, vector in zip(chunk_dicts, vectors):
        db.add(LessonChunk(
            daily_lesson_id=lesson.id,
            source_type="lesson",
            chunk_type=chunk_dict["chunk_type"],
            content=chunk_dict["content"],
            embedding=vector,
            chunk_metadata=chunk_dict["metadata"],
        ))
    db.commit()
    return len(chunk_dicts)


def reindex_lesson_safely(db: Session, lesson: DailyLesson) -> None:
    """Best-effort reindex used by admin create/update hooks — never raises."""
    try:
        count = ingest_lesson(db, lesson)
        print(f"RAG index updated for lesson {lesson.id}: {count} chunks")
    except EmbeddingUnavailable as e:
        print(f"RAG index skipped for lesson {lesson.id} (embeddings unavailable): {e}")
    except Exception as e:
        db.rollback()
        print(f"RAG index failed for lesson {lesson.id}: {e}")


# ---------------------------------------------------------------------------
# Retrieval (pgvector)
# ---------------------------------------------------------------------------

@dataclass
class RetrievedChunk:
    chunk: LessonChunk
    similarity: float


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Unit-test helper — production retrieval uses pgvector SQL instead."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _max_cosine_distance() -> float:
    """OpenAI embeddings are normalized: similarity = 1 - cosine_distance."""
    return 1.0 - settings.RAG_MIN_SIMILARITY


def _vector_search(
    db: Session,
    query_vector: List[float],
    top_k: int,
    diagnosis_type: Optional[DiagnosisType] = None,
    lesson_ids: Optional[List[int]] = None,
) -> List[RetrievedChunk]:
    """
    pgvector cosine search with metadata pre-filter:
      1) diagnosis_tags match
      2) mapped category match
      3) whole corpus
    """
    distance = LessonChunk.embedding.cosine_distance(query_vector)
    max_distance = _max_cosine_distance()

    def run(filters) -> List[RetrievedChunk]:
        q = (
            db.query(LessonChunk, distance.label("distance"))
            .filter(
                LessonChunk.embedding.isnot(None),
                distance <= max_distance,
            )
        )
        if filters is not None:
            q = q.filter(filters)
        if lesson_ids:
            q = q.filter(LessonChunk.daily_lesson_id.in_(lesson_ids))

        rows = q.order_by(distance).limit(top_k).all()
        return [
            RetrievedChunk(chunk=row[0], similarity=1.0 - float(row[1]))
            for row in rows
        ]

    if diagnosis_type:
        tag = diagnosis_type.value
        categories = decision_tree.DIAGNOSIS_CATEGORY_MAP[diagnosis_type]
        meta = cast(LessonChunk.chunk_metadata, JSONB)

        for filt in (
            meta.contains({"diagnosis_tags": [tag]}),
            meta["category"].astext.in_(categories),
            None,
        ):
            results = run(filt)
            if results:
                return results
        return []

    return run(None)


def retrieve(
    db: Session,
    query_text: str,
    diagnosis_type: Optional[DiagnosisType] = None,
    top_k: Optional[int] = None,
) -> List[RetrievedChunk]:
    """Metadata pre-filter + pgvector cosine ranking."""
    top_k = top_k or settings.RAG_TOP_K
    query_vector = embed_query(query_text)
    return _vector_search(db, query_vector, top_k, diagnosis_type=diagnosis_type)


# ---------------------------------------------------------------------------
# Grounded generation (S7 guidance)
# ---------------------------------------------------------------------------

_GUIDANCE_SYSTEM_PROMPT = """You are the coaching assistant for the Intent2Lead app.
You help managers handle a real leadership situation they are facing right now.

STRICT RULES:
- Use ONLY the knowledge-base excerpts provided by the user message. Do not use
  any other knowledge, do not invent advice, do not mention the excerpts.
- Write 3 to 4 short, practical guidance bullets the manager can act on today.
- Each bullet is one sentence, direct and specific to the situation described.
- Respond with a JSON array of strings and nothing else, e.g. ["...", "..."].
- If the excerpts are not relevant enough to give grounded advice, respond with
  exactly: NO_ANSWER"""


def _generate_guidance_bullets(situation: str, retrieved: List[RetrievedChunk]) -> Optional[List[str]]:
    """LLM rewrite of retrieved content into situation-specific bullets. None on any failure."""
    excerpts = "\n\n".join(
        f"[{i + 1}] {r.chunk.content}" for i, r in enumerate(retrieved)
    )
    user_message = (
        f"The manager's situation:\n{situation}\n\n"
        f"Knowledge-base excerpts:\n{excerpts}"
    )

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=25.0, max_retries=1)
        response = client.chat.completions.create(
            model=settings.RAG_CHAT_MODEL,
            messages=[
                {"role": "system", "content": _GUIDANCE_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=400,
            temperature=0.3,
        )
        text = (response.choices[0].message.content or "").strip()
        if not text or text == "NO_ANSWER":
            return None
        if text.startswith("```"):
            text = text.strip("`").lstrip("json").strip()
        bullets = json.loads(text)
        if (
            isinstance(bullets, list)
            and 2 <= len(bullets) <= 5
            and all(isinstance(b, str) and b.strip() for b in bullets)
        ):
            return [b.strip() for b in bullets]
        return None
    except Exception as e:
        print(f"RAG guidance generation failed: {e}")
        return None


def build_guidance_for_session(db: Session, session: CoachingSession) -> Optional[dict]:
    """
    Full S7 pipeline: retrieve -> generate. Never raises.
    Returns {"bullets", "source": "rag", "chunk_ids", "lesson_ids"} or None
    (None -> caller omits S7 guidance content).
    """
    if not is_configured():
        return None

    situation = " ".join(filter(None, [
        session.problem_detail,
        session.raw_input_text,
        f"Diagnosis: {session.diagnosis_type.value}" if session.diagnosis_type else None,
    ]))
    if not situation.strip():
        return None

    try:
        retrieved = retrieve(db, situation, diagnosis_type=session.diagnosis_type)
        print(f"RAG retrieval successful: {retrieved}")
    except EmbeddingUnavailable as e:
        print(f"RAG retrieval unavailable: {e}")
        return None
    except Exception as e:
        # pgvector extension missing, wrong column type, etc. -> safe fallback
        print(f"RAG retrieval failed: {e}")
        return None

    if not retrieved:
        return None

    bullets = _generate_guidance_bullets(situation, retrieved)
    print(f"RAG guidance generation successful: {bullets}")
    if not bullets:
        return None

    return {
        "bullets": bullets,
        "source": "rag",
        "chunk_ids": [r.chunk.id for r in retrieved],
        "lesson_ids": sorted({
            r.chunk.daily_lesson_id for r in retrieved if r.chunk.daily_lesson_id
        }),
    }


# ---------------------------------------------------------------------------
# S14: semantic lesson ranking (pgvector)
# ---------------------------------------------------------------------------

def rank_lessons_semantically(
    db: Session,
    query_text: str,
    lesson_ids: List[int],
) -> Optional[List[int]]:
    """
    Order candidate lessons by best pgvector match among their chunks.
    Returns ordered lesson ids, or None when ranking isn't possible.
    """
    if not is_configured() or not lesson_ids or not query_text:
        return None

    try:
        query_vector = embed_query(query_text)
    except EmbeddingUnavailable:
        return None

    try:
        from sqlalchemy import func

        distance = LessonChunk.embedding.cosine_distance(query_vector)
        rows = (
            db.query(
                LessonChunk.daily_lesson_id,
                func.min(distance).label("best_distance"),
            )
            .filter(
                LessonChunk.daily_lesson_id.in_(lesson_ids),
                LessonChunk.embedding.isnot(None),
            )
            .group_by(LessonChunk.daily_lesson_id)
            .order_by("best_distance")
            .all()
        )
        print(f"Rows: {rows}")
    except Exception as e:
        print(f"RAG lesson ranking failed: {e}")
        return None

    if not rows:
        return None

    return [row.daily_lesson_id for row in rows]
