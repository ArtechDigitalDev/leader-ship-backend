from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class AssessmentResultBase(BaseModel):
    clarity_score: int = Field(..., ge=5, le=25, description="Clarity category score (5-25)")
    consistency_score: int = Field(..., ge=5, le=25, description="Consistency category score (5-25)")
    connection_score: int = Field(..., ge=5, le=25, description="Connection category score (5-25)")
    courage_score: int = Field(..., ge=5, le=25, description="Courage category score (5-25)")
    curiosity_score: int = Field(..., ge=5, le=25, description="Curiosity category score (5-25)")


class AssessmentResultCreate(AssessmentResultBase):
    pass


class AssessmentResultUpdate(BaseModel):
    clarity_score: Optional[int] = Field(None, ge=5, le=25)
    consistency_score: Optional[int] = Field(None, ge=5, le=25)
    connection_score: Optional[int] = Field(None, ge=5, le=25)
    courage_score: Optional[int] = Field(None, ge=5, le=25)
    curiosity_score: Optional[int] = Field(None, ge=5, le=25)


class AssessmentResultResponse(AssessmentResultBase):
    id: int
    user_id: int
    total_score: int = Field(..., ge=25, le=125, description="Total assessment score (25-125)")
    growth_focus: str = Field(..., description="Category with lowest score (growth focus)")
    intentional_advantage: str = Field(..., description="Category with highest score (intentional advantage)")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssessmentSubmission(BaseModel):
    """Schema for submitting assessment responses"""
    responses: Dict[str, int] = Field(..., description="Question responses (1-5 scale)")
    
    @validator('responses')
    def validate_responses(cls, v):
        if not v:
            raise ValueError("Responses cannot be empty")
        
        # Check that we have exactly 25 responses (5 categories × 5 questions each)
        if len(v) != 25:
            raise ValueError("Must have exactly 25 responses")
        
        # Validate response values (1-5 scale)
        for question, response in v.items():
            if not isinstance(response, int) or response < 1 or response > 5:
                raise ValueError(f"Response for {question} must be between 1 and 5")
        
        # Validate that we have questions for all 5 categories
        categories = ['clarity', 'consistency', 'connection', 'courage', 'curiosity']
        for category in categories:
            category_questions = [q for q in v.keys() if q.startswith(category)]
            if len(category_questions) != 5:
                raise ValueError(f"Must have exactly 5 questions for {category} category")
        
        return v


class AssessmentResultSummary(BaseModel):
    """Summary view of assessment results"""
    id: int
    user_id: int
    total_score: int
    growth_focus: str
    intentional_advantage: str
    category_scores: Dict[str, int] = Field(..., description="Individual category scores")
    created_at: datetime
    
    class Config:
        from_attributes = True
