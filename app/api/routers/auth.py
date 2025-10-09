from datetime import timedelta, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.services import user_service as crud_user
from app.schemas.token import Token
from app.schemas.user import (
    User, UserCreate, UserSignUpResponse, UserLogin, UserLoginResponse,
    PasswordResetRequest, PasswordReset, EmailVerification, RoleRequest, RoleRequestResponse
)
from app.models.user import UserRole
from app.core import security
from app.core.config import settings
from app.api import deps
from app.utils.response import (
    APIResponse
)

router = APIRouter()


@router.post("/login/access-token", response_model=Token)
def login_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud_user.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    elif not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/test-token", response_model=User)
def test_token(current_user: User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    return current_user


@router.get("/decode-token", response_model=APIResponse)
def decode_token_endpoint(
    *,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Decode current user's token and return user data
    """
    return APIResponse(
        success=True,
        message="Token decoded successfully",
        data={
            "user_id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "is_email_verified": current_user.is_email_verified
        }
    )


@router.post("/login", response_model=APIResponse)
def login(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserLogin,
) -> Any:
    """
    Login with email and password (role-based)
    """
    user = crud_user.authenticate_by_email(
        db, email=user_in.email, password=user_in.password
    )
    if not user:
        return APIResponse(
            success=False,
            message="Incorrect email or password",
            data=None
        )
    elif not crud_user.is_active(user):
        return APIResponse(
            success=False,
            message="Inactive user",
            data=None
        )
    
    # Check if user role matches expected role (if specified)
    if user_in.role and user.role != user_in.role:
        return APIResponse(
            success=False,
            message=f"Access denied. Expected role: {user_in.role.value}, but user has role: {user.role.value}",
            data=None
        )
    
    # Check email verification for non-admin users
    if not user.is_email_verified and not user.is_admin():
        return APIResponse(
            success=False,
            message="Please verify your email address before logging in",
            data=None
        )
    
    # Create access token with user data
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    user_data = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "is_email_verified": user.is_email_verified
    }
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires, user_data=user_data
    )
    
    return APIResponse(
        success=True,
        message="Login successful",
        data={
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "mobile_number": user.mobile_number,
                "role": user.role,
                "is_active": user.is_active,
                "is_email_verified": user.is_email_verified,
                "created_at": user.created_at
            },
            "access_token": access_token,
            "token_type": "bearer"
        }
    )


@router.post("/login/username", response_model=UserLoginResponse)
def login_with_username(
    *,
    db: Session = Depends(deps.get_db),
    username: str = Form(...),
    password: str = Form(...),
) -> Any:
    """
    Login with username and password (form data)
    """
    user = crud_user.authenticate(
        db, username=username, password=password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    elif not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    return {
        "message": "Login successful",
        "user": user,
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/signup", response_model=APIResponse)
def sign_up(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user account with sign up
    """
    # Check if user with same email already exists
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        return APIResponse(
            success=False,
            message="A user with this email already exists in the system.",
            data=None
        )
    
    # Check if user with same username already exists
    user = crud_user.get_by_username(db, username=user_in.username)
    if user:
        return APIResponse(
            success=False,
            message="A user with this username already exists in the system.",
            data=None
        )
    
    # Check if user with same mobile number already exists
    user = crud_user.get_by_mobile_number(db, mobile_number=user_in.mobile_number)
    if user:
        return APIResponse(
            success=False,
            message="A user with this mobile number already exists in the system.",
            data=None
        )
    
    # Create new user
    user = crud_user.create(db, obj_in=user_in)
    
    # Send verification email
    from app.utils.email_verification import create_email_verification_token, send_verification_email
    
    verification_token = create_email_verification_token(user.email)
    print("verification token ---------", verification_token)
    send_verification_email(
        user_email=user.email,
        user_name=user.full_name or user.username,
        verification_token=verification_token
    )
    print("verification email sent ---------")
    
    # Create access token with user data
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    user_data = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "is_email_verified": user.is_email_verified
    }
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires, user_data=user_data
    )
    
    return APIResponse(
        success=True,
        message="User created successfully",
        data={
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "mobile_number": user.mobile_number,
                "role": user.role,
                "is_active": user.is_active,
                "is_email_verified": user.is_email_verified,
                "created_at": user.created_at
            },
            "access_token": access_token,
            "token_type": "bearer"
        }
    )


