

from datetime import datetime
from operator import and_
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

import pytz

from models import Product, Client
from config.statuses import BaseStatus
from config.database import async_session_maker

from tasks.notification.transit import send_notification_telegram_transit


async def create_notification_for_products_status_transit(session: AsyncSession):
    # Установите текущую дату в Бишкеке
    today = datetime.now(pytz.timezone('Asia/Bishkek')).date()
    
    # Выборка продуктов со статусом IN_TRANSIT и сегодняшней датой, включая данные клиента
    stmt = (
        select(Product)
        .options(joinedload(Product.client))  # Подгружаем связанную таблицу Client
        .where(
            and_(
                Product.status_id == 3,  # Сравниваем status_id
                Product.date == today
            )
        )
    )

    result = await session.execute(stmt)
    products = result.scalars().all()

    # Словарь для хранения количества товаров по telegram_chat_id
    product_count_by_chat_id = {}

    for product in products:
        # Проверяем, что у продукта есть связанный клиент и telegram_chat_id
        if product.client and product.client.telegram_chat_id:
            chat_id = product.client.telegram_chat_id
            if chat_id not in product_count_by_chat_id:
                product_count_by_chat_id[chat_id] = 0
            product_count_by_chat_id[chat_id] += 1  # Увеличиваем счетчик для этого chat_id
        else:
            # Можно добавить логирование, если telegram_chat_id отсутствует
            continue

    # Подготавливаем данные для уведомлений
    notifications = [
        {
            "telegram_chat_id": chat_id,
            "count": count
        }
        for chat_id, count in product_count_by_chat_id.items()
    ]

    # Отправка уведомлений
    await send_notification_telegram_transit(session, notifications)