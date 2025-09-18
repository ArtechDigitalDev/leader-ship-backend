from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class DailyLesson(Base):
    __tablename__ = "daily_lessons"

    id = Column(Integer, primary_key=True, index=True)
    week_id = Column(Integer, ForeignKey("weeks.id"), nullable=False)
    day_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    daily_tip = Column(JSON, nullable=False)  # {whenToUse: str, topTakeaway: str}
    swipe_cards = Column(JSON, nullable=False)  # Array of {title: str, content: str|str[]}
    scenario = Column(JSON, nullable=False)  # {story: str, choices: [], correct: str, explanation: str}
    go_deeper = Column(JSON, nullable=False)  # Array of {type: str, title: str, description?: str, link?: str}
    reflection_prompt = Column(Text, nullable=False)
    leader_win = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with Week
    week = relationship("Week", back_populates="daily_lessons")
