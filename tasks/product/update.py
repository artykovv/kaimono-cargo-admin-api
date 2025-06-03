import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Product, Status, Configuration
import pytz
from config.database import async_session_maker
from config.statuses import BaseStatus

from tasks.product.create_transit import create_notification_for_products_status_transit


async def update_product_statuses_async():
    async with async_session_maker() as db:
        """
        Асинхронно обновляет статусы товаров, находящихся в Китае дольше определенного времени.
        """
        try:
            # Получаем конфигурацию transit_hours
            transit_hours_query = select(Configuration).filter(Configuration.key == "transit_hours")
            transit_hours_result = await db.execute(transit_hours_query)
            transit_hours = transit_hours_result.scalars().first()
            hours_value = int(transit_hours.value)

            # Вычисляем время, которое было hours_value часов назад
            hours_ago = datetime.now(pytz.UTC) - timedelta(hours=hours_value)

            # Получаем статус "CHINA"
            status_china_query = select(Status).filter(Status.name == BaseStatus.CHINA)
            status_china_result = await db.execute(status_china_query)
            status_china = status_china_result.scalars().first()

            # Получаем товары в Китае, у которых дата <= hours_ago
            products_query = select(Product).filter(
                Product.status_id == status_china.id,
                Product.date <= hours_ago
            )
            products_result = await db.execute(products_query)
            products_in_china = products_result.scalars().all()

            updated_count = 0
            updated_ids = []

            # Получаем статус "В пути"
            status_transit_query = select(Status).filter(Status.name == BaseStatus.TRANSIT)
            status_transit_result = await db.execute(status_transit_query)
            status_transit = status_transit_result.scalars().first()

            # Обновляем товары
            for product in products_in_china:
                product.status_id = status_transit.id
                product.date = datetime.now(pytz.timezone('Asia/Bishkek')).date()
                db.add(product)
                updated_count += 1
                updated_ids.append(product.id)

            # Фиксируем изменения в базе данных
            await db.commit()
            # Если нужна асинхронная нотификация, можно создать задачу
            asyncio.create_task(create_notification_for_products_status_transit(session=db))

            return {
                "updated_count": updated_count,
                "updated_ids": updated_ids,
                "timestamp": datetime.now(pytz.UTC).isoformat(),
            }

        except Exception as e:
            await db.rollback()  # Откатываем изменения в случае ошибки
            return {"error": str(e)}