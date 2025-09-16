from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import csv
import io
import json
from datetime import timedelta

from app.services import admin_service
from app.api import deps
from app.core import security
from app.schemas.admin import (
    UserStats, UserWithTrack, UserListResponse, UserSearchRequest,
    AdminUserCreate, AdminUserUpdate, AdminDashboardStats, 
    UserExportRequest, BulkUserAction
)
from app.schemas.user import UserInvitation, RoleRequestResponse
from app.models.user import UserRole, RoleRequestStatus
from app.models.user import User

router = APIRouter()


def require_admin(current_user: User = Depends(deps.get_current_user)) -> User:
    """Require admin privileges"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.get("/dashboard", response_model=AdminDashboardStats)
def get_admin_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """
    Get admin dashboard statistics and overview data.
    """
    return admin_service.get_admin_dashboard_stats(db)


@router.get("/users/stats", response_model=UserStats)
def get_user_statistics(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """
    Get user statistics for the admin panel.
    """
    return admin_service.get_user_stats(db)


@router.get("/users", response_model=UserListResponse)
def get_users(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
    query: str = Query(None, description="Search query"),
    status: str = Query(None, description="Filter by status (active, inactive, pending)"),
    learning_track: str = Query(None, description="Filter by learning track"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Users per page"),
) -> Any:
    """
    Get list of users with search and filter capabilities.
    """
    search_request = UserSearchRequest(
        query=query,
        status=status,
        learning_track=learning_track,
        page=page,
        per_page=per_page
    )
    
    users, total = admin_service.get_users_with_tracks(db, search_request)
    total_pages = (total + per_page - 1) // per_page
    
    return UserListResponse(
        users=users,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.post("/users", response_model=UserWithTrack)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
    user_data: AdminUserCreate,
) -> Any:
    """
    Create a new user (Admin only).
    """
    try:
        user = admin_service.create_admin_user(db, user_data)
        
        # Convert to UserWithTrack
        return UserWithTrack(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            mobile_number=user.mobile_number,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            learning_track=None,
            assessment_count=0,
            last_assessment_date=None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users/{user_id}", response_model=UserWithTrack)
def get_user(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
    user_id: int,
) -> Any:
    """
    Get user details by ID (Admin only).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get assessment data
    from app.models.assessment import UserAssessment
    assessment_count = db.query(UserAssessment).filter(
        UserAssessment.user_id == user.id,
        UserAssessment.status == "completed"
    ).count()
    
    last_assessment = db.query(UserAssessment).filter(
        UserAssessment.user_id == user.id,
        UserAssessment.status == "completed"
    ).order_by(UserAssessment.completed_at.desc()).first()
    
    learning_track = "Strategic Vision" if assessment_count > 0 else None
    
    return UserWithTrack(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        mobile_number=user.mobile_number,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        learning_track=learning_track,
        assessment_count=assessment_count,
        last_assessment_date=last_assessment.completed_at if last_assessment else None
    )


@router.put("/users/{user_id}", response_model=UserWithTrack)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
    user_id: int,
    user_data: AdminUserUpdate,
) -> Any:
    """
    Update user by ID (Admin only).
    """
    user = admin_service.update_admin_user(db, user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get assessment data
    from app.models.assessment import UserAssessment
    assessment_count = db.query(UserAssessment).filter(
        UserAssessment.user_id == user.id,
        UserAssessment.status == "completed"
    ).count()
    
    learning_track = "Strategic Vision" if assessment_count > 0 else None
    
    return UserWithTrack(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        mobile_number=user.mobile_number,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        learning_track=learning_track,
        assessment_count=assessment_count,
        last_assessment_date=None
    )


@router.delete("/users/{user_id}")
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
    user_id: int,
) -> Any:
    """
    Delete user by ID (Admin only).
    """
    success = admin_service.delete_admin_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}


