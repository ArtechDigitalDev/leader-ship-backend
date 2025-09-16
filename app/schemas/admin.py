from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.user import User


# Admin Panel Schemas
class UserStats(BaseModel):
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    pending_users: int = Field(..., description="Number of pending users")
    inactive_users: int = Field(..., description="Number of inactive users")


class UserWithTrack(User):
    """User with learning track information"""
    learning_track: Optional[str] = Field(None, description="User's current learning track")
    assessment_count: int = Field(0, description="Number of assessments completed")
    last_assessment_date: Optional[datetime] = Field(None, description="Date of last assessment")


class UserListResponse(BaseModel):
    users: List[UserWithTrack] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of users per page")
    total_pages: int = Field(..., description="Total number of pages")


class UserSearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query")
    status: Optional[str] = Field(None, description="Filter by status (active, inactive, pending)")
    learning_track: Optional[str] = Field(None, description="Filter by learning track")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(10, ge=1, le=100, description="Users per page")


class AdminUserCreate(BaseModel):
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    full_name: str = Field(..., description="Full name")
    mobile_number: str = Field(..., description="Mobile number")
    password: str = Field(..., description="Password")
    is_active: bool = Field(True, description="Is user active")
    is_superuser: bool = Field(False, description="Is user superuser")
    learning_track: Optional[str] = Field(None, description="Learning track")


class AdminUserUpdate(BaseModel):
    email: Optional[str] = Field(None, description="User email")
    username: Optional[str] = Field(None, description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    mobile_number: Optional[str] = Field(None, description="Mobile number")
    is_active: Optional[bool] = Field(None, description="Is user active")
    is_superuser: Optional[bool] = Field(None, description="Is user superuser")
    learning_track: Optional[str] = Field(None, description="Learning track")


class UserExportRequest(BaseModel):
    format: str = Field("csv", description="Export format (csv, json)")
    include_inactive: bool = Field(False, description="Include inactive users")
    include_assessments: bool = Field(True, description="Include assessment data")


class AssessmentStats(BaseModel):
    total_assessments: int = Field(..., description="Total assessments completed")
    completed_assessments: int = Field(..., description="Completed assessments")
    average_score: float = Field(..., description="Average assessment score")
    most_common_profile: str = Field(..., description="Most common leadership profile")


class AdminDashboardStats(BaseModel):
    user_stats: UserStats = Field(..., description="User statistics")
    assessment_stats: AssessmentStats = Field(..., description="Assessment statistics")
    recent_users: List[UserWithTrack] = Field(..., description="Recently registered users")
    top_performing_users: List[UserWithTrack] = Field(..., description="Top performing users")


class BulkUserAction(BaseModel):
    user_ids: List[int] = Field(..., description="List of user IDs")
    action: str = Field(..., description="Action to perform (activate, deactivate, delete)")
