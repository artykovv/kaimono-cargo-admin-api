import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Product, Client, Status
import openpyxl
from io import BytesIO
from datetime import datetime
from config.statuses import BaseStatus
from tasks.notification.bihskek import notification_bishkek

# Асинхронная обработка файла для Бишкека
async def process_bishkek_products(file_content: bytes, db: AsyncSession):
    try:
        workbook = openpyxl.load_workbook(BytesIO(file_content))
        sheet = workbook.active

        products_created = 0
        products_updated = 0
        clients_products_count = {}

        for row in sheet.iter_rows(min_row=2, values_only=True):
            if len(row) < 2 or not row[0] or not row[2]:  # Проверяем наличие product_code и weight
                continue

            product_code = str(row[0]).strip()
            client_id = row[1] if len(row) > 1 else None
            weight = row[2]
            price = row[3] if len(row) > 3 else None

            client = None
            if client_id:
                if isinstance(client_id, float):
                    client_id = int(client_id)
                else:
                    client_id = int(str(client_id).strip())

                query = select(Client).filter(Client.numeric_code == client_id)
                result = await db.execute(query)
                client = result.scalars().first()

            bishkek_status_query = select(Status).filter(Status.name == BaseStatus.BISHKEK)
            bishkek_status_result = await db.execute(bishkek_status_query)
            bishkek_status = bishkek_status_result.scalars().first()

            # Проверяем, существует ли продукт только по product_code
            query = select(Product).filter(Product.product_code == product_code)
            result = await db.execute(query)
            product = result.scalars().first()

            if product:
                # Обновляем существующий продукт
                product.weight = weight
                product.status_id = bishkek_status.id
                product.date = datetime.utcnow().date()
                if client:
                    product.client_id = client.id  # Обновляем client_id, если он пришел
                if price is not None:
                    product.price = price
                db.add(product)
                products_updated += 1
            else:
                # Создаем новый продукт
                product = Product(
                    product_code=product_code,
                    client_id=client.id if client else None,
                    weight=weight,
                    price=price,
                    date=datetime.utcnow().date(),
                    status_id=bishkek_status.id,
                    branch_id=client.branch_id if client else None
                )
                db.add(product)
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
        return {"error": str(e)}