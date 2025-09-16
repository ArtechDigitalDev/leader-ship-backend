from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    total_questions = Column(Integer, default=0)
    estimated_time_minutes = Column(Integer, default=10)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    questions = relationship("AssessmentQuestion", back_populates="assessment")
    user_assessments = relationship("UserAssessment", back_populates="assessment")


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, default="multiple_choice")  # multiple_choice, text, rating
    order_index = Column(Integer, nullable=False)
    is_required = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    assessment = relationship("Assessment", back_populates="questions")
    options = relationship("AssessmentOption", back_populates="question", order_by="AssessmentOption.order_index")
    user_responses = relationship("UserAssessmentResponse", back_populates="question")


class AssessmentOption(Base):
    __tablename__ = "assessment_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("assessment_questions.id"), nullable=False)
    option_text = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False)
    score_value = Column(Integer, default=0)  # For scoring calculations
    is_correct = Column(Boolean, default=False)  # For knowledge-based assessments
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    question = relationship("AssessmentQuestion", back_populates="options")
    user_responses = relationship("UserAssessmentResponse", back_populates="selected_option")


class UserAssessment(Base):
    __tablename__ = "user_assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    status = Column(String, default="in_progress")  # in_progress, completed, abandoned
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    total_score = Column(Integer, default=0)
    max_possible_score = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="assessments")
    assessment = relationship("Assessment", back_populates="user_assessments")
    responses = relationship("UserAssessmentResponse", back_populates="user_assessment")


class UserAssessmentResponse(Base):
    __tablename__ = "user_assessment_responses"

    id = Column(Integer, primary_key=True, index=True)
    user_assessment_id = Column(Integer, ForeignKey("user_assessments.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("assessment_questions.id"), nullable=False)
    selected_option_id = Column(Integer, ForeignKey("assessment_options.id"))
    text_response = Column(Text)  # For text-based questions
    rating_value = Column(Integer)  # For rating questions
    score_earned = Column(Integer, default=0)
    response_time_seconds = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user_assessment = relationship("UserAssessment", back_populates="responses")
    question = relationship("AssessmentQuestion", back_populates="user_responses")
    selected_option = relationship("AssessmentOption", back_populates="user_responses")
