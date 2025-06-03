# services/status_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.status import Status
from schemas.status import StatusCreate, StatusUpdate
from typing import Optional, List

class StatusService:
    @staticmethod
    async def create_status(db: AsyncSession, status_data: StatusCreate) -> Status:
        db_status = Status(**status_data.dict())
        db.add(db_status)
        await db.commit()
        await db.refresh(db_status)
        return db_status

    @staticmethod
    async def get_status(db: AsyncSession, status_id: int) -> Optional[Status]:
        result = await db.execute(
            select(Status).filter(Status.id == status_id)
        )
        return result.scalars().first()

    @staticmethod
    async def get_all_statuses(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Status]:
        result = await db.execute(
            select(Status).offset(skip).limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def update_status(db: AsyncSession, status_id: int, status_data: StatusUpdate) -> Optional[Status]:
        db_status = await StatusService.get_status(db, status_id)
        if not db_status:
            return None
        
        update_data = status_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_status, key, value)
        
        await db.commit()
        await db.refresh(db_status)
        return db_status

    @staticmethod
    async def delete_status(db: AsyncSession, status_id: int) -> Optional[Status]:
        db_status = await StatusService.get_status(db, status_id)
        if not db_status:
            return None
        
        await db.delete(db_status)
        await db.commit()
        return db_status