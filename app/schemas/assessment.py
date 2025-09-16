from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# Simple Assessment Schema
class AssessmentBase(BaseModel):
    category: str = Field(..., description="Assessment category")
    question: str = Field(..., description="Assessment question")
    is_active: bool = Field(default=True, description="Whether the assessment is active")


class AssessmentCreate(AssessmentBase):
    pass


class AssessmentUpdate(BaseModel):
    category: Optional[str] = Field(None, description="Assessment category")
    question: Optional[str] = Field(None, description="Assessment question")
    is_active: Optional[bool] = Field(None, description="Whether the assessment is active")


class AssessmentResponse(AssessmentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True