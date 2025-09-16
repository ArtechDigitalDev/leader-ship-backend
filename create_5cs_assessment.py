#!/usr/bin/env python3
"""
Script to create the ROI Leadership Journey: 5Cs Assessment in the database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app import crud
from app.schemas.assessment import AssessmentCreate, AssessmentQuestionCreate, AssessmentOptionCreate

def create_5cs_assessment():
    """Create the 5Cs assessment with all questions and options."""
    
    db = SessionLocal()
    try:
        # Check if assessment already exists
        existing_assessment = crud.assessment.get_assessment_by_title(
            db, "ROI Leadership Journey: 5Cs Assessment"
        )
        
        if existing_assessment:
            print("5Cs Assessment already exists in database.")
            return existing_assessment
        
        # Define the 5Cs questions
        questions_data = {
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
        
        # Create Likert scale options (1-5)
        likert_options = [
            AssessmentOptionCreate(
                option_text="Strongly Disagree",
                order_index=1,
                score_value=1,
                is_correct=False
            ),
            AssessmentOptionCreate(
                option_text="Disagree",
                order_index=2,
                score_value=2,
                is_correct=False
            ),
            AssessmentOptionCreate(
                option_text="Neutral",
                order_index=3,
                score_value=3,
                is_correct=False
            ),
            AssessmentOptionCreate(
                option_text="Agree",
                order_index=4,
                score_value=4,
                is_correct=False
            ),
            AssessmentOptionCreate(
                option_text="Strongly Agree",
                order_index=5,
                score_value=5,
                is_correct=False
            )
        ]
        
        # Create assessment questions
        questions = []
        question_order = 1
        
        for category, category_data in questions_data.items():
            for question_text in category_data["questions"]:
                question = AssessmentQuestionCreate(
                    question_text=question_text,
                    question_type="rating",
                    order_index=question_order,
                    is_required=True,
                    options=likert_options
                )
                questions.append(question)
                question_order += 1
        
        # Create the assessment
        assessment_data = AssessmentCreate(
            title="ROI Leadership Journey: 5Cs Assessment",
            description="A comprehensive leadership assessment measuring Clarity, Consistency, Connection, Courage, and Curiosity. Please rate each statement honestly. Your responses are confidential.",
            total_questions=25,
            estimated_time_minutes=15,
            is_active=True,
            questions=questions
        )
        
        assessment = crud.assessment.create_assessment(db, obj_in=assessment_data)
        
        print(f"Successfully created 5Cs Assessment with ID: {assessment.id}")
        print(f"Total questions created: {len(questions)}")
        
        return assessment
        
    except Exception as e:
        print(f"Error creating 5Cs assessment: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating ROI Leadership Journey: 5Cs Assessment...")
    create_5cs_assessment()
    print("Done!")
