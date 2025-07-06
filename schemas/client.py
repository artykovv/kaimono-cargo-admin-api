# schemas/client.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from .product import ProductResponse
from .base import ClientBase

class ClientCreate(BaseModel):
    name: Optional[str] = None
    number: Optional[str] = None
    city: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    branch_id: Optional[int] = None

class ClientUpdate(ClientCreate):
    pass

class ClientResponse(ClientBase):
    id: int
    code: Optional[str] = None
    numeric_code: Optional[int] = None
    registered_at: datetime
    branch_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedClientsResponse(BaseModel):
    clients: List[ClientResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ClientDataResponse(ClientBase):
    id: int
    code: Optional[str] = None
    numeric_code: Optional[int] = None
    registered_at: datetime
    branch_id: Optional[int] = None
    products: Optional[List[ProductResponse]] = None  # Добавляем список товаров
    
    model_config = ConfigDict(from_attributes=True)