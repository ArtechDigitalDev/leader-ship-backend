from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.core.config import settings
from app.core.database import Base


class LessonChunk(Base):
    """
    RAG search index — small text pieces extracted from knowledge-base content,
    each with an embedding vector (BRD v2 Section 2.2).

    daily_lessons remains the source of truth that users read; chunks exist
    only for retrieval. Embeddings are stored as pgvector VECTOR columns and
    ranked with cosine distance in SQL (Neon PostgreSQL + pgvector extension).
    """
    __tablename__ = "lesson_chunks"

    id = Column(Integer, primary_key=True, index=True)
    daily_lesson_id = Column(Integer, ForeignKey("daily_lessons.id"), nullable=True, index=True)

    source_type = Column(String(30), nullable=False, default="lesson")
    chunk_type = Column(String(30), nullable=False)
    content = Column(Text, nullable=False)

    embedding = Column(Vector(settings.EMBEDDING_DIMENSIONS), nullable=True)
    chunk_metadata = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    daily_lesson = relationship("DailyLesson", back_populates="chunks")

    def __repr__(self):
        return f"<LessonChunk(id={self.id}, lesson_id={self.daily_lesson_id}, type={self.chunk_type})>"
