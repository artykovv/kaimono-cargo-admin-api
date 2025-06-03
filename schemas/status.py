# schemas/status.py
from pydantic import BaseModel
from typing import Optional

class StatusBase(BaseModel):
    name: str
    description: Optional[str] = None

class StatusCreate(StatusBase):
    pass

class StatusUpdate(StatusBase):
    name: Optional[str] = None

class StatusResponse(StatusBase):
    id: int
    
    class Config:
        from_attributes = True