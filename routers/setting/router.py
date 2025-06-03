from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from auth.fastapi_users_instance import fastapi_users
from schemas.setting import ConfigurationResponse, ConfigurationBase, ConfigurationUpdate
from services.settng import SettingService
from config.database import get_async_session
from models import Configuration, User

router = APIRouter(prefix="/settings", tags=["setting"])

@router.post("/")
async def create_setting(
    setting: ConfigurationBase, 
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    setting = await SettingService.create_setting(db, setting)
    return setting


# Read (one)
@router.get("/{setting_id}")
async def read_branch(
    setting_id: int, 
    db: AsyncSession = Depends(get_async_session), 
    current_user: User = Depends(fastapi_users.current_user())
):
    setting = await SettingService.get_setting(db, setting_id)
    if setting is None:
        raise HTTPException(status_code=404, detail="Config not found")
    return setting

@router.get("/")
async def get_all_settings(
    skip: int = 0, 
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session), 
    current_user: User = Depends(fastapi_users.current_user())
):
    settings = await SettingService.get_all_settings(db, skip, limit)
    return settings

@router.patch("/{setting_id}")
async def read_branch(
    setting_id: int, 
    setting: ConfigurationUpdate,
    db: AsyncSession = Depends(get_async_session), 
    current_user: User = Depends(fastapi_users.current_user())
):
    setting_update = await SettingService.update_setting(db, setting_id, setting)
    if setting_update is None:
        raise HTTPException(status_code=404, detail="Config not found")
    return setting_update