@router.get("/me", response_model=User)
def get_current_user(
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get current user information
    """
    return current_user


@router.post("/register", response_model=UserSignUpResponse)
def register_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
) -> Any:
    """
    Register new user (alias for signup)
    """
    # Check if user with same email already exists
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists in the system.",
        )
    
    # Check if user with same username already exists
    user = crud_user.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists in the system.",
        )
    
    # Check if user with same mobile number already exists
    user = crud_user.get_by_mobile_number(db, mobile_number=user_in.mobile_number)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this mobile number already exists in the system.",
        )
    
    # Create new user
    user = crud_user.create(db, obj_in=user_in)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    return {
        "message": "User registered successfully",
        "user": user,
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/forgot-password")
def forgot_password(
    *,
    db: Session = Depends(deps.get_db),
    request: PasswordResetRequest,
) -> Any:
    """
    Request password reset (sends email with reset token)
    """
    user = crud_user.get_by_email(db, email=request.email)
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Generate password reset token
    reset_token = security.create_access_token(
        user.id, expires_delta=timedelta(hours=1)
    )
    
    # In a real application, you would send an email here
    # For now, we'll just return the token (remove this in production)
    return {
        "message": "Password reset link sent to your email",
        "reset_token": reset_token,  # Remove this in production
        "expires_in": "1 hour"
    }


@router.post("/reset-password")
def reset_password(
    *,
    db: Session = Depends(deps.get_db),
    request: PasswordReset,
) -> Any:
    """
    Reset password using token
    """
    # Verify token
    user_id = security.verify_token(request.token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user = crud_user.get(db, id=int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = security.get_password_hash(request.new_password)
    db.commit()
    
    return {"message": "Password reset successfully"}


@router.post("/verify-email")
def verify_email(
    *,
    db: Session = Depends(deps.get_db),
    request: EmailVerification,
) -> Any:
    """
    Verify email address using token
    """
    # Verify token
    user_id = security.verify_token(request.token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    user = crud_user.get(db, id=int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_email_verified:
        return {"message": "Email already verified"}
    
    # Mark email as verified
    user.is_email_verified = True
    db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
def resend_verification(
    *,
    db: Session = Depends(deps.get_db),
    request: PasswordResetRequest,  # Reuse the email field
) -> Any:
    """
    Resend email verification token
    """
    user = crud_user.get_by_email(db, email=request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_email_verified:
        return {"message": "Email already verified"}
    
    # Generate verification token
    verification_token = security.create_access_token(
        user.id, expires_delta=timedelta(hours=24)
    )
    
    # In a real application, you would send an email here
    # For now, we'll just return the token (remove this in production)
    return {
        "message": "Verification email sent",
        "verification_token": verification_token,  # Remove this in production
        "expires_in": "24 hours"
    }


@router.post("/request-role", response_model=RoleRequestResponse)
def request_role(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    request: RoleRequest,
) -> Any:
    """
    Request a role upgrade (participant -> coach/admin)
    """
    # Only participants can request role upgrades
    if current_user.role != UserRole.PARTICIPANT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only participants can request role upgrades"
        )
    
    # Check if user already has a pending request
    if current_user.has_pending_role_request():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pending role request"
        )
    
    # Update user with role request
    from datetime import datetime
    current_user.requested_role = request.requested_role
    current_user.role_request_status = "pending"
    current_user.role_request_reason = request.reason
    current_user.role_requested_at = datetime.utcnow()
    
    db.commit()
    db.refresh(current_user)
    
    return RoleRequestResponse(
        message="Role request submitted successfully. An admin will review your request.",
        requested_role=request.requested_role,
        status="pending",
        reason=request.reason,
        requested_at=current_user.role_requested_at
    )


@router.get("/verify-email", response_model=APIResponse)
def verify_email(
    token: str,
    db: Session = Depends(deps.get_db)
):
    """
    Verify user's email address using the verification token
    
    Query Parameters:
    - token: JWT verification token from email
    """
    from app.utils.email_verification import verify_email_token
    
    # Verify token and extract email
    email = verify_email_token(token)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Get user by email
    user = crud_user.get_by_email(db, email=email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already verified
    if user.is_email_verified:
        return APIResponse(
            success=True,
            message="Email already verified",
            data={
                "email": user.email,
                "is_email_verified": True,
                "verified_at": "Already verified"
            }
        )
    
    # Update user's email verification status
    user.is_email_verified = True
    db.commit()
    db.refresh(user)
    
    return APIResponse(
        success=True,
        message="Email verified successfully! You can now access all features.",
        data={
            "email": user.email,
            "is_email_verified": True,
            "verified_at": datetime.utcnow().isoformat()
        }
    )


@router.post("/resend-verification-email", response_model=APIResponse)
def resend_verification_email(
    email: str,
    db: Session = Depends(deps.get_db)
):
    """
    Resend verification email to user
    
    Request Body:
    - email: User's email address
    """
    # Get user by email
    user = crud_user.get_by_email(db, email=email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already verified
    if user.is_email_verified:
        return APIResponse(
            success=False,
            message="Email already verified. No need to resend.",
            data=None
        )
    
    # Send verification email
    from app.utils.email_verification import create_email_verification_token, send_verification_email
    
    verification_token = create_email_verification_token(user.email)
    success = send_verification_email(
        user_email=user.email,
        user_name=user.full_name or user.username,
        verification_token=verification_token
    )
    
    if success:
        return APIResponse(
            success=True,
            message="Verification email sent successfully. Please check your inbox.",
            data={
                "email": user.email,
                "sent_at": datetime.utcnow().isoformat()
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later."
        )
