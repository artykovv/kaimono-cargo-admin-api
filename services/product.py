# services/product_service.py
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from config.statuses import BaseStatus
from models import Product, Client, Status, ProductHistory
from sqlalchemy import func
from schemas.product import ProductCreate, ProductUpdate
from typing import Optional, List
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import selectinload

from services.product_history import ProductHistoryManager

class ProductService:
    @staticmethod
    async def create_product(db: AsyncSession, product_data: ProductCreate, user: dict) -> Product:
        try:
            # Преобразуем данные
            data = product_data.dict()

            # Находим клиента по client_code
            client_query = select(Client).filter(Client.code == product_data.client_code)
            client_result = await db.execute(client_query)
            client = client_result.scalars().first()
            if client is None:
                raise HTTPException(status_code=404, detail=f"Клиент с кодом '{product_data.client_code}' не найден")

            # Заменяем client_code на client_id и product_date на date
            data["client_id"] = client.id
            del data["client_code"]
            data["date"] = data["product_date"]
            del data["product_date"]

            

            # Находим статус.get("statu по status_id или status_name
            status_id = product_data.status_id
            if not status_id and hasattr(product_data, "status_name") and product_data.status_name:
                status_query = select(Status).filter(Status.name == product_data.status_name)
                status_result = await db.execute(status_query)
                status = status_result.scalars().first()
                if not status:
                    raise HTTPException(status_code=404, detail=f"Статус '{product_data.status_name}' не найден")
                status_id = status.id
            
            # Если статус не указан, используем "В Китае" по умолчанию
            if not status_id:
                status_query = select(Status).filter(Status.name == BaseStatus.CHINA)
                status_result = await db.execute(status_query)
                status = status_result.scalars().first()
                if not status:
                    raise HTTPException(status_code=404, detail="Статус 'В Китае' не найден")
                status_id = status.id
            
            data["status_id"] = status_id
            data["registered_at"] = datetime.now(timezone(timedelta(hours=6))).replace(tzinfo=None)

            # Создаем продукт
            db_product = Product(**data)
            
            # Устанавливаем даты в зависимости от статуса
            status_name = await ProductHistoryManager.get_status_name(db, status_id)
            ProductHistoryManager.apply_status_dates(db_product, status_name)
            
            db.add(db_product)
            await db.flush()  # Получаем ID продукта для записи в историю

            # Создаем запись в ProductHistory
            await ProductHistoryManager.log_action(
                db=db,
                product=db_product,
                action="created",
                user=user,
                client_code=client.code
            )

            await db.commit()
            await db.refresh(db_product)
            return db_product
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка при создании товара: {str(e)}")

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
    async def update_product(db: AsyncSession, product_id: int, product_data: ProductUpdate, user: dict) -> Optional[Product]:
        try:
            # Получаем товар
            db_product = await ProductService.get_product(db, product_id)
            if not db_product:
                raise HTTPException(status_code=404, detail="Товар не найден")
            
            # Сохраняем старые данные для описания изменений
            old_data = {
                "product_code": db_product.product_code,
                "weight": db_product.weight,
                "price": db_product.price,
                "client_id": db_product.client_id,
                "status_id": db_product.status_id,
                "date": db_product.date,
                "date_china": db_product.date_china,
                "date_transit": db_product.date_transit,
                "date_bishkek": db_product.date_bishkek,
                "take_time": db_product.take_time,
                "branch_id": db_product.branch_id
            }
            
            # Обновляем client_id, если указан client_code
            client_code = None
            if product_data.client_code:
                client_query = select(Client).filter(Client.code == product_data.client_code)
                client_result = await db.execute(client_query)
                client = client_result.scalars().first()
                if not client:
                    raise HTTPException(status_code=404, detail=f"Клиент с кодом '{product_data.client_code}' не найден")
                db_product.client_id = client.id
                client_code = client.code
            
            # Получаем данные для обновления
            update_data = product_data.dict(exclude_unset=True)
            if "take_time" in update_data and update_data["take_time"] and update_data["take_time"].tzinfo:
                update_data["take_time"] = update_data["take_time"].replace(tzinfo=None)
            
            # Проверяем статус, если он передан
            status_name = None
            if "status_id" in update_data:
                status_query = select(Status).filter(Status.id == update_data["status_id"])
                status_result = await db.execute(status_query)
                status = status_result.scalars().first()
                if not status:
                    raise HTTPException(status_code=404, detail=f"Статус с ID {update_data['status_id']} не найден")
                status_name = status.name
            elif hasattr(product_data, "status_name") and product_data.status_name:
                status_query = select(Status).filter(Status.name == product_data.status_name)
                status_result = await db.execute(status_query)
                status = status_result.scalars().first()
                if not status:
                    raise HTTPException(status_code=404, detail=f"Статус '{product_data.status_name}' не найден")
                update_data["status_id"] = status.id
                status_name = status.name
            else:
                status_name = await ProductHistoryManager.get_status_name(db, db_product.status_id)

            # Устанавливаем даты в зависимости от статуса
            ProductHistoryManager.apply_status_dates(db_product, status_name)

            # Обновляем остальные поля
            for key, value in update_data.items():
                setattr(db_product, key, value)
            
            # Логируем изменения
            new_data = {
                key: getattr(db_product, key) for key in old_data
            }
            await ProductHistoryManager.log_action(
                db=db,
                product=db_product,
                action="updated",
                user=user,
                client_code=client_code,
                old_data=old_data,
                new_data=new_data
            )
            
            await db.commit()
            await db.refresh(db_product)
            return db_product
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка при обновлении товара: {str(e)}")
    
    @staticmethod
    async def delete_product(db: AsyncSession, product_id: int) -> Optional[Product]:
        db_product = await ProductService.get_product(db, product_id)
        if not db_product:
            return None
        
        await db.delete(db_product)
        await db.commit()
        return db_product
    
    @staticmethod
    async def update_products_status(db: AsyncSession, product_ids: List[int], status_id: int, user: dict) -> List[Product]:
        try:
            # Получаем товары по ID
            query = select(Product).filter(Product.id.in_(product_ids))
            result = await db.execute(query)
            products = result.scalars().all()
            if not products:
                raise HTTPException(status_code=404, detail="Товары с указанными ID не найдены")

            # Проверяем существование статуса
            status_query = select(Status).filter(Status.id == status_id)
            status_result = await db.execute(status_query)
            status = status_result.scalars().first()
            if not status:
                raise HTTPException(status_code=404, detail=f"Статус с ID {status_id} не найден")
            status_name = status.name

            # Обновляем статус товаров и создаем записи в ProductHistory
            for product in products:
                # Сохраняем старые данные для истории
                old_data = {
                    "status_id": product.status_id,
                    "date_china": product.date_china,
                    "date_transit": product.date_transit,
                    "date_bishkek": product.date_bishkek,
                    "take_time": product.take_time
                }

                # Обновляем статус
                product.status_id = status_id
                
                # Устанавливаем даты через ProductHistoryManager
                ProductHistoryManager.apply_status_dates(product, status_name)
                
                db.add(product)
                await db.flush()  # Получаем изменения перед записью в историю

                # Логируем обновление
                new_data = {
                    "status_id": product.status_id,
                    "date_china": product.date_china,
                    "date_transit": product.date_transit,
                    "date_bishkek": product.date_bishkek,
                    "take_time": product.take_time
                }
                await ProductHistoryManager.log_action(
                    db=db,
                    product=product,
                    action="updated",
                    user=user,
                    old_data=old_data,
                    new_data=new_data
                )

            await db.commit()

            # Обновляем объекты для возврата
            for product in products:
                await db.refresh(product)

            return products
        except HTTPException as e:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка при обновлении статуса товаров: {str(e)}")
    

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