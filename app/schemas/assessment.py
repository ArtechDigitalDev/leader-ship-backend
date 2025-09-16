from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# Base schemas
class AssessmentOptionBase(BaseModel):
    option_text: str = Field(..., description="The text of the option")
    order_index: int = Field(..., description="Order of the option")
    score_value: int = Field(default=0, description="Score value for this option")
    is_correct: bool = Field(default=False, description="Whether this is the correct answer")


class AssessmentQuestionBase(BaseModel):
    question_text: str = Field(..., description="The question text")
    question_type: str = Field(default="multiple_choice", description="Type of question")
    order_index: int = Field(..., description="Order of the question")
    is_required: bool = Field(default=True, description="Whether this question is required")


class AssessmentBase(BaseModel):
    title: str = Field(..., description="Assessment title")
    description: Optional[str] = Field(None, description="Assessment description")
    is_active: bool = Field(default=True, description="Whether the assessment is active")
    total_questions: int = Field(default=0, description="Total number of questions")
    estimated_time_minutes: int = Field(default=10, description="Estimated time to complete")


# Create schemas
class AssessmentOptionCreate(AssessmentOptionBase):
    pass


class AssessmentQuestionCreate(AssessmentQuestionBase):
    options: List[AssessmentOptionCreate] = Field(default=[], description="Question options")


class AssessmentCreate(AssessmentBase):
    questions: List[AssessmentQuestionCreate] = Field(default=[], description="Assessment questions")


# Response schemas
class AssessmentOptionResponse(AssessmentOptionBase):
    id: int
    question_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssessmentQuestionResponse(AssessmentQuestionBase):
    id: int
    assessment_id: int
    options: List[AssessmentOptionResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssessmentResponse(AssessmentBase):
    id: int
    questions: List[AssessmentQuestionResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# User Assessment schemas
class UserAssessmentBase(BaseModel):
    assessment_id: int = Field(..., description="ID of the assessment")
    status: str = Field(default="in_progress", description="Assessment status")


class UserAssessmentCreate(UserAssessmentBase):
    pass


class UserAssessmentResponse(BaseModel):
    question_id: int = Field(..., description="ID of the question")
    selected_option_id: Optional[int] = Field(None, description="ID of selected option")
    text_response: Optional[str] = Field(None, description="Text response for text questions")
    rating_value: Optional[int] = Field(None, description="Rating value for rating questions")
    response_time_seconds: Optional[int] = Field(None, description="Time taken to respond")


class UserAssessmentSubmit(BaseModel):
    responses: List[UserAssessmentResponse] = Field(..., description="User responses")


class UserAssessmentResponseDetail(UserAssessmentResponse):
    id: int
    user_assessment_id: int
    score_earned: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserAssessmentDetail(UserAssessmentBase):
    id: int
    user_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_score: int
    max_possible_score: int
    responses: List[UserAssessmentResponseDetail] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Assessment progress schemas
class AssessmentProgress(BaseModel):
    current_question: int = Field(..., description="Current question number")
    total_questions: int = Field(..., description="Total questions in assessment")
    progress_percentage: float = Field(..., description="Progress percentage")
    estimated_time_remaining: int = Field(..., description="Estimated time remaining in minutes")
    status: str = Field(..., description="Assessment status")


class AssessmentQuestionWithProgress(BaseModel):
    question: AssessmentQuestionResponse
    progress: AssessmentProgress
    user_response: Optional[UserAssessmentResponseDetail] = None


# Assessment results schemas
class AssessmentResult(BaseModel):
    user_assessment: UserAssessmentDetail
    assessment: AssessmentResponse
    score_percentage: float = Field(..., description="Score as percentage")
    completion_time_minutes: float = Field(..., description="Time taken to complete")
    recommendations: List[str] = Field(default=[], description="Recommendations based on results")


# 5Cs Assessment specific schemas
class FiveCsCategoryDetail(BaseModel):
    name: str = Field(..., description="Category name")
    growth_focus: str = Field(..., description="Growth focus title")
    advantage: str = Field(..., description="Advantage title")
    questions: List[str] = Field(..., description="List of questions for this category")


class FiveCsQuestionsResponse(BaseModel):
    title: str = Field(..., description="Assessment title")
    description: str = Field(..., description="Assessment description")
    total_questions: int = Field(..., description="Total number of questions")
    categories: dict = Field(..., description="Categories with their questions and metadata")


class FiveCsGrowthFocus(BaseModel):
    categories: List[str] = Field(..., description="Categories with lowest scores")
    score: Optional[int] = Field(None, description="Score for growth focus categories (None for balanced leaders)")
    details: List[FiveCsCategoryDetail] = Field(..., description="Category details")


class FiveCsIntentionalAdvantage(BaseModel):
    categories: List[str] = Field(..., description="Categories with highest scores")
    score: int = Field(..., description="Score for advantage categories")
    details: List[FiveCsCategoryDetail] = Field(..., description="Category details")


class FiveCsAssessmentResult(BaseModel):
    category_scores: dict = Field(..., description="Scores for each category")
    total_score: int = Field(..., description="Total assessment score")
    max_possible_score: int = Field(..., description="Maximum possible score")
    score_percentage: float = Field(..., description="Score as percentage")
    is_balanced_leader: bool = Field(..., description="Whether user is a balanced leader")
    growth_focus: FiveCsGrowthFocus = Field(..., description="Growth focus information")
    intentional_advantage: FiveCsIntentionalAdvantage = Field(..., description="Intentional advantage information")
    recommendations: List[str] = Field(..., description="Personalized recommendations")


class FiveCsResponse(BaseModel):
    responses: List[int] = Field(..., description="List of 25 responses (1-5 scale)", min_items=25, max_items=25)


# Enhanced Profile Determination schemas
class ProfileDeterminationContent(BaseModel):
    growth_focus_summary: str = Field(..., description="Summary of growth focus area")
    intentional_advantage_summary: str = Field(..., description="Summary of intentional advantage area")


class LearningTrack(BaseModel):
    title: str = Field(..., description="Learning track title")
    description: str = Field(..., description="Learning track description")
    is_recommended: bool = Field(default=False, description="Whether this track is recommended")


class LeadershipProfile(BaseModel):
    primary_type: str = Field(..., description="Primary leadership type (e.g., 'COLLABORATIVE LEADER')")
    description: str = Field(..., description="Description of the leadership type")
    strengths: List[str] = Field(..., description="List of current strengths")
    areas_for_development: List[str] = Field(..., description="List of areas for development")
    learning_tracks: List[LearningTrack] = Field(..., description="Available learning tracks")
    profile_content: ProfileDeterminationContent = Field(..., description="Detailed profile content")


class ProfileDeterminationResult(BaseModel):
    leadership_profile: LeadershipProfile = Field(..., description="Complete leadership profile")
    category_scores: dict = Field(..., description="Scores for each category")
    growth_focus: str = Field(..., description="Growth focus category")
    intentional_advantage: str = Field(..., description="Intentional advantage category")
    is_balanced_leader: bool = Field(..., description="Whether user is a balanced leader")
