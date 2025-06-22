
from datetime import date, datetime
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from auth.fastapi_users_instance import fastapi_users
from config.database import get_async_session

from models import Client, Product, Status, User, PaymentMethod, payment_products, Payment

router = APIRouter()

@router.get("/summary")
async def get_statistics(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    """
    Возвращает статистику:
    - Общее количество клиентов
    - Общее количество товаров
    - Количество товаров по каждому статусу (BISHKEK, CHINA, TRANSIT, PIKED)
    """
    try:
        # 1. Подсчет общего количества клиентов
        clients_count_query = select(func.count(Client.id)).select_from(Client)
        clients_count_result = await db.execute(clients_count_query)
        total_clients = clients_count_result.scalar() or 0

        # 2. Подсчет общего количества товаров
        products_count_query = select(func.count(Product.id)).select_from(Product)
        products_count_result = await db.execute(products_count_query)
        total_products = products_count_result.scalar() or 0

        # 3. Получение всех статусов из таблицы statuses
        statuses_query = select(Status)
        statuses_result = await db.execute(statuses_query)
        statuses = statuses_result.scalars().all()

        # Если статусов нет, возвращаем пустой словарь для products_by_status
        if not statuses:
            return {
                "total_clients": total_clients,
                "total_products": total_products,
                "products_by_status": {}
            }

        # 4. Подсчет товаров по каждому статусу
        status_counts_query = (
            select(Product.status_id, func.count(Product.id).label("count"))
            .group_by(Product.status_id)
        )
        status_counts_result = await db.execute(status_counts_query)
        status_counts_raw = status_counts_result.all()

        # Формируем словарь статусов: id -> имя
        status_dict = {status.id: status.name for status in statuses}

        # Инициализируем результат для всех статусов (включая те, где товаров может быть 0)
        products_by_status = {status.name: 0 for status in statuses}

        # Заполняем количество товаров для каждого status_id
        for status_id, count in status_counts_raw:
            if status_id in status_dict:
                products_by_status[status_dict[status_id]] = count

        # Формируем итоговый результат
        result = {
            "total_clients": total_clients,
            "total_products": total_products,
            "products_by_status": products_by_status
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении статистики: {str(e)}")
    

@router.get("/data")
async def get_report(
    start_date: str = Query(default=date.today().isoformat(), description="Начальная дата (гггг-мм-дд)"),
    end_date: str = Query(default=date.today().isoformat(), description="Конечная дата (гггг-мм-дд)"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
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


    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_clients": total_clients,
        "total_products": total_products,
        "total_weight": round(total_weight, 2),
        "total_price": total_price,

    }