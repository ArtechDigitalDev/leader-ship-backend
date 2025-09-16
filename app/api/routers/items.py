from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.services import item_service as crud
from app.services import user_service as user_crud
from app.models.user import User as UserModel
from app.models.item import Item as ItemModel
from app.schemas.item import Item, ItemCreate, ItemUpdate
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[Item])
def read_items(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve items.
    """
    if user_crud.is_superuser(current_user):
        items = crud.get_multi(db, skip=skip, limit=limit)
    else:
        items = crud.get_multi_by_owner(
            db=db, owner_id=current_user.id, skip=skip, limit=limit
        )
    return items


@router.post("/", response_model=Item)
def create_item(
    *,
    db: Session = Depends(deps.get_db),
    item_in: ItemCreate,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new item.
    """
    item = crud.create(db=db, obj_in=item_in, owner_id=current_user.id)
    return item


@router.put("/{id}", response_model=Item)
def update_item(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    item_in: ItemUpdate,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an item.
    """
    item = crud.get(db=db, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not user_crud.is_superuser(current_user) and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    item = crud.update(db=db, db_obj=item, obj_in=item_in)
    return item


@router.get("/{id}", response_model=Item)
def read_item(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get item by ID.
    """
    item = crud.get(db=db, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not user_crud.is_superuser(current_user) and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return item


@router.delete("/{id}")
def delete_item(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an item.
    """
    item = crud.get(db=db, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not user_crud.is_superuser(current_user) and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    item = crud.remove(db=db, id=id)
    return item
