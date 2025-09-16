from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.models.assessment import (
    Assessment, AssessmentQuestion, AssessmentOption,
    UserAssessment, UserAssessmentResponse
)
from app.schemas.assessment import (
    AssessmentCreate, AssessmentQuestionCreate, AssessmentOptionCreate,
    UserAssessmentCreate, UserAssessmentSubmit, UserAssessmentResponse as UserResponseSchema
)


# Assessment CRUD operations
def create_assessment(db: Session, *, obj_in: AssessmentCreate) -> Assessment:
    """Create a new assessment with questions and options"""
    # Create assessment
    assessment_data = obj_in.dict(exclude={'questions'})
    assessment = Assessment(**assessment_data)
    assessment.total_questions = len(obj_in.questions)
    db.add(assessment)
    db.flush()  # Get the assessment ID
    
    # Create questions and options
    for question_data in obj_in.questions:
        question_options = question_data.options
        question = AssessmentQuestion(
            assessment_id=assessment.id,
            question_text=question_data.question_text,
            question_type=question_data.question_type,
            order_index=question_data.order_index,
            is_required=question_data.is_required
        )
        db.add(question)
        db.flush()  # Get the question ID
        
        # Create options for this question
        for option_data in question_options:
            option = AssessmentOption(
                question_id=question.id,
                option_text=option_data.option_text,
                order_index=option_data.order_index,
                score_value=option_data.score_value,
                is_correct=option_data.is_correct
            )
            db.add(option)
    
    db.commit()
    db.refresh(assessment)
    return assessment


def get_assessment(db: Session, assessment_id: int) -> Optional[Assessment]:
    """Get assessment by ID with questions and options"""
    return db.query(Assessment).filter(Assessment.id == assessment_id).first()


def get_assessment_by_title(db: Session, title: str) -> Optional[Assessment]:
    """Get assessment by title"""
    return db.query(Assessment).filter(Assessment.title == title).first()


def get_active_assessments(db: Session, skip: int = 0, limit: int = 100) -> List[Assessment]:
    """Get all active assessments"""
    return db.query(Assessment).filter(Assessment.is_active == True).offset(skip).limit(limit).all()


def update_assessment(db: Session, *, db_obj: Assessment, obj_in: Dict[str, Any]) -> Assessment:
    """Update assessment"""
    for field, value in obj_in.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_assessment(db: Session, *, assessment_id: int) -> Assessment:
    """Delete assessment"""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if assessment:
        db.delete(assessment)
        db.commit()
    return assessment


# User Assessment CRUD operations
def create_user_assessment(db: Session, *, user_id: int, assessment_id: int) -> UserAssessment:
    """Start a new assessment for a user"""
    # Check if user already has an in-progress assessment
    existing = db.query(UserAssessment).filter(
        UserAssessment.user_id == user_id,
        UserAssessment.assessment_id == assessment_id,
        UserAssessment.status == "in_progress"
    ).first()
    
    if existing:
        return existing
    
    # Get assessment to calculate max possible score
    assessment = get_assessment(db, assessment_id)
    max_score = 0
    if assessment:
        for question in assessment.questions:
            max_score += max([option.score_value for option in question.options], default=0)
    
    user_assessment = UserAssessment(
        user_id=user_id,
        assessment_id=assessment_id,
        max_possible_score=max_score
    )
    db.add(user_assessment)
    db.commit()
    db.refresh(user_assessment)
    return user_assessment


def get_user_assessment(db: Session, *, user_id: int, assessment_id: int) -> Optional[UserAssessment]:
    """Get user's assessment by user ID and assessment ID"""
    return db.query(UserAssessment).filter(
        UserAssessment.user_id == user_id,
        UserAssessment.assessment_id == assessment_id
    ).first()


def get_user_assessment_by_id(db: Session, user_assessment_id: int) -> Optional[UserAssessment]:
    """Get user assessment by ID"""
    return db.query(UserAssessment).filter(UserAssessment.id == user_assessment_id).first()


def submit_user_assessment(
    db: Session, 
    *, 
    user_assessment_id: int, 
    responses: List[UserResponseSchema]
) -> UserAssessment:
    """Submit user assessment responses and calculate score"""
    user_assessment = get_user_assessment_by_id(db, user_assessment_id)
    if not user_assessment:
        raise ValueError("User assessment not found")
    
    if user_assessment.status == "completed":
        raise ValueError("Assessment already completed")
    
    total_score = 0
    
    # Process each response
    for response_data in responses:
        # Check if response already exists
        existing_response = db.query(UserAssessmentResponse).filter(
            UserAssessmentResponse.user_assessment_id == user_assessment_id,
            UserAssessmentResponse.question_id == response_data.question_id
        ).first()
        
        if existing_response:
            # Update existing response
            existing_response.selected_option_id = response_data.selected_option_id
            existing_response.text_response = response_data.text_response
            existing_response.rating_value = response_data.rating_value
            existing_response.response_time_seconds = response_data.response_time_seconds
            response = existing_response
        else:
            # Create new response
            response = UserAssessmentResponse(
                user_assessment_id=user_assessment_id,
                question_id=response_data.question_id,
                selected_option_id=response_data.selected_option_id,
                text_response=response_data.text_response,
                rating_value=response_data.rating_value,
                response_time_seconds=response_data.response_time_seconds
            )
            db.add(response)
        
        # Calculate score for this response
        if response_data.selected_option_id:
            option = db.query(AssessmentOption).filter(
                AssessmentOption.id == response_data.selected_option_id
            ).first()
            if option:
                response.score_earned = option.score_value
                total_score += option.score_value
    
    # Update user assessment
    user_assessment.total_score = total_score
    user_assessment.status = "completed"
    user_assessment.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user_assessment)
    return user_assessment


