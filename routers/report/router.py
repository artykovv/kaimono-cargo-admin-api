from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from auth.fastapi_users_instance import fastapi_users
from config.database import get_async_session
from models import User, Status, Product, Client, PaymentMethod, Payment, payment_products
from config.statuses import BaseStatus

router = APIRouter(prefix="/report", tags=["report"])

# API маршрут для получения данных отчёта
@router.get("/data")
async def get_report(
    start_date: str = Query(default=date.today().isoformat(), description="Начальная дата (гггг-мм-дд)"),
    end_date: str = Query(default=date.today().isoformat(), description="Конечная дата (гггг-мм-дд)"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    # Преобразуем строки в даты
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    # Получаем статус "PIKED"
    status_query = select(Status).where(Status.name == "Забрали")  # Предполагаем BaseStatus.PIKED
    status_result = await db.execute(status_query)
    status = status_result.scalars().first()
    if not status:
        raise HTTPException(status_code=404, detail="Статус PIKED не найден")

    # Фильтрация товаров по дате и статусу
    products_query = select(Product).where(
        Product.date.between(start_date, end_date),
        Product.status_id == status.id
    )
    products_result = await db.execute(products_query)
    products = products_result.scalars().all()

    # Сводная информация
    total_clients = len(set(p.client_id for p in products if p.client_id))
    total_products = len(products)
    total_weight = sum(float(p.weight or 0) for p in products)
    total_price = sum(p.price or 0 for p in products)

    # Детальная информация по клиентам
    client_details_query = (
        select(
            Client.name.label("client__name"),
            Client.code.label("client__code"),
            PaymentMethod.name.label("payments__payment_method__name"),
            func.count(Product.id).label("total_products"),
            func.sum(Product.weight).label("total_weight"),
            func.sum(Product.price).label("total_price"),
            func.min(Product.take_time).label("earliest_take_time"),
            func.max(Product.take_time).label("latest_take_time")
        )
        .select_from(Product)
        .join(Client, Client.id == Product.client_id, isouter=True)
        .join(payment_products, Product.id == payment_products.c.product_id, isouter=True)
        .join(Payment, Payment.id == payment_products.c.payment_id, isouter=True)
        .join(PaymentMethod, Payment.payment_method_id == PaymentMethod.id, isouter=True)
        .where(
            Product.date.between(start_date, end_date),
            Product.status_id == status.id
        )
        .group_by(Client.name, Client.code, PaymentMethod.name)
        .order_by(Client.name)
    )
    client_details_result = await db.execute(client_details_query)
    client_details = client_details_result.all()

    # Подробности по каждому товару
    product_details_query = (
        select(
            Product.product_code,
            Client.name.label("client__name"),
            Client.code.label("client__code"),
            Product.weight,
            Product.price,
            Product.take_time,
            PaymentMethod.name.label("payments__payment_method__name")
        )
        .select_from(Product)
        .join(Client, Client.id == Product.client_id, isouter=True)
        .join(payment_products, Product.id == payment_products.c.product_id, isouter=True)
        .join(Payment, Payment.id == payment_products.c.payment_id, isouter=True)
        .join(PaymentMethod, Payment.payment_method_id == PaymentMethod.id, isouter=True)
        .where(
            Product.date.between(start_date, end_date),
            Product.status_id == status.id
        )
        .order_by(Client.name, Product.take_time)
    )
    product_details_result = await db.execute(product_details_query)
    product_details = product_details_result.all()

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_clients": total_clients,
        "total_products": total_products,
        "total_weight": round(total_weight, 2),
        "total_price": total_price,
        "client_details": [
            {
                "client__name": row.client__name,
                "client__code": row.client__code,
                "total_products": row.total_products,
                "total_weight": float(row.total_weight) if row.total_weight is not None else 0,
                "total_price": row.total_price if row.total_price is not None else 0,
                "payments__payment_method__name": row.payments__payment_method__name,
                "earliest_take_time": row.earliest_take_time.isoformat() if row.earliest_take_time else None,
                "latest_take_time": row.latest_take_time.isoformat() if row.latest_take_time else None
            } for row in client_details
        ],
        "product_details": [
            {
                "product_code": row.product_code,
                "client__name": row.client__name,
                "client__code": row.client__code,
                "weight": float(row.weight) if row.weight is not None else 0,
                "price": row.price if row.price is not None else 0,
                "take_time": row.take_time.isoformat() if row.take_time else None,
                "payments__payment_method__name": row.payments__payment_method__name
            } for row in product_details
        ]
    }