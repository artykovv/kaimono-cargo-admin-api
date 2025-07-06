from pydantic import BaseModel, HttpUrl
from typing import Optional


class AddressBase(BaseModel):
    name: str
    url: str
    active: bool = False


class AddressPhotoCreate(AddressBase):
    pass


class AddressPhotoRead(AddressBase):
    id: int

    class Config:
        from_attributes = True


class AddressPhotoUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    active: Optional[bool] = None


class AddressVideoCreate(AddressBase):
    pass


class AddressVideoRead(AddressBase):
    id: int

    class Config:
        from_attributes = True


class AddressVideoUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    active: Optional[bool] = None