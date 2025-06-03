from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import get_async_session
from models import ChinaAddress
from auth.fastapi_users_instance import fastapi_users
from models.user import User

router = APIRouter(prefix="/china-address", tags=["china-address"])

current_user = fastapi_users.current_user(active=True)

# Получение или создание экземпляра ChinaAddress
@router.get("/instance")
async def get_china_address(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_user)
):
    china_address = await ChinaAddress.get_instance(db)
    return {
        "id": china_address.id,
        "name1": china_address.name1,
        "name2": china_address.name2,
        "name3": china_address.name3
    }

# Обновление экземпляра ChinaAddress
@router.post("/update")
async def update_china_address(
    name1: str = Form(...),
    name2: str = Form(...),
    name3: str = Form(...),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_user)
):
    china_address = await ChinaAddress.get_instance(db)
    china_address.name1 = name1
    china_address.name2 = name2
    china_address.name3 = name3
    await china_address.save(db)
    return {
        "message": "Адрес успешно обновлён",
        "id": china_address.id,
        "name1": china_address.name1,
        "name2": china_address.name2,
        "name3": china_address.name3
    }

# Попытка удаления (ничего не произойдёт)
@router.delete("/delete")
async def delete_china_address(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_user)
):
    china_address = await ChinaAddress.get_instance(db)
    await china_address.delete(db)
    return {"message": "Удаление отключено, запись осталась без изменений"}