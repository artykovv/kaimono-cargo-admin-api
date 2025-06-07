from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Text
from schemas.text import TextBase, TextCreate, TextUpdate

class TextServices:

    async def all(
        session: AsyncSession
    ):
        query = select(Text)
        result = await session.execute(query)
        textes = result.scalars().all()
        if not textes:
            raise HTTPException(status_code=404, detail="Не найдено")
        return textes

    async def get(
        text_id: int,
        session: AsyncSession
    ):
        query = select(Text).where(Text.id == text_id)
        result = await session.execute(query)
        text = result.scalars().first()
        if not text:
            raise HTTPException(status_code=404, detail="Не найдено")
        return text
    
    async def key(
        key: str,
        session: AsyncSession
    ):
        query = select(Text).where(Text.key == key)
        result = await session.execute(query)
        text = result.scalars().first()
        if not text:
            raise HTTPException(status_code=404, detail="Не найдено")
        return text

    async def create(
        data: dict,
        session: AsyncSession
    ):
        text = Text(**data.dict())
        session.add(text)
        await session.commit()
        await session.refresh(text)
        return text

    async def update(
        text_id: int,
        data: dict,
        session: AsyncSession
    ):
        query = select(Text).where(Text.id == text_id)
        result = await session.execute(query)
        text = result.scalars().first()

        if not text:
            return None
        
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(text, key, value)
        
        await session.commit()
        await session.refresh(text)
        return text

    async def delete(
        text_id: int
    ):
        pass