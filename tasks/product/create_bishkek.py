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
from tasks.notification.bihskek import notification_bishkek

async def process_bishkek_products(file_content: bytes, db: AsyncSession, user: dict):
    try:
        workbook = openpyxl.load_workbook(BytesIO(file_content))
        sheet = workbook.active

        products_created = 0
        products_updated = 0
        clients_products_count = {}

        # Получаем статус "BISHKEK"
        bishkek_status_query = select(Status).filter(Status.name == BaseStatus.BISHKEK)
        bishkek_status_result = await db.execute(bishkek_status_query)
        bishkek_status = bishkek_status_result.scalars().first()
        if not bishkek_status:
            raise HTTPException(status_code=404, detail="Статус 'BISHKEK' не найден")

        for row in sheet.iter_rows(min_row=2, values_only=True):
            if len(row) < 2 or not row[0] or not row[2]:  # Проверяем наличие product_code и weight
                continue

            product_code = str(row[0]).strip()
            client_id = row[1] if len(row) > 1 else None
            weight = row[2]
            price = row[3] if len(row) > 3 else None

            client = None
            client_code = None
            if client_id:
                if isinstance(client_id, float):
                    client_id = int(client_id)
                else:
                    client_id = int(str(client_id).strip())

                query = select(Client).filter(Client.numeric_code == client_id)
                result = await db.execute(query)
                client = result.scalars().first()
                if client:
                    client_code = client.code

            # Проверяем, существует ли продукт по product_code
            query = select(Product).filter(Product.product_code == product_code)
            result = await db.execute(query)
            product = result.scalars().first()

            if product:
                # Сохраняем старые данные для истории
                old_data = {
                    "product_code": product.product_code,
                    "weight": product.weight,
                    "price": product.price,
                    "client_id": product.client_id,
                    "status_id": product.status_id,
                    "date": product.date,
                    "date_bishkek": product.date_bishkek
                }

                # Обновляем существующий продукт
                product.weight = weight
                product.status_id = bishkek_status.id
                product.date = datetime.now(timezone(timedelta(hours=6))).date()
                if client:
                    product.client_id = client.id
                if price is not None:
                    product.price = price
                
                # Устанавливаем даты через ProductHistoryManager
                ProductHistoryManager.apply_status_dates(product, BaseStatus.BISHKEK)
                
                db.add(product)
                await db.flush()  # Получаем ID для записи в историю

                # Логируем обновление
                new_data = {
                    "product_code": product.product_code,
                    "weight": product.weight,
                    "price": product.price,
                    "client_id": product.client_id,
                    "status_id": product.status_id,
                    "date": product.date,
                    "date_bishkek": product.date_bishkek
                }
                await ProductHistoryManager.log_action(
                    db=db,
                    product=product,
                    action="updated",
                    user=user,
                    client_code=client_code,
                    old_data=old_data,
                    new_data=new_data
                )
                products_updated += 1
            else:
                # Создаем новый продукт
                product = Product(
                    product_code=product_code,
                    client_id=client.id if client else None,
                    weight=weight,
                    price=price,
                    date=datetime.now(timezone(timedelta(hours=6))).date(),
                    status_id=bishkek_status.id,
                    branch_id=client.branch_id if client else None
                )
                
                # Устанавливаем даты через ProductHistoryManager
                ProductHistoryManager.apply_status_dates(product, BaseStatus.BISHKEK)
                
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
            asyncio.create_task(notification_bishkek(db=db, data=clients_products_count))

        return {
            "products_created": products_created,
            "products_updated": products_updated,
            "clients_products_count": clients_products_count
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке файла: {str(e)}")