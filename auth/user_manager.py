# auth/user_manager.py
from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from sqlalchemy import select, UUID
from sqlalchemy.orm import selectinload
from models.user import User
from config.config import SECRET
from config.database import async_session_maker
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import get_async_session


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def get(self, user_id: UUID) -> Optional[User]:
        async with async_session_maker() as session:
            result = await session.execute(
                select(User)
                .options(
                    selectinload(User.branches),  # Подгружаем связанные филиалы
                )
                .where(User.id == user_id)
            )
            user = result.scalars().first()
            await session.commit()
            return user

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        pass

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)