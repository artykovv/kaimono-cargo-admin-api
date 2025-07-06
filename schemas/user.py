# schemas/user.py
from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID
from typing import List, Optional
from datetime import datetime
from fastapi_users import schemas

class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    name: Optional[str] = None
    lastname: Optional[str] = None
    register_at: Optional[datetime] = None
    is_active: bool
    is_superuser: bool
    is_verified: bool
    branch_ids: List[int] = []

    model_config = ConfigDict(from_attributes=True)

class UserCreate(schemas.BaseUserCreate):
    name: Optional[str] = None
    lastname: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    name: Optional[str] = None
    lastname: Optional[str] = None
    branch_ids: Optional[List[int]] = None