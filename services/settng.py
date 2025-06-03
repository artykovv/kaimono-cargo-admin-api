
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Configuration
from schemas.setting import ConfigurationBase

class SettingService:
    @staticmethod
    async def create_setting(db: AsyncSession, setting_data: ConfigurationBase):
        db_setting = Configuration(**setting_data.dict())
        db.add(db_setting)
        await db.commit()
        await db.refresh(db_setting)
        return db_setting
    
    @staticmethod
    async def get_setting(db: AsyncSession, setting_id: int):
        result = await db.execute(select(Configuration).filter(Configuration.id == setting_id))
        return result.scalars().first()
    
    @staticmethod
    async def get_all_settings(db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(Configuration).offset(skip).limit(limit))
        return result.scalars().all()
    
    @staticmethod
    async def update_setting(db: AsyncSession, setting_id: int, setting_data: ConfigurationBase):
        setting = await SettingService.get_setting(db, setting_id)
        if not setting:
            return None
        
        update_data = setting_data.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(setting, key, value)
        
        await db.commit()
        await db.refresh(setting)
        return setting
    