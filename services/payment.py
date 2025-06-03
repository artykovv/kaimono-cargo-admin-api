# services/payment_method_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import PaymentMethod, Payment, Product
from schemas.payment import PaymentMethodCreate, PaymentMethodUpdate, PaymentCreate, PaymentUpdate
from typing import Optional, List
from uuid import UUID

class PaymentMethodService:
    @staticmethod
    async def create_payment_method(db: AsyncSession, method_data: PaymentMethodCreate) -> PaymentMethod:
        db_method = PaymentMethod(**method_data.dict())
        db.add(db_method)
        await db.commit()
        await db.refresh(db_method)
        return db_method

    @staticmethod
    async def get_payment_method(db: AsyncSession, method_id: int) -> Optional[PaymentMethod]:
        result = await db.execute(
            select(PaymentMethod).filter(PaymentMethod.id == method_id)
        )
        return result.scalars().first()

    @staticmethod
    async def get_all_payment_methods(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PaymentMethod]:
        result = await db.execute(
            select(PaymentMethod).offset(skip).limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def update_payment_method(db: AsyncSession, method_id: int, method_data: PaymentMethodUpdate) -> Optional[PaymentMethod]:
        db_method = await PaymentMethodService.get_payment_method(db, method_id)
        if not db_method:
            return None
        
        update_data = method_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_method, key, value)
        
        await db.commit()
        await db.refresh(db_method)
        return db_method

    @staticmethod
    async def delete_payment_method(db: AsyncSession, method_id: int) -> Optional[PaymentMethod]:
        db_method = await PaymentMethodService.get_payment_method(db, method_id)
        if not db_method:
            return None
        
        await db.delete(db_method)
        await db.commit()
        return db_method
    

class PaymentService:
    @staticmethod
    async def create_payment(db: AsyncSession, payment_data: PaymentCreate, user_id: UUID) -> Payment:
        db_payment = Payment(
            client_id=payment_data.client_id,
            branch_id=payment_data.branch_id,
            payment_method_id=payment_data.payment_method_id,
            amount=payment_data.amount,
            taken_by_id=user_id,
        )
        
        if payment_data.product_ids:
            products = await db.execute(
                select(Product).where(Product.id.in_(payment_data.product_ids))
            )
            db_payment.products = products.scalars().all()
        
        db.add(db_payment)
        await db.commit()
        await db.refresh(db_payment)
        return db_payment

    @staticmethod
    async def get_payment(db: AsyncSession, payment_id: int) -> Optional[Payment]:
        result = await db.execute(
            select(Payment).filter(Payment.id == payment_id)
        )
        return result.scalars().first()

    @staticmethod
    async def get_all_payments(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Payment]:
        result = await db.execute(
            select(Payment).offset(skip).limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_user_payments(db: AsyncSession, user_branches: List[int], skip: int = 0, limit: int = 100) -> List[Payment]:
        result = await db.execute(
            select(Payment)
            .filter(Payment.branch_id.in_(user_branches))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def update_payment(db: AsyncSession, payment_id: int, payment_data: PaymentUpdate) -> Optional[Payment]:
        db_payment = await PaymentService.get_payment(db, payment_id)
        if not db_payment:
            return None
        
        update_data = payment_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            if key == "product_ids" and value is not None:
                products = await db.execute(
                    select(Product).where(Product.id.in_(value))
                )
                db_payment.products = products.scalars().all()
            else:
                setattr(db_payment, key, value)
        
        await db.commit()
        await db.refresh(db_payment)
        return db_payment

    @staticmethod
    async def delete_payment(db: AsyncSession, payment_id: int) -> Optional[Payment]:
        db_payment = await PaymentService.get_payment(db, payment_id)
        if not db_payment:
            return None
        
        await db.delete(db_payment)
        await db.commit()
        return db_payment