def get_user_assessment_progress(db: Session, *, user_assessment_id: int) -> Dict[str, Any]:
    """Get user assessment progress"""
    user_assessment = get_user_assessment_by_id(db, user_assessment_id)
    if not user_assessment:
        return {}
    
    # Get total questions
    assessment = get_assessment(db, user_assessment.assessment_id)
    total_questions = len(assessment.questions) if assessment else 0
    
    # Get answered questions
    answered_questions = db.query(UserAssessmentResponse).filter(
        UserAssessmentResponse.user_assessment_id == user_assessment_id
    ).count()
    
    # Calculate progress
    progress_percentage = (answered_questions / total_questions * 100) if total_questions > 0 else 0
    
    # Estimate time remaining (assuming 2 minutes per question)
    time_per_question = 2  # minutes
    remaining_questions = total_questions - answered_questions
    estimated_time_remaining = remaining_questions * time_per_question
    
    return {
        "current_question": answered_questions + 1,
        "total_questions": total_questions,
        "progress_percentage": round(progress_percentage, 2),
        "estimated_time_remaining": estimated_time_remaining,
        "status": user_assessment.status
    }


def get_user_assessment_results(db: Session, *, user_assessment_id: int) -> Dict[str, Any]:
    """Get detailed assessment results"""
    user_assessment = get_user_assessment_by_id(db, user_assessment_id)
    if not user_assessment or user_assessment.status != "completed":
        return {}
    
    # Calculate score percentage
    score_percentage = (
        (user_assessment.total_score / user_assessment.max_possible_score * 100)
        if user_assessment.max_possible_score > 0 else 0
    )
    
    # Calculate completion time
    completion_time_minutes = 0
    if user_assessment.completed_at and user_assessment.started_at:
        time_diff = user_assessment.completed_at - user_assessment.started_at
        completion_time_minutes = time_diff.total_seconds() / 60
    
    # Generate recommendations based on score
    recommendations = []
    if score_percentage >= 80:
        recommendations.append("Excellent performance! You demonstrate strong leadership potential.")
    elif score_percentage >= 60:
        recommendations.append("Good performance. Focus on areas of improvement for enhanced leadership skills.")
    else:
        recommendations.append("Consider focusing on leadership development areas to improve your skills.")
    
    return {
        "score_percentage": round(score_percentage, 2),
        "completion_time_minutes": round(completion_time_minutes, 2),
        "recommendations": recommendations,
        "total_score": user_assessment.total_score,
        "max_possible_score": user_assessment.max_possible_score
    }


def get_user_assessments(db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[UserAssessment]:
    """Get all assessments for a user"""
    return db.query(UserAssessment).filter(
        UserAssessment.user_id == user_id
    ).offset(skip).limit(limit).all()


def get_assessment_statistics(db: Session, *, assessment_id: int) -> Dict[str, Any]:
    """Get statistics for an assessment"""
    # Get total participants
    total_participants = db.query(UserAssessment).filter(
        UserAssessment.assessment_id == assessment_id
    ).count()
    
    # Get completed assessments
    completed_assessments = db.query(UserAssessment).filter(
        UserAssessment.assessment_id == assessment_id,
        UserAssessment.status == "completed"
    ).count()
    
    # Get average score
    avg_score = db.query(func.avg(UserAssessment.total_score)).filter(
        UserAssessment.assessment_id == assessment_id,
        UserAssessment.status == "completed"
    ).scalar() or 0
    
    # Get average completion time
    avg_completion_time = db.query(
        func.avg(
            func.extract('epoch', UserAssessment.completed_at - UserAssessment.started_at) / 60
        )
    ).filter(
        UserAssessment.assessment_id == assessment_id,
        UserAssessment.status == "completed",
        UserAssessment.completed_at.isnot(None)
    ).scalar() or 0
    
    return {
        "total_participants": total_participants,
        "completed_assessments": completed_assessments,
        "completion_rate": (completed_assessments / total_participants * 100) if total_participants > 0 else 0,
        "average_score": round(avg_score, 2),
        "average_completion_time_minutes": round(avg_completion_time, 2)
    }
