#!/usr/bin/env python3
"""
Script to create a sample leadership assessment for testing purposes.
"""

from app.core.database import SessionLocal
from app.crud.assessment import create_assessment
from app.schemas.assessment import (
    AssessmentCreate, AssessmentQuestionCreate, AssessmentOptionCreate
)

def create_leadership_assessment():
    """Create a sample leadership assessment with questions and options."""
    
    # Sample leadership assessment data
    assessment_data = AssessmentCreate(
        title="Leadership Assessment",
        description="Answer the questions to assess your leadership potential.",
        is_active=True,
        total_questions=5,
        estimated_time_minutes=10,
        questions=[
            AssessmentQuestionCreate(
                question_text="What is your primary motivation for seeking a leadership role?",
                question_type="multiple_choice",
                order_index=1,
                is_required=True,
                options=[
                    AssessmentOptionCreate(
                        option_text="To gain more authority and control",
                        order_index=1,
                        score_value=1
                    ),
                    AssessmentOptionCreate(
                        option_text="To help others grow and achieve their potential",
                        order_index=2,
                        score_value=5
                    ),
                    AssessmentOptionCreate(
                        option_text="To earn a higher salary and recognition",
                        order_index=3,
                        score_value=2
                    ),
                    AssessmentOptionCreate(
                        option_text="To implement my own vision without much input",
                        order_index=4,
                        score_value=3
                    )
                ]
            ),
            AssessmentQuestionCreate(
                question_text="How do you typically handle conflicts within your team?",
                question_type="multiple_choice",
                order_index=2,
                is_required=True,
                options=[
                    AssessmentOptionCreate(
                        option_text="Avoid the conflict and hope it resolves itself",
                        order_index=1,
                        score_value=1
                    ),
                    AssessmentOptionCreate(
                        option_text="Address it immediately and directly with all parties",
                        order_index=2,
                        score_value=4
                    ),
                    AssessmentOptionCreate(
                        option_text="Let team members work it out among themselves",
                        order_index=3,
                        score_value=2
                    ),
                    AssessmentOptionCreate(
                        option_text="Bring in HR or management to handle it",
                        order_index=4,
                        score_value=3
                    )
                ]
            ),
            AssessmentQuestionCreate(
                question_text="When making important decisions, you prefer to:",
                question_type="multiple_choice",
                order_index=3,
                is_required=True,
                options=[
                    AssessmentOptionCreate(
                        option_text="Make the decision quickly and move forward",
                        order_index=1,
                        score_value=2
                    ),
                    AssessmentOptionCreate(
                        option_text="Gather input from team members before deciding",
                        order_index=2,
                        score_value=5
                    ),
                    AssessmentOptionCreate(
                        option_text="Analyze all possible outcomes thoroughly",
                        order_index=3,
                        score_value=4
                    ),
                    AssessmentOptionCreate(
                        option_text="Follow established procedures and guidelines",
                        order_index=4,
                        score_value=3
                    )
                ]
            ),
            AssessmentQuestionCreate(
                question_text="How do you measure success as a leader?",
                question_type="multiple_choice",
                order_index=4,
                is_required=True,
                options=[
                    AssessmentOptionCreate(
                        option_text="Meeting or exceeding targets and goals",
                        order_index=1,
                        score_value=4
                    ),
                    AssessmentOptionCreate(
                        option_text="Team satisfaction and retention rates",
                        order_index=2,
                        score_value=5
                    ),
                    AssessmentOptionCreate(
                        option_text="Personal recognition and advancement",
                        order_index=3,
                        score_value=2
                    ),
                    AssessmentOptionCreate(
                        option_text="Efficiency and cost savings",
                        order_index=4,
                        score_value=3
                    )
                ]
            ),
            AssessmentQuestionCreate(
                question_text="What is your approach to developing your team members?",
                question_type="multiple_choice",
                order_index=5,
                is_required=True,
                options=[
                    AssessmentOptionCreate(
                        option_text="Focus on their current role performance",
                        order_index=1,
                        score_value=2
                    ),
                    AssessmentOptionCreate(
                        option_text="Help them identify and work toward career goals",
                        order_index=2,
                        score_value=5
                    ),
                    AssessmentOptionCreate(
                        option_text="Provide training only when necessary",
                        order_index=3,
                        score_value=3
                    ),
                    AssessmentOptionCreate(
                        option_text="Let them take responsibility for their own development",
                        order_index=4,
                        score_value=4
                    )
                ]
            )
        ]
    )
    
    db = SessionLocal()
    try:
        # Create the assessment
        assessment = create_assessment(db, obj_in=assessment_data)
        print(f"✅ Leadership Assessment created successfully!")
        print(f"   ID: {assessment.id}")
        print(f"   Title: {assessment.title}")
        print(f"   Questions: {len(assessment.questions)}")
        print(f"   Total Options: {sum(len(q.options) for q in assessment.questions)}")
        
        return assessment.id
        
    except Exception as e:
        print(f"❌ Error creating assessment: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating sample leadership assessment...")
    assessment_id = create_leadership_assessment()
    if assessment_id:
        print(f"\n🎉 Assessment created with ID: {assessment_id}")
        print("You can now test the assessment endpoints!")
    else:
        print("\n❌ Failed to create assessment")
