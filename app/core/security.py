from datetime import datetime, timedelta
from typing import Any, Union, Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None, user_data: dict = None
) -> str:
    """Create JWT access token with user information"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire, 
        "sub": str(subject),
        "user_id": user_data.get("id") if user_data else None,
        "email": user_data.get("email") if user_data else None,
        "username": user_data.get("username") if user_data else None,
        "role": user_data.get("role") if user_data else None,
        "is_active": user_data.get("is_active") if user_data else None,
        "is_email_verified": user_data.get("is_email_verified") if user_data else None
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_token(token: str) -> Optional[str]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        subject: str = payload.get("sub")
        if subject is None:
            return None
        return subject
    except jwt.JWTError:
        return None


def decode_token(token: str) -> Optional[dict]:
    """Decode JWT token and return user data"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return {
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "username": payload.get("username"),
            "role": payload.get("role"),
            "is_active": payload.get("is_active"),
            "is_email_verified": payload.get("is_email_verified")
        }
    except jwt.JWTError:
        return None