@router.post("/users/export")
def export_users(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
    export_request: UserExportRequest,
) -> Any:
    """
    Export users data (Admin only).
    """
    # Get all users
    query = db.query(User)
    if not export_request.include_inactive:
        query = query.filter(User.is_active == True)
    
    users = query.all()
    
    if export_request.format == "csv":
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = ["ID", "Email", "Username", "Full Name", "Mobile Number", "Active", "Superuser", "Created At"]
        if export_request.include_assessments:
            headers.extend(["Assessment Count", "Learning Track"])
        
        writer.writerow(headers)
        
        # Write data
        for user in users:
            row = [
                user.id,
                user.email,
                user.username,
                user.full_name,
                user.mobile_number,
                user.is_active,
                user.is_superuser,
                user.created_at.isoformat() if user.created_at else ""
            ]
            
            if export_request.include_assessments:
                from app.models.assessment import UserAssessment
                assessment_count = db.query(UserAssessment).filter(
                    UserAssessment.user_id == user.id,
                    UserAssessment.status == "completed"
                ).count()
                learning_track = "Strategic Vision" if assessment_count > 0 else "None"
                
                row.extend([assessment_count, learning_track])
            
            writer.writerow(row)
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=users_export.csv"}
        )
    
    elif export_request.format == "json":
        # Create JSON
        users_data = []
        for user in users:
            user_data = {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "mobile_number": user.mobile_number,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            
            if export_request.include_assessments:
                from app.models.assessment import UserAssessment
                assessment_count = db.query(UserAssessment).filter(
                    UserAssessment.user_id == user.id,
                    UserAssessment.status == "completed"
                ).count()
                learning_track = "Strategic Vision" if assessment_count > 0 else None
                
                user_data.update({
                    "assessment_count": assessment_count,
                    "learning_track": learning_track
                })
            
            users_data.append(user_data)
        
        return StreamingResponse(
            io.BytesIO(json.dumps(users_data, indent=2).encode('utf-8')),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=users_export.json"}
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported export format"
        )


@router.post("/users/bulk-action")
def bulk_user_action(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
    action_data: BulkUserAction,
) -> Any:
    """
    Perform bulk actions on users (Admin only).
    """
    users = db.query(User).filter(User.id.in_(action_data.user_ids)).all()
    
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found"
        )
    
    updated_count = 0
    
    if action_data.action == "activate":
        for user in users:
            user.is_active = True
            updated_count += 1
    elif action_data.action == "deactivate":
        for user in users:
            user.is_active = False
            updated_count += 1
    elif action_data.action == "delete":
        for user in users:
            db.delete(user)
            updated_count += 1
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action"
        )
    
    db.commit()
    
    return {
        "message": f"Bulk action '{action_data.action}' completed successfully",
        "affected_users": updated_count
    }


@router.get("/role-requests")
def get_role_requests(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
    status: str = Query("pending", description="Filter by status (pending, approved, rejected)"),
) -> Any:
    """
    Get all pending role requests (Admin only).
    """
    query = db.query(User).filter(User.requested_role.isnot(None))
    
    if status:
        query = query.filter(User.role_request_status == status)
    
    users = query.order_by(User.role_requested_at.desc()).all()
    
    requests = []
    for user in users:
        requests.append({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "current_role": user.role.value,
            "requested_role": user.requested_role.value,
            "status": user.role_request_status.value,
            "reason": user.role_request_reason,
            "requested_at": user.role_requested_at,
            "approved_by": user.role_approved_by,
            "approved_at": user.role_approved_at
        })
    
    return {"role_requests": requests}


@router.post("/role-requests/{user_id}/approve")
def approve_role_request(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
    user_id: int,
) -> Any:
    """
    Approve a role request (Admin only).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.has_pending_role_request():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a pending role request"
        )
    
    # Approve the role request
    from datetime import datetime
    user.role = user.requested_role
    user.role_request_status = RoleRequestStatus.APPROVED
    user.role_approved_by = current_user.id
    user.role_approved_at = datetime.utcnow()
    
    # Clear the request fields
    user.requested_role = None
    user.role_request_reason = None
    user.role_requested_at = None
    
    db.commit()
    
    return {
        "message": f"Role request approved. User {user.email} is now a {user.role.value}.",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role.value
        }
    }


@router.post("/role-requests/{user_id}/reject")
def reject_role_request(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
    user_id: int,
) -> Any:
    """
    Reject a role request (Admin only).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.has_pending_role_request():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a pending role request"
        )
    
    # Reject the role request
    from datetime import datetime
    user.role_request_status = RoleRequestStatus.REJECTED
    user.role_approved_by = current_user.id
    user.role_approved_at = datetime.utcnow()
    
    # Clear the request fields
    user.requested_role = None
    user.role_request_reason = None
    user.role_requested_at = None
    
    db.commit()
    
    return {
        "message": f"Role request rejected for user {user.email}.",
        "user": {
            "id": user.id,
            "email": user.email,
            "current_role": user.role.value
        }
    }


@router.post("/invite-user")
def invite_user(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
    invitation: UserInvitation,
) -> Any:
    """
    Invite a user to join as coach or admin (Admin only).
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == invitation.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Generate a temporary username
    import uuid
    temp_username = f"invited_{uuid.uuid4().hex[:8]}"
    
    # Create invitation token (in production, this would be sent via email)
    invitation_token = security.create_access_token(
        f"invite_{invitation.email}", expires_delta=timedelta(days=7)
    )
    
    # In a real application, you would:
    # 1. Send an email with the invitation link
    # 2. Store invitation details in a separate table
    # 3. Create user account when they accept the invitation
    
    return {
        "message": f"Invitation sent to {invitation.email}",
        "invitation": {
            "email": invitation.email,
            "role": invitation.role.value,
            "invitation_token": invitation_token,  # Remove this in production
            "expires_in": "7 days"
        }
    }
