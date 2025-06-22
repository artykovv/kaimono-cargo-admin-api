# routers/payment_method.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from auth.fastapi_users_instance import fastapi_users
from schemas.payment import PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse
from services.payment import PaymentMethodService
from config.database import get_async_session
from models.user import User

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])



@router.post("/", response_model=PaymentMethodResponse)
async def create_payment_method(
    method: PaymentMethodCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    db_method = await PaymentMethodService.create_payment_method(db, method)
    return db_method

@router.get("/{method_id}", response_model=PaymentMethodResponse)
async def read_payment_method(
    method_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    db_method = await PaymentMethodService.get_payment_method(db, method_id)
    if db_method is None:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return db_method

@router.get("/", response_model=list[PaymentMethodResponse])
async def read_payment_methods(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    methods = await PaymentMethodService.get_all_payment_methods(db, skip=skip, limit=limit)
    return methods

@router.patch("/{method_id}", response_model=PaymentMethodResponse)
async def update_payment_method(
    method_id: int,
    method: PaymentMethodUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    db_method = await PaymentMethodService.update_payment_method(db, method_id, method)
    if db_method is None:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return db_method

@router.delete("/{method_id}")
async def delete_payment_method(
    method_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    db_method = await PaymentMethodService.delete_payment_method(db, method_id)
    if db_method is None:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return {"message": "Payment method deleted successfully"}