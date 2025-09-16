from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re
from datetime import datetime
from app.models.user import UserRole, RoleRequestStatus


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    mobile_number: Optional[str] = None
    role: Optional[UserRole] = UserRole.PARTICIPANT
    is_active: Optional[bool] = True
    is_superuser: bool = False
    is_email_verified: Optional[bool] = False


class UserCreate(UserBase):
    email: EmailStr
    username: str
    full_name: str = Field(..., min_length=1, description="Your full name")
    mobile_number: str = Field(..., description="Mobile number (e.g., 1234567890)")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    role: UserRole = Field(UserRole.PARTICIPANT, description="User role")
    terms_accepted: bool = Field(..., description="Must accept terms and conditions")
    
    @validator('mobile_number')
    def validate_mobile_number(cls, v):
        # Remove any non-digit characters
        digits_only = re.sub(r'\D', '', v)
        if len(digits_only) < 10:
            raise ValueError('Mobile number must have at least 10 digits')
        return digits_only
    
    @validator('terms_accepted')
    def validate_terms_accepted(cls, v):
        if not v:
            raise ValueError('You must accept the Terms of Service and Privacy Policy')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        # Only allow participants to sign up directly
        if v != UserRole.PARTICIPANT:
            raise ValueError('Only participants can sign up directly. Coaches and admins must be invited or request approval.')
        return v


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: Optional[int] = None

    model_config = {
        "from_attributes": True
    }


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str


class UserSignUpResponse(BaseModel):
    message: str
    user: User
    access_token: str
    token_type: str = "bearer"


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Your email address")
    password: str = Field(..., description="Your password")
    role: Optional[UserRole] = Field(None, description="Expected user role for validation")


class UserLoginResponse(BaseModel):
    message: str
    user: User
    access_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to reset password for")


class PasswordReset(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")


class EmailVerification(BaseModel):
    token: str = Field(..., description="Email verification token")


class RoleRequest(BaseModel):
    requested_role: UserRole = Field(..., description="Role being requested")
    reason: str = Field(..., min_length=10, description="Reason for role request (minimum 10 characters)")


class RoleRequestResponse(BaseModel):
    message: str
    requested_role: UserRole
    status: RoleRequestStatus
    reason: str
    requested_at: datetime


class AdminUserCreate(BaseModel):
    """Admin-only user creation (bypasses role restrictions)"""
    email: EmailStr
    username: str
    full_name: str = Field(..., min_length=1, description="Full name")
    mobile_number: str = Field(..., description="Mobile number (e.g., 1234567890)")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(True, description="Is user active")
    is_email_verified: bool = Field(True, description="Skip email verification for admin-created users")
    
    @validator('mobile_number')
    def validate_mobile_number(cls, v):
        # Remove any non-digit characters
        digits_only = re.sub(r'\D', '', v)
        if len(digits_only) < 10:
            raise ValueError('Mobile number must have at least 10 digits')
        return digits_only


class UserInvitation(BaseModel):
    """Invite a user to join as coach or admin"""
    email: EmailStr = Field(..., description="Email to invite")
    full_name: str = Field(..., description="Full name")
    role: UserRole = Field(..., description="Role to invite as")
    message: Optional[str] = Field(None, description="Optional invitation message")
    
    @validator('role')
    def validate_invitation_role(cls, v):
        if v == UserRole.PARTICIPANT:
            raise ValueError('Participants can sign up directly. Only invite coaches and admins.')
        return v
