from sqlalchemy.ext.asyncio import AsyncSession
import logging
import httpx
from .headers import headers
from config.config import TRANSIT_API_URL

logger = logging.getLogger(__name__)


async def notification_transit(db: AsyncSession, data: dict):
    notifications = []

    for user_code, count in data.items():  # Итерируем по ключам и значениям
        try:
            notifications.append({
                "telegram_chat_id": user_code,  # Ключ теперь - это user_code
                "count": count  # Значение - это count
            })
        except Exception as e:
            logger.error(f"Ошибка при получении telegram_chat_id для user_code {user_code}: {e}")

    if notifications:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(TRANSIT_API_URL, headers=headers, json=notifications)

                if response.status_code != 200:
                    logger.error(f"Не удалось отправить уведомления: {response.text}")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомлений: {e}")