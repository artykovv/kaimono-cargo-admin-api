from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config.config import Base  # Предполагается, что у вас есть базовая модель Base

class ChinaAddress(Base):
    __tablename__ = 'china_address'

    id = Column(Integer, primary_key=True)
    name1 = Column(String(500), nullable=False)
    name2 = Column(String(500), nullable=False)
    name3 = Column(String(500), nullable=False)

    async def save(self, db: AsyncSession):
        """Сохраняет объект с фиксированным id=1"""
        self.id = 1  # Всегда используем один и тот же первичный ключ
        db.add(self)
        await db.commit()
        await db.refresh(self)

    async def delete(self, db: AsyncSession):
        """Отключаем удаление"""
        pass  # Ничего не делаем, чтобы нельзя было удалить запись

    @classmethod
    async def get_instance(cls, db: AsyncSession):
        """Получает или создаёт единственный экземпляр с id=1"""
        query = select(cls).where(cls.id == 1)
        result = await db.execute(query)
        obj = result.scalars().first()
        if not obj:
            obj = cls(name1="", name2="", name3="")  # Значения по умолчанию
            obj.id = 1
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
        return obj