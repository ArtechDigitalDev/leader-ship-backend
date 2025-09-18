from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


class DailyTip(BaseModel):
    when_to_use: str
    top_takeaway: str


class SwipeCard(BaseModel):
    title: str = Field(..., pattern="^(The Trap|The Shift|The Tool|The Reminder)$")
    content: Union[str, List[str]]


class Choice(BaseModel):
    label: str
    text: str
    correct: Optional[bool] = None


class Scenario(BaseModel):
    story: str
    choices: List[Choice]
    correct: str
    explanation: str


class GoDeeper(BaseModel):
    type: str = Field(..., pattern="^(article|book|podcast|video)$")
    title: str
    description: Optional[str] = None
    link: Optional[str] = None


class DailyLessonBase(BaseModel):
    week_id: int
    day_number: int
    title: str
    daily_tip: DailyTip
    swipe_cards: List[SwipeCard]
    scenario: Scenario
    go_deeper: List[GoDeeper]
    reflection_prompt: str
    leader_win: str


class DailyLessonCreate(DailyLessonBase):
    pass


class DailyLessonUpdate(BaseModel):
    week_id: Optional[int] = None
    day_number: Optional[int] = None
    title: Optional[str] = None
    daily_tip: Optional[DailyTip] = None
    swipe_cards: Optional[List[SwipeCard]] = None
    scenario: Optional[Scenario] = None
    go_deeper: Optional[List[GoDeeper]] = None
    reflection_prompt: Optional[str] = None
    leader_win: Optional[str] = None


class DailyLessonResponse(DailyLessonBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
