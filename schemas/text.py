from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class TextBase(BaseModel):
    key: str
    name: str
    text: str

class TextCreate(TextBase):
    pass

class TextUpdate(BaseModel):
    name: Optional[str] = None
    text: Optional[str] = None

class TextResponse(TextBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)