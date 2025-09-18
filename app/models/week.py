from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Week(Base):
    __tablename__ = "weeks"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)  # Five categories: Clarity, Consistency, Connection, Courage, Curiosity
    week_number = Column(Integer, nullable=False)  # 1 to 7
    title = Column(String, nullable=False)
    intro = Column(Text, nullable=False)
    weekly_challenge = Column(JSON, nullable=True)  # JSON structure for challenge details
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with DailyLesson
    daily_lessons = relationship("DailyLesson", back_populates="week")
