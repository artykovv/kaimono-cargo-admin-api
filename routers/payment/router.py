# routers/payment.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from auth.fastapi_users_instance import fastapi_users
from schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse
from services.payment import PaymentService
from config.database import get_async_session
from models.user import User

router = APIRouter(prefix="/payments", tags=["payments"])

current_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)

async def check_superuser_permissions(current_user: User = Depends(current_superuser)):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения действия.",
        )

@router.post("/", response_model=PaymentResponse)
async def create_payment(
    payment: PaymentCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
):
    db_payment = await PaymentService.create_payment(db, payment, user.id)
    return db_payment

@router.get("/{payment_id}", response_model=PaymentResponse)
async def read_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
):
    db_payment = await PaymentService.get_payment(db, payment_id)
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    if not user.is_superuser and db_payment.branch_id not in [b.id for b in user.branches]:
        raise HTTPException(status_code=403, detail="Forbidden")
    return db_payment

@router.get("/", response_model=list[PaymentResponse])
async def read_payments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
):
    if user.is_superuser:
        payments = await PaymentService.get_all_payments(db, skip=skip, limit=limit)
    else:
        user_branches = [b.id for b in user.branches]
        payments = await PaymentService.get_user_payments(db, user_branches, skip=skip, limit=limit)
    return payments

@router.patch("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int,
    payment: PaymentUpdate,
    db: AsyncSession = Depends(get_async_session),
    _=Depends(check_superuser_permissions),
):
    db_payment = await PaymentService.update_payment(db, payment_id, payment)
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return db_payment

@router.delete("/{payment_id}")
async def delete_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_async_session),
    _=Depends(check_superuser_permissions),
):
    db_payment = await PaymentService.delete_payment(db, payment_id)
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"message": "Payment deleted successfully"}