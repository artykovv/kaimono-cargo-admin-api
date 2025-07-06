# schemas/product.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from .base import ClientBase, ProductBase
from .status import StatusBase

class ProductCreate(ProductBase):
    client_code: str

class ProductUpdate(ProductBase):
    update_date: Optional[date] = None
    client_code: Optional[str] = None

class ProductResponse(BaseModel):
    id: int
    product_code: str
    weight: Optional[Decimal] = None
    price: Optional[int] = None
    date: date
    take_time: Optional[datetime] = None
    status_id: Optional[int] = None
    branch_id: Optional[int] = None
    registered_at: datetime
    client: Optional[ClientBase] = None
    status: Optional[StatusBase] = None
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedProductsResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BulkRequest(BaseModel):
    product_ids: List[int]
    status_id: Optional[int] = None