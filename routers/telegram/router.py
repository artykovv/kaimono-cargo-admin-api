import asyncio
import json
from fastapi import APIRouter, Body, Depends, Query, Request, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from auth.fastapi_users_instance import fastapi_users
from config.database import get_async_session
from models.user import User
from models.client import Client
from typing import List, Optional
import shutil
import os
import httpx

from schemas.telegram import TelegramMessage
from tasks.telegram.send_message import send_notification_telegram, send_send_notification_telegram_photo
from media import MEDIA_DIR

router = APIRouter(prefix="/telegram", tags=["telegram"])

# Существующий поиск клиентов (без изменений)
@router.get("/clients/search")
async def search_clients(
    search: str = Query(""),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    if not search.strip():
        return []

    query = select(Client).where(
        Client.name.ilike(f"%{search}%") |
        Client.number.ilike(f"%{search}%") |
        Client.city.ilike(f"%{search}%")
    ).limit(50)
    result = await db.execute(query)
    clients = result.scalars().all()

    return [
        {
            "id": client.id,
            "name": client.name or "",
            "number": client.number or "",
            "code": client.code or "",
            "telegram_chat_id": client.telegram_chat_id or ""
        } for client in clients
    ]


@router.post("/send-message")
async def send_notification_without_photo(
    telegram_message: TelegramMessage,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(fastapi_users.current_user(verified=True))
):
    background_tasks.add_task(send_notification_telegram, telegram_message.message_text, telegram_message.telegram_chat_ids)
    return {"message": "Сообщение отправлено"}


@router.post("/send-photo")
async def send_notification_with_photo(
    request: Request,
    background_tasks: BackgroundTasks,
    message_text: str = Form(...),
    telegram_chat_ids: Optional[str] = Form(None),
    files: List[UploadFile] = File(...)
):
    # Конвертируем строку "123,456,789" в список [123, 456, 789]
    chat_ids = [int(i) for i in telegram_chat_ids.split(",")] if telegram_chat_ids else []
    
    uploaded_files = []
    

    try:
        for file in files:
            file_path = os.path.join(MEDIA_DIR, file.filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            full_url = f"{request.base_url}media/{file.filename}"
            uploaded_files.append(full_url)
    except Exception as e:
        return {"error": str(e)}
    finally:
        for file in files:
            file.file.close()

    background_tasks.add_task(
        send_send_notification_telegram_photo, 
        message_text, 
        chat_ids, 
        uploaded_files
    )
    return {"message": "Сообщение отправлено"}
