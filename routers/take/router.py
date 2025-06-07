from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, Form, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
from auth.fastapi_users_instance import fastapi_users
from config.database import get_async_session
from sqlalchemy.orm import selectinload

from config.statuses import BaseStatus
from models import User, Client, Product, Payment, PaymentMethod, Status, payment_products, ProductHistory
from services.product_history import ProductHistoryManager



router = APIRouter(prefix="/take", tags=["take"])


# Read (one)
@router.get("/{code}")
async def client_code(
    code: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    query = (
        select(Client)
        .where(Client.numeric_code == code)
        .options(selectinload(Client.products).joinedload(Product.status))
    )
    result = await db.execute(query)
    client = result.scalars().first()

    if client:
        # Фильтруем продукты с нужным статусом
        client.products = [p for p in client.products if p.status and p.status.name == BaseStatus.BISHKEK]

    return client

# Маршрут для выдачи товаров
@router.post("/issue")
async def take_issue(
    selected_products: List[int] = Form(...),
    payment_method: int = Form(...),
    client_code: str = Form(...),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    try:
        if not selected_products:
            raise HTTPException(status_code=400, detail="Выберите товары для выдачи")
        if not payment_method:
            raise HTTPException(status_code=400, detail="Выберите способ оплаты")

        # Получаем клиента
        client_query = select(Client).where(Client.code == client_code)
        client_result = await db.execute(client_query)
        client = client_result.scalars().first()
        if not client:
            raise HTTPException(status_code=404, detail="Клиент не найден")

        # Получаем способ оплаты
        payment_method_query = select(PaymentMethod).where(PaymentMethod.id == payment_method, PaymentMethod.is_active == True)
        payment_method_result = await db.execute(payment_method_query)
        payment_method_obj = payment_method_result.scalars().first()
        if not payment_method_obj:
            raise HTTPException(status_code=404, detail="Выбранный способ оплаты недоступен")

        # Получаем статус "PIKED"
        status_query = select(Status).where(Status.name == BaseStatus.PIKED)
        status_result = await db.execute(status_query)
        status_piked = status_result.scalars().first()
        if not status_piked:
            raise HTTPException(status_code=404, detail="Статус 'PIKED' не найден")

        # Обновляем товары
        products_query = select(Product).where(Product.id.in_(selected_products))
        result = await db.execute(products_query)
        products_to_update = result.scalars().all()
        if not products_to_update:
            raise HTTPException(status_code=404, detail="Выбранные товары не найдены")

        total_price = sum(product.price or 0 for product in products_to_update)

        for product in products_to_update:
            product.status_id = status_piked.id
            product.date = datetime.now(timezone(timedelta(hours=6))).date()
            
            # Устанавливаем даты через ProductHistoryManager
            ProductHistoryManager.apply_status_dates(product, BaseStatus.PIKED)
            
            db.add(product)

            # Создаем запись в ProductHistory через ProductHistoryManager
            await ProductHistoryManager.log_action(
                db=db,
                product=product,
                action="issued",
                user=current_user,
                client_code=client.code
            )

        # Создаем запись оплаты
        payment = Payment(
            client_id=client.id,
            branch_id=client.branch_id if client.branch_id else None,
            payment_method_id=payment_method_obj.id,
            amount=total_price,
            taken_by_id=current_user.id,
            paid_at=datetime.now(timezone(timedelta(hours=6))).replace(tzinfo=None)
        )
        db.add(payment)
        await db.flush()  # Получаем payment.id для связи с товарами

        # Привязываем товары к оплате через таблицу payment_products
        payment_product_data = [
            {"payment_id": payment.id, "product_id": product.id}
            for product in products_to_update
        ]
        await db.execute(
            insert(payment_products),
            payment_product_data
        )

        await db.commit()

        return {
            "message": "Товары успешно выданы и оплата зафиксирована",
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при выдаче товаров: {str(e)}")