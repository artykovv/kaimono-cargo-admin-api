# schemas/status.py
from pydantic import BaseModel, ConfigDict
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
    
    model_config = ConfigDict(from_attributes=True)