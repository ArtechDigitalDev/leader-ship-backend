from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.services import user_service as crud
from app.models.user import User
from app.schemas.token import TokenPayload
from app.core import security
from app.core.config import settings
from app.core.database import SessionLocal
from app.utils.response import APIException

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token"
)


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Could not validate credentials",
            success=False
        )
    user = crud.get(db, id=int(token_data.sub))
    if not user:
        raise APIException(
            status_code=404, 
            message="User not found",
            success=False
        )
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not crud.is_active(current_user):
        raise APIException(
            status_code=400, 
            message="Inactive user",
            success=False
        )
    return current_user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not crud.is_superuser(current_user):
        raise APIException(
            status_code=400, 
            message="The user doesn't have enough privileges",
            success=False
        )
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not crud.is_active(current_user):
        raise APIException(
            status_code=400,
            message="Inactive user",
            success=False
        )
    if current_user.role != "admin":
        raise APIException(
            status_code=403,
            message="Admin access required",
            success=False
        )
    return current_user


def get_current_coach_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not crud.is_active(current_user):
        raise APIException(
            status_code=400,
            message="Inactive user",
            success=False
        )
    if current_user.role != "coach":
        raise APIException(
            status_code=403,
            message="Coach access required",
            success=False
        )
    return current_user


def get_current_admin_or_coach_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not crud.is_active(current_user):
        raise APIException(
            status_code=400,
            message="Inactive user",
            success=False
        )
    if current_user.role not in ["admin", "coach"]:
        raise APIException(
            status_code=403,
            message="Admin or Coach access required",
            success=False
        )
    return current_user