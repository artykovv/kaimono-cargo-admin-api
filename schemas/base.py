from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import date

class ClientBase(BaseModel):
    id: int
    name: Optional[str] = None
    number: Optional[str] = None
    code: str
    city: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    branch_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class ProductBase(BaseModel):
    product_code: Optional[str] = None
    weight: Optional[Decimal] = None
    price: Optional[int] = None
    product_date: Optional[date] = None
    status_id: Optional[int] = None
    branch_id: Optional[int] = None