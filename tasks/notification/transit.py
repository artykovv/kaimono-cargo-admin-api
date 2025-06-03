import logging
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from config.config import TRANSIT_API_URL
from .headers import headers

logger = logging.getLogger(__name__)



async def send_notification_telegram_transit(db: AsyncSession, data: list):
    if not data:  # Проверяем, что список не пустой
        return

    # Поскольку data уже является списком словарей, просто используем его напрямую
    notifications = data

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(TRANSIT_API_URL, headers=headers, json=notifications)

            if response.status_code != 200:
                logger.error(f"Не удалось отправить уведомления: {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений: {e}")