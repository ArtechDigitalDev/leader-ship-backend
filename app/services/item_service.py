from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


def get(db: Session, id: Any) -> Optional[Item]:
    return db.query(Item).filter(Item.id == id).first()


def get_multi(
    db: Session, *, skip: int = 0, limit: int = 100
) -> list[Item]:
    return db.query(Item).offset(skip).limit(limit).all()


def get_multi_by_owner(
    db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
) -> list[Item]:
    return (
        db.query(Item)
        .filter(Item.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create(db: Session, *, obj_in: ItemCreate, owner_id: int) -> Item:
    db_obj = Item(
        title=obj_in.title,
        description=obj_in.description,
        is_active=obj_in.is_active,
        owner_id=owner_id,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(
    db: Session, *, db_obj: Item, obj_in: Union[ItemUpdate, Dict[str, Any]]
) -> Item:
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove(db: Session, *, id: int) -> Item:
    obj = db.query(Item).get(id)
    db.delete(obj)
    db.commit()
    return obj
