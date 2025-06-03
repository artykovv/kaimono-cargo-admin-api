import asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Product, Client, Status, ProductHistory
import openpyxl
from io import BytesIO
from datetime import datetime, timedelta, timezone
from config.statuses import BaseStatus
from services.product_history import ProductHistoryManager
from tasks.notification.china import notification_china

# Асинхронная обработка файла
async def process_china_products(file_content: bytes, db: AsyncSession, user: dict):
    try:
        workbook = openpyxl.load_workbook(BytesIO(file_content))
        sheet = workbook.active

        products_created = 0
        products_skipped = 0
        clients_products_count = {}

        # Получаем статус "CHINA"
        china_status_query = select(Status).filter(Status.name == BaseStatus.CHINA)
        china_status_result = await db.execute(china_status_query)
        china_status = china_status_result.scalars().first()
        if not china_status:
            raise HTTPException(status_code=404, detail="Статус 'CHINA' не найден")

        for row in sheet.iter_rows(min_row=2, values_only=True):
            if len(row) < 1 or not row[0]:
                continue

            product_code = str(row[0]).strip()
            client_id = None
            client = None
            client_code = None

            if len(row) >= 2 and row[1] is not None:
                client_id = row[1]
                if isinstance(client_id, float):
                    client_id = int(client_id)
                else:
                    client_id = int(str(client_id).strip())

                query = select(Client).filter(Client.numeric_code == client_id)
                result = await db.execute(query)
                client = result.scalars().first()
                if client:
                    client_code = client.code

            # Проверяем, существует ли продукт
            exists_query = select(Product).filter(Product.product_code == product_code)
            if client:
                exists_query = exists_query.filter(Product.client_id == client.id)
            else:
                exists_query = exists_query.filter(Product.client_id == None)
            exists_result = await db.execute(exists_query)
            if exists_result.scalars().first():
                products_skipped += 1
                continue

            # Создаем новый продукт
            product = Product(
                product_code=product_code,
                client_id=client.id if client else None,
                date=datetime.now(timezone(timedelta(hours=6))).date(),
                status_id=china_status.id,
                branch_id=client.branch_id if client else None,
                registered_at=datetime.now(timezone(timedelta(hours=6))).replace(tzinfo=None)
            )
            
            # Устанавливаем даты через ProductHistoryManager
            ProductHistoryManager.apply_status_dates(product, BaseStatus.CHINA)
            
            db.add(product)
            await db.flush()  # Получаем ID для записи в историю

            # Логируем создание
            await ProductHistoryManager.log_action(
                db=db,
                product=product,
                action="created",
                user=user,
                client_code=client_code
            )

            products_created += 1

            if client:
                clients_products_count[client.telegram_chat_id] = clients_products_count.get(client.telegram_chat_id, 0) + 1

        await db.commit()

        if clients_products_count:
            asyncio.create_task(notification_china(db=db, data=clients_products_count))

        return {
            "products_created": products_created,
            "products_skipped": products_skipped,
            "clients_products_count": clients_products_count
        }
    except HTTPException as e:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке файла: {str(e)}")