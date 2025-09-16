from typing import Optional
from pydantic import BaseModel


class ItemBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True


class ItemCreate(ItemBase):
    title: str


class ItemUpdate(ItemBase):
    pass


class ItemInDBBase(ItemBase):
    id: Optional[int] = None
    owner_id: Optional[int] = None

    model_config = {
        "from_attributes": True
    }


class Item(ItemInDBBase):
    pass


class ItemInDB(ItemInDBBase):
    pass
