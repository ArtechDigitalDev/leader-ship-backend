from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.schemas.user import UserCreate, UserUpdate


def get(db: Session, id: Any) -> Optional[User]:
    return db.query(User).filter(User.id == id).first()


def get_by_email(db: Session, *, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_by_username(db: Session, *, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_by_mobile_number(db: Session, *, mobile_number: str) -> Optional[User]:
    return db.query(User).filter(User.mobile_number == mobile_number).first()


def get_multi(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at.asc()).all()


def create(db: Session, *, obj_in: UserCreate) -> User:
    db_obj = User(
        email=obj_in.email,
        username=obj_in.username,
        full_name=obj_in.full_name,
        mobile_number=obj_in.mobile_number,
        hashed_password=get_password_hash(obj_in.password),
        role=obj_in.role,
        is_superuser=obj_in.is_superuser,
        is_email_verified=False,  # New users need email verification
    )
    db.add(db_obj)
    db.flush()  # Get user ID without committing
    
    # Create default user preferences
    preferences = UserPreferences(
        user_id=db_obj.id,
        frequency="daily",
        active_days=["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        lesson_time="00:00",
        timezone="ET",
        days_between_lessons=1,
        reminder_enabled="true",
        reminder_time="14:00",
        reminder_type="1"
    )
    db.add(preferences)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(
    db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
) -> User:
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)
    
    if update_data.get("password"):
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
    
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove(db: Session, *, id: int) -> User:
    obj = db.query(User).get(id)
    db.delete(obj)
    db.commit()
    return obj


def authenticate(db: Session, *, username: str, password: str) -> Optional[User]:
    user = get_by_username(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def authenticate_by_email(db: Session, *, email: str, password: str) -> Optional[User]:
    user = get_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def is_active(user: User) -> bool:
    return user.is_active


def is_superuser(user: User) -> bool:
    return user.is_superuser
