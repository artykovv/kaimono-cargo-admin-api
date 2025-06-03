# services/product_service.py
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Product, Client, Status
from sqlalchemy import func
from schemas.product import ProductCreate, ProductUpdate
from typing import Optional, List
from datetime import date, datetime
from sqlalchemy.orm import selectinload

class ProductService:
    @staticmethod
    async def create_product(db: AsyncSession, product_data: ProductCreate) -> Product:
        try:
            # Преобразуем данные
            data = product_data.dict()

            # Находим клиента по client_code
            client_query = select(Client).filter(Client.code == product_data.client_code)
            client_result = await db.execute(client_query)
            client = client_result.scalars().first()
            
            if client is None:
                # raise ValueError(f"Клиент с кодом '{product_data.client_code}' не найден")
                raise HTTPException(status_code=404, detail="Клиент не найден")

            # Заменяем client_code на client_id в данных
            data["client_id"] = client.id
            del data["client_code"]
            data["date"] = data["product_date"]
            del data["product_date"]

            # Создаём продукт
            db_product = Product(**data)
            db.add(db_product)
            await db.commit()
            await db.refresh(db_product)
            return db_product
        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    async def get_product(db: AsyncSession, product_id: int) -> Optional[Product]:
        result = await db.execute(
            select(Product)
            .options(
                selectinload(Product.client),
                selectinload(Product.status)

            )
            .where(Product.id == product_id)
        )
        return result.scalars().first()

    @staticmethod
    async def get_products(
        db: AsyncSession,
        user_branches: List[int],
        search_query: str = "",
        status_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 30,
    ) -> dict:
        # Базовый запрос
        query = (
            select(Product)
            .options(selectinload(Product.status), selectinload(Product.client))
            .filter(Product.status_id != None)  # Предполагаем, что BaseStatus.PIKED заменяется на конкретный ID
            .order_by(Product.id.desc())
        )
        # Ограничение по филиалам пользователя (если не суперпользователь)
        if user_branches:
            query = query.filter(Product.branch_id.in_(user_branches))

        # Фильтрация по поисковому запросу
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                (Product.product_code.ilike(search_pattern)) |
                (Product.status.has(Status.name.ilike(search_pattern))) |
                (Product.client.has(Client.name.ilike(search_pattern)))
            )

        # Фильтрация по статусу
        if status_id is not None:
            query = query.filter(Product.status_id == status_id)

        # Фильтрация по датам
        if start_date:
            query = query.filter(Product.date >= start_date)
        if end_date:
            query = query.filter(Product.date <= end_date)

        # Подсчет общего количества записей
        total_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(total_query)
        total_products = total.scalar()

        # Пагинация
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)
        products = result.scalars().all()

        # Получение всех статусов (без кэширования пока)
        statuses = await db.execute(select(Status))
        statuses = statuses.scalars().all()

        return {
            "products": products,
            "total": total_products,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_products + page_size - 1) // page_size,
            "statuses": statuses
        }

    @staticmethod
    async def get_user_products(db: AsyncSession, user_branches: List[int], skip: int = 0, limit: int = 100) -> List[Product]:
        result = await db.execute(
            select(Product)
            .filter(Product.branch_id.in_(user_branches))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def update_product(db: AsyncSession, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        db_product = await ProductService.get_product(db, product_id)
        if not db_product:
            return None
        
        if product_data.client_code:
            # Находим клиента по client_code
            client_query = select(Client).filter(Client.code == product_data.client_code)
            client_result = await db.execute(client_query)
            client = client_result.scalars().first()

            if not client:
                return None
            
            db_product.client_id = client.id
        
        update_data = product_data.dict(exclude_unset=True)
        if "take_time" in update_data and update_data["take_time"].tzinfo:
            update_data["take_time"] = update_data["take_time"].replace(tzinfo=None)
        
        for key, value in update_data.items():
            setattr(db_product, key, value)
        
        await db.commit()
        await db.refresh(db_product)
        return db_product

    @staticmethod
    async def delete_product(db: AsyncSession, product_id: int) -> Optional[Product]:
        db_product = await ProductService.get_product(db, product_id)
        if not db_product:
            return None
        
        await db.delete(db_product)
        await db.commit()
        return db_product
    
    @staticmethod
    async def update_products_status(db: AsyncSession, product_ids: List[int], status_id: int) -> List[Product]:
        query = select(Product).filter(Product.id.in_(product_ids))
        result = await db.execute(query)
        products = result.scalars().all()

        if not products:
            raise ValueError("Товары с указанными ID не найдены")

        for product in products:
            product.status_id = status_id
            db.add(product)

        await db.commit()
        for product in products:
            await db.refresh(product)
        
        return products
    

    @staticmethod
    async def delete_products(db: AsyncSession, product_ids: List[int]) -> int:
        query = select(Product).filter(Product.id.in_(product_ids))
        result = await db.execute(query)
        products = result.scalars().all()

        if not products:
            raise ValueError("Товары с указанными ID не найдены")

        deleted_count = 0
        for product in products:
            await db.delete(product)
            deleted_count += 1

        await db.commit()
        return deleted_count