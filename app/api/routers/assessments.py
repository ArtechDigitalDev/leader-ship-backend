from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services import assessment_service as crud
from app.services.profile_determination_service import determine_profile
from app.api import deps
from app.schemas.assessment import (
    AssessmentCreate, AssessmentResponse, UserAssessmentCreate, UserAssessmentDetail,
    UserAssessmentSubmit, AssessmentQuestionWithProgress, AssessmentResult,
    AssessmentProgress, FiveCsQuestionsResponse, FiveCsAssessmentResult, FiveCsResponse,
    FiveCsGrowthFocus, FiveCsIntentionalAdvantage, FiveCsCategoryDetail,
    ProfileDeterminationResult
)
from app.models.user import User

router = APIRouter()

# 5Cs Assessment specific endpoints
@router.get("/5cs/questions", response_model=FiveCsQuestionsResponse)
def get_5cs_assessment_questions() -> Any:
    """
    Get the ROI Leadership Journey: 5Cs Assessment questions.
    """
    questions = {
        "title": "ROI Leadership Journey: 5Cs Assessment",
        "description": "Please rate each statement honestly. Your responses are confidential.",
        "total_questions": 25,
        "categories": {
            "clarity": {
                "name": "Clarity",
                "growth_focus": "The Anchor Seeker",
                "advantage": "Clarity",
                "questions": [
                    "I consistently prioritize the most important work over reactive tasks.",
                    "I help my team understand how their work connects to our larger goals.",
                    "I communicate a clear purpose that guides our actions.",
                    "I create space for reflection on what truly matters most.",
                    "I feel confident that I'm leading from vision—not just urgency."
                ]
            },
            "consistency": {
                "name": "Consistency",
                "growth_focus": "The Fire Cycle",
                "advantage": "Consistency",
                "questions": [
                    "I follow through on leadership habits, even when things get busy.",
                    "My team experiences stability in how I lead—day to day and week to week.",
                    "I proactively protect time for both action and recovery.",
                    "I avoid extremes (like overworking one week and withdrawing the next).",
                    "I lead in a way that is sustainable—for me and for my team."
                ]
            },
            "connection": {
                "name": "Connection",
                "growth_focus": "The Trust Void",
                "advantage": "Connection",
                "questions": [
                    "I make time to genuinely listen before offering solutions.",
                    "My team feels safe bringing me difficult news or feedback.",
                    "I give feedback that strengthens trust—not just performance.",
                    "I ask questions that invite openness, not defensiveness.",
                    "I foster a culture where real conversations happen—even when it's hard."
                ]
            },
            "courage": {
                "name": "Courage",
                "growth_focus": "The Harmony Trap",
                "advantage": "Courage",
                "questions": [
                    "I hold others accountable without fear of harming the relationship.",
                    "I respectfully challenge decisions that feel misaligned.",
                    "I take ownership when I make mistakes, even if uncomfortable.",
                    "I say no when priorities compete—even if it's unpopular.",
                    "I consistently model courageous behavior for my team to follow."
                ]
            },
            "curiosity": {
                "name": "Curiosity",
                "growth_focus": "The Fixed Frame",
                "advantage": "Curiosity",
                "questions": [
                    "I ask my team questions that unlock new ideas and perspectives.",
                    "I seek out feedback even when I know it might be hard to hear.",
                    "I create space for my team to question the status quo.",
                    "I regularly reflect on what I'm learning and how I'm growing.",
                    "I stay open and adaptive, especially during times of change."
                ]
            }
        }
    }
    return questions


