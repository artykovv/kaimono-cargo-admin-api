# services/client_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func as sql_func
from models import Client, Branch
from schemas.client import ClientCreate, ClientUpdate
from typing import Optional, List

class ClientService:
    @staticmethod
    async def create_client(db: AsyncSession, client_data: ClientCreate) -> Client:
        # Создаем клиента
        db_client = Client(
            name=client_data.name,
            number=client_data.number,
            city=client_data.city,
            telegram_chat_id=client_data.telegram_chat_id,
            branch_id=client_data.branch_id,
        )
        
        # Генерация numeric_code
        if not db_client.numeric_code:
            last_numeric = await db.execute(
                select(sql_func.max(Client.numeric_code))
            )
            db_client.numeric_code = (last_numeric.scalar() or 0) + 1
        
        # Формирование code на основе branch.code
        if db_client.branch_id:
            branch = await db.execute(
                select(Branch).filter(Branch.id == db_client.branch_id)
            )
            branch = branch.scalars().first()
            if branch:
                db_client.code = f"{branch.code}{db_client.numeric_code}"
        
        db.add(db_client)
        await db.commit()
        await db.refresh(db_client)
        return db_client

    @staticmethod
    async def get_client(db: AsyncSession, client_id: int) -> Optional[Client]:
        result = await db.execute(
            select(Client)
            .filter(Client.id == client_id)
        )
        return result.scalars().first()

    @staticmethod
    async def get_all_clients(
        db: AsyncSession,
        user_branches: List[int],
        search_query: str = "",
        branch_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 30,
    )-> dict:
        # Базовый запрос
        query = select(Client).order_by(desc(Client.id))

        # Ограничение по филиалам пользователя (если не суперпользователь)
        if branch_id is not None:
            query = query.filter(Client.branch_id == branch_id)
            
        # Фильтрация по поисковому запросу
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                (Client.name.ilike(search_pattern)) |
                (Client.number.ilike(search_pattern)) |
                (Client.code.ilike(search_pattern))
            )

        # Подсчет общего количества записей
        total_query = select(sql_func.count()).select_from(query.subquery())
        total = await db.execute(total_query)
        total_clients = total.scalar()

        # Пагинация
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)
        clients = result.scalars().all()

        # Формируем ответ с метаинформацией
        return {
            "clients": clients,
            "total": total_clients,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_clients + page_size - 1) // page_size
        }
    

    @staticmethod
    async def update_client(db: AsyncSession, client_id: int, client_data: ClientUpdate) -> Optional[Client]:
        db_client = await ClientService.get_client(db, client_id)
        if not db_client:
            return None
        
        update_data = client_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_client, key, value)
        
        # Пересчитываем code, если изменился branch_id
        if "branch_id" in update_data:
            if db_client.branch_id:
                branch = await db.execute(
                    select(Branch).filter(Branch.id == db_client.branch_id)
                )
                branch = branch.scalars().first()
                db_client.code = f"{branch.code}{db_client.numeric_code}" if branch else None
            else:
                db_client.code = None
        
        await db.commit()
        await db.refresh(db_client)
        return db_client

    @staticmethod
    async def delete_client(db: AsyncSession, client_id: int) -> Optional[Client]:
        db_client = await ClientService.get_client(db, client_id)
        if not db_client:
            return None
        
        await db.delete(db_client)
        await db.commit()
        return db_client