# tasks.py
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import NotificationTask, Client
from config.config import TELEGRAM_API_KEY, TELEGRAM_API_URL



async def send_notification_telegram(message: str, telegram_chat_ids: list = None):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-API-Key": TELEGRAM_API_KEY
    }
    url = f"{TELEGRAM_API_URL}/api/v1/send_message"
    payload = {
        "text": message,
        "parse_mode": "HTML"
    }
    if telegram_chat_ids:
        payload["chat_ids"] = telegram_chat_ids
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        return response.json()


async def send_send_notification_telegram_photo(
    message: str, 
    telegram_chat_ids: list = None,
    photo_urls: list = None
):

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-API-Key": TELEGRAM_API_KEY
    }
    url = f"{TELEGRAM_API_URL}/api/v1/send_photo"

    payload = {
        "photos": photo_urls,
        "message": message,
        "parse_mode": "HTML"
    }

    if telegram_chat_ids:
        payload["chat_ids"] = telegram_chat_ids

    print(payload)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        print(response.json())
        return response.json()