"""
Backfill the RAG search index: chunk + embed every daily lesson.

Requires OPENAI_API_KEY in the environment (.env).
Safe to re-run — each lesson's old chunks are replaced.

Usage: venv\\Scripts\\python.exe scripts\\ingest_lesson_chunks.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import joinedload

from app.core.database import SessionLocal
from app.models.daily_lesson import DailyLesson
from app.services import rag_service
from app.services.embedding_service import EmbeddingUnavailable, is_configured


def main() -> int:
    if not is_configured():
        print("ERROR: OPENAI_API_KEY is not configured (.env). Aborting.")
        return 1

    db = SessionLocal()
    try:
        lessons = (
            db.query(DailyLesson)
            .options(joinedload(DailyLesson.week))
            .order_by(DailyLesson.id)
            .all()
        )
        print(f"Found {len(lessons)} lessons to index.\n")

        total_chunks = 0
        failures = 0
        for lesson in lessons:
            try:
                count = rag_service.ingest_lesson(db, lesson)
                total_chunks += count
                print(f"  lesson {lesson.id:>4} ({lesson.title[:50]}): {count} chunks")
            except EmbeddingUnavailable as e:
                print(f"  lesson {lesson.id:>4}: FAILED — {e}")
                failures += 1
                db.rollback()

        print(f"\nDone. {total_chunks} chunks indexed, {failures} failures.")
        return 0 if failures == 0 else 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