@router.post("/5cs/submit", response_model=FiveCsAssessmentResult)
def submit_5cs_assessment(
    *,
    responses: FiveCsResponse,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Submit 5Cs assessment responses and get personalized results.
    Responses should be a list of 25 integers (1-5) representing Likert scale responses.
    """
    responses_list = responses.responses
    
    # Validate response values
    for i, response in enumerate(responses_list):
        if not isinstance(response, int) or response < 1 or response > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Response {i+1} must be an integer between 1 and 5"
            )
    
    # Calculate scores for each category
    category_scores = {
        "clarity": sum(responses_list[0:5]),
        "consistency": sum(responses_list[5:10]),
        "connection": sum(responses_list[10:15]),
        "courage": sum(responses_list[15:20]),
        "curiosity": sum(responses_list[20:25])
    }
    
    # Determine Intentional Advantage (highest score)
    max_score = max(category_scores.values())
    advantage_categories = [cat for cat, score in category_scores.items() if score == max_score]
    
    # Check if balanced leadership (all scores within 2-3 points)
    score_range = max_score - min(category_scores.values())
    is_balanced = score_range <= 3
    
    # Determine Growth Focus (lowest score) - but only if not balanced
    if is_balanced:
        # For balanced leaders, no specific growth focus
        growth_focus_categories = []
        growth_focus_score = None
    else:
        # For non-balanced leaders, identify the lowest scoring category
        min_score = min(category_scores.values())
        growth_focus_categories = [cat for cat, score in category_scores.items() if score == min_score]
        growth_focus_score = min_score
    
    # Get category details
    questions_data = get_5cs_assessment_questions()
    categories = questions_data["categories"]
    
    # Save results to database
    try:
        # Get or create 5Cs assessment
        assessment = crud.get_assessment_by_title(db, "ROI Leadership Journey: 5Cs Assessment")
        if not assessment:
            # Create the 5Cs assessment if it doesn't exist
            assessment_data = AssessmentCreate(
                title="ROI Leadership Journey: 5Cs Assessment",
                description="A comprehensive leadership assessment measuring Clarity, Consistency, Connection, Courage, and Curiosity.",
                total_questions=25,
                estimated_time_minutes=15,
                is_active=True,
                questions=[]  # We'll handle questions separately
            )
            assessment = crud.create_assessment(db, obj_in=assessment_data)
        
        # Create or get user assessment
        user_assessment = crud.create_user_assessment(
            db, user_id=current_user.id, assessment_id=assessment.id
        )
        
        # Save responses and mark as completed
        # This would need to be implemented in the CRUD layer
        # For now, we'll just return the results
        
    except Exception as e:
        # Log the error but don't fail the assessment
        print(f"Error saving assessment results: {e}")
    
    # Build results
    results = FiveCsAssessmentResult(
        category_scores=category_scores,
        total_score=sum(responses_list),
        max_possible_score=125,  # 25 questions * 5 points
        score_percentage=(sum(responses_list) / 125) * 100,
        is_balanced_leader=is_balanced,
        growth_focus=FiveCsGrowthFocus(
            categories=growth_focus_categories,
            score=growth_focus_score,
            details=[FiveCsCategoryDetail(**categories[cat]) for cat in growth_focus_categories] if growth_focus_categories else []
        ),
        intentional_advantage=FiveCsIntentionalAdvantage(
            categories=advantage_categories,
            score=max_score,
            details=[FiveCsCategoryDetail(**categories[cat]) for cat in advantage_categories]
        ),
        recommendations=generate_5cs_recommendations(category_scores, is_balanced)
    )
    
    return results


@router.get("/5cs/results/{user_id}")
def get_5cs_assessment_results(
    *,
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get 5Cs assessment results for a specific user (if they have completed the assessment).
    """
    # Check if user is requesting their own results or is admin
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view other users' results"
        )
    
    # Get user's 5Cs assessment results from database
    # This would need to be implemented in the CRUD layer
    # For now, return a placeholder
    return {"message": "Results retrieval not yet implemented"}


def generate_5cs_recommendations(category_scores: dict, is_balanced: bool) -> List[str]:
    """
    Generate personalized recommendations based on 5Cs scores.
    """
    recommendations = []
    
    if is_balanced:
        recommendations.append("You demonstrate balanced leadership across all 5Cs. Focus on leveraging your Intentional Advantage to mentor others.")
        recommendations.append("Consider which area you'd like to develop further for even greater impact.")
    else:
        # Growth focus recommendations
        growth_focus = min(category_scores, key=category_scores.get)
        if growth_focus == "clarity":
            recommendations.append("Focus on creating more space for strategic thinking and vision-setting.")
            recommendations.append("Practice communicating the 'why' behind decisions to your team.")
        elif growth_focus == "consistency":
            recommendations.append("Develop daily leadership habits that create stability for your team.")
            recommendations.append("Create routines that balance action and recovery.")
        elif growth_focus == "connection":
            recommendations.append("Practice active listening before offering solutions.")
            recommendations.append("Create safe spaces for difficult conversations.")
        elif growth_focus == "courage":
            recommendations.append("Practice holding others accountable with compassion.")
            recommendations.append("Model courageous behavior by admitting mistakes openly.")
        elif growth_focus == "curiosity":
            recommendations.append("Ask more open-ended questions that unlock new perspectives.")
            recommendations.append("Seek feedback regularly, especially when it might be challenging.")
        
        # Advantage recommendations
        advantage = max(category_scores, key=category_scores.get)
        if advantage == "clarity":
            recommendations.append("Leverage your clarity to help others understand their role in the bigger picture.")
        elif advantage == "consistency":
            recommendations.append("Use your consistency to create reliable systems and processes.")
        elif advantage == "connection":
            recommendations.append("Share your connection-building skills to strengthen team relationships.")
        elif advantage == "courage":
            recommendations.append("Model courageous leadership to inspire others to speak up.")
        elif advantage == "curiosity":
            recommendations.append("Use your curiosity to foster innovation and continuous learning.")
    
    return recommendations


