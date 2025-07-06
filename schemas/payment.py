# schemas/payment_method.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID

class PaymentMethodBase(BaseModel):
    name: str
    code: str
    is_active: Optional[bool] = True

class PaymentMethodCreate(PaymentMethodBase):
    pass

class PaymentMethodUpdate(PaymentMethodBase):
    name: Optional[str] = None
    code: Optional[str] = None
    is_active: Optional[bool] = None

class PaymentMethodResponse(PaymentMethodBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PaymentBase(BaseModel):
    client_id: Optional[int] = None
    branch_id: Optional[int] = None
    payment_method_id: Optional[int] = None
    amount: Optional[Decimal] = None
    product_ids: Optional[List[int]] = []

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    id: int
    paid_at: datetime
    taken_by_id: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)