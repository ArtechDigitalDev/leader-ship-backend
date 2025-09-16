from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base
from app.models.item import Item


class UserRole(str, enum.Enum):
    PARTICIPANT = "participant"
    COACH = "coach"
    ADMIN = "admin"


class RoleRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    mobile_number = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.PARTICIPANT, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)  # Keep for backward compatibility
    is_email_verified = Column(Boolean, default=False)
    terms_accepted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Role request fields
    requested_role = Column(Enum(UserRole), nullable=True)
    role_request_status = Column(Enum(RoleRequestStatus), nullable=True)
    role_request_reason = Column(Text, nullable=True)
    role_requested_at = Column(DateTime(timezone=True), nullable=True)
    role_approved_by = Column(Integer, nullable=True)  # Admin user ID who approved
    role_approved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    items = relationship("Item", back_populates="owner")
    # assessments = relationship("UserAssessment", back_populates="user", lazy="dynamic")
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN or self.is_superuser
    
    def is_coach(self) -> bool:
        """Check if user is coach"""
        return self.role == UserRole.COACH
    
    def is_participant(self) -> bool:
        """Check if user is participant"""
        return self.role == UserRole.PARTICIPANT
    
    def has_pending_role_request(self) -> bool:
        """Check if user has a pending role request"""
        return (
            self.requested_role is not None and 
            self.role_request_status == RoleRequestStatus.PENDING
        )