@router.get("/", response_model=List[AssessmentResponse])
def get_assessments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve all active assessments.
    """
    assessments = crud.get_active_assessments(db, skip=skip, limit=limit)
    return assessments


@router.post("/", response_model=AssessmentResponse)
def create_assessment(
    *,
    db: Session = Depends(deps.get_db),
    assessment_in: AssessmentCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new assessment (Admin only).
    """
    assessment = crud.create_assessment(db, obj_in=assessment_in)
    return assessment


@router.get("/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
) -> Any:
    """
    Get assessment by ID.
    """
    assessment = crud.get_assessment(db, assessment_id=assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    return assessment


@router.post("/{assessment_id}/start", response_model=UserAssessmentDetail)
def start_assessment(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Start an assessment for the current user.
    """
    # Check if assessment exists
    assessment = crud.get_assessment(db, assessment_id=assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    
    if not assessment.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment is not active",
        )
    
    # Start or get existing user assessment
    user_assessment = crud.create_user_assessment(
        db, user_id=current_user.id, assessment_id=assessment_id
    )
    return user_assessment


@router.get("/{assessment_id}/question/{question_number}", response_model=AssessmentQuestionWithProgress)
def get_assessment_question(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    question_number: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get a specific question from an assessment with progress information.
    """
    # Get user assessment
    user_assessment = crud.get_user_assessment(
        db, user_id=current_user.id, assessment_id=assessment_id
    )
    if not user_assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not started. Please start the assessment first.",
        )
    
    # Get assessment
    assessment = crud.get_assessment(db, assessment_id=assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    
    # Validate question number
    if question_number < 1 or question_number > len(assessment.questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question number must be between 1 and {len(assessment.questions)}",
        )
    
    # Get the specific question
    question = assessment.questions[question_number - 1]  # Convert to 0-based index
    
    # Get progress
    progress_data = crud.get_user_assessment_progress(
        db, user_assessment_id=user_assessment.id
    )
    progress = AssessmentProgress(**progress_data)
    
    # Get user's previous response for this question (if any)
    user_response = None
    if user_assessment.responses:
        for response in user_assessment.responses:
            if response.question_id == question.id:
                user_response = response
                break
    
    return AssessmentQuestionWithProgress(
        question=question,
        progress=progress,
        user_response=user_response
    )


@router.post("/{assessment_id}/submit", response_model=AssessmentResult)
def submit_assessment(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    responses: UserAssessmentSubmit,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Submit assessment responses and get results.
    """
    # Get user assessment
    user_assessment = crud.get_user_assessment(
        db, user_id=current_user.id, assessment_id=assessment_id
    )
    if not user_assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not started. Please start the assessment first.",
        )
    
    if user_assessment.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment already completed",
        )
    
    try:
        # Submit responses
        updated_user_assessment = crud.submit_user_assessment(
            db, user_assessment_id=user_assessment.id, responses=responses.responses
        )
        
        # Get assessment
        assessment = crud.get_assessment(db, assessment_id=assessment_id)
        
        # Get results
        results_data = crud.get_user_assessment_results(
            db, user_assessment_id=user_assessment.id
        )
        
        return AssessmentResult(
            user_assessment=updated_user_assessment,
            assessment=assessment,
            score_percentage=results_data.get("score_percentage", 0),
            completion_time_minutes=results_data.get("completion_time_minutes", 0),
            recommendations=results_data.get("recommendations", [])
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{assessment_id}/progress", response_model=AssessmentProgress)
def get_assessment_progress(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current progress for an assessment.
    """
    # Get user assessment
    user_assessment = crud.get_user_assessment(
        db, user_id=current_user.id, assessment_id=assessment_id
    )
    if not user_assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not started. Please start the assessment first.",
        )
    
    progress_data = crud.get_user_assessment_progress(
        db, user_assessment_id=user_assessment.id
    )
    return AssessmentProgress(**progress_data)


@router.get("/{assessment_id}/results", response_model=AssessmentResult)
def get_assessment_results(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get assessment results (only for completed assessments).
    """
    # Get user assessment
    user_assessment = crud.get_user_assessment(
        db, user_id=current_user.id, assessment_id=assessment_id
    )
    if not user_assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    
    if user_assessment.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment not completed yet",
        )
    
    # Get assessment
    assessment = crud.get_assessment(db, assessment_id=assessment_id)
    
    # Get results
    results_data = crud.get_user_assessment_results(
        db, user_assessment_id=user_assessment.id
    )
    
    return AssessmentResult(
        user_assessment=user_assessment,
        assessment=assessment,
        score_percentage=results_data.get("score_percentage", 0),
        completion_time_minutes=results_data.get("completion_time_minutes", 0),
        recommendations=results_data.get("recommendations", [])
    )


@router.get("/user/history", response_model=List[UserAssessmentDetail])
def get_user_assessment_history(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get assessment history for the current user.
    """
    user_assessments = crud.get_user_assessments(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return user_assessments


# Admin endpoints
@router.get("/{assessment_id}/statistics")
def get_assessment_statistics(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get assessment statistics (Admin only).
    """
    # Check if assessment exists
    assessment = crud.get_assessment(db, assessment_id=assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    
    statistics = crud.get_assessment_statistics(db, assessment_id=assessment_id)
    return statistics


@router.delete("/{assessment_id}")
def delete_assessment(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete assessment (Admin only).
    """
    assessment = crud.delete_assessment(db, assessment_id=assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    return {"message": "Assessment deleted successfully"}


@router.post("/5cs/profile-determination", response_model=ProfileDeterminationResult)
def get_profile_determination(
    *,
    responses: FiveCsResponse,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get detailed leadership profile determination based on 5Cs assessment responses.
    This endpoint provides the complete profile information including strengths, 
    areas for development, learning tracks, and detailed content summaries.
    """
    responses_list = responses.responses
    
    # Validate response values
    for i, response in enumerate(responses_list):
        if not isinstance(response, int) or response < 1 or response > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Response {i+1} must be an integer between 1 and 5"
            )
    
    # Calculate scores for each category
    category_scores = {
        "clarity": sum(responses_list[0:5]),
        "consistency": sum(responses_list[5:10]),
        "connection": sum(responses_list[10:15]),
        "courage": sum(responses_list[15:20]),
        "curiosity": sum(responses_list[20:25])
    }
    
    # Check if balanced leadership (all scores within 2-3 points)
    score_range = max(category_scores.values()) - min(category_scores.values())
    is_balanced = score_range <= 3
    
    # Determine profile using the profile determination service
    profile_result = determine_profile(category_scores, is_balanced)
    
    return profile_result


@router.post("/5cs/complete-profile", response_model=dict)
def get_complete_profile_assessment(
    *,
    responses: FiveCsResponse,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get complete assessment results including both traditional 5Cs results and detailed profile determination.
    This endpoint combines the assessment results with the comprehensive leadership profile.
    """
    responses_list = responses.responses
    
    # Validate response values
    for i, response in enumerate(responses_list):
        if not isinstance(response, int) or response < 1 or response > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Response {i+1} must be an integer between 1 and 5"
            )
    
    # Calculate scores for each category
    category_scores = {
        "clarity": sum(responses_list[0:5]),
        "consistency": sum(responses_list[5:10]),
        "connection": sum(responses_list[10:15]),
        "courage": sum(responses_list[15:20]),
        "curiosity": sum(responses_list[20:25])
    }
    
    # Check if balanced leadership (all scores within 2-3 points)
    score_range = max(category_scores.values()) - min(category_scores.values())
    is_balanced = score_range <= 3
    
    # Get traditional 5Cs results
    max_score = max(category_scores.values())
    advantage_categories = [cat for cat, score in category_scores.items() if score == max_score]
    
    if is_balanced:
        growth_focus_categories = []
        growth_focus_score = None
    else:
        min_score = min(category_scores.values())
        growth_focus_categories = [cat for cat, score in category_scores.items() if score == min_score]
        growth_focus_score = min_score
    
    # Get category details
    questions_data = get_5cs_assessment_questions()
    categories = questions_data["categories"]
    
    # Build traditional results
    traditional_results = FiveCsAssessmentResult(
        category_scores=category_scores,
        total_score=sum(responses_list),
        max_possible_score=125,
        score_percentage=(sum(responses_list) / 125) * 100,
        is_balanced_leader=is_balanced,
        growth_focus=FiveCsGrowthFocus(
            categories=growth_focus_categories,
            score=growth_focus_score,
            details=[FiveCsCategoryDetail(**categories[cat]) for cat in growth_focus_categories] if growth_focus_categories else []
        ),
        intentional_advantage=FiveCsIntentionalAdvantage(
            categories=advantage_categories,
            score=max_score,
            details=[FiveCsCategoryDetail(**categories[cat]) for cat in advantage_categories]
        ),
        recommendations=generate_5cs_recommendations(category_scores, is_balanced)
    )
    
    # Get detailed profile determination
    profile_result = determine_profile(category_scores, is_balanced)
    
    return {
        "assessment_results": traditional_results,
        "profile_determination": profile_result
    }
