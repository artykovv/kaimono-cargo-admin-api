import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Product, Client, Status
import openpyxl
from io import BytesIO
from datetime import datetime
from config.statuses import BaseStatus
from tasks.notification.china import notification_china

# Асинхронная обработка файла
async def process_china_products(file_content: bytes, db: AsyncSession):
    try:
        workbook = openpyxl.load_workbook(BytesIO(file_content))
        sheet = workbook.active

        products_created = 0
        products_skipped = 0
        clients_products_count = {}

        for row in sheet.iter_rows(min_row=2, values_only=True):
            if len(row) < 1 or not row[0]:
                continue

            product_code = str(row[0]).strip()
            client_id = None
            client = None

            if len(row) >= 2 and row[1] is not None:
                client_id = row[1]
                if isinstance(client_id, float):
                    client_id = int(client_id)
                else:
                    client_id = int(str(client_id).strip())

                query = select(Client).filter(Client.numeric_code == client_id)
                result = await db.execute(query)
                client = result.scalars().first()

            china_status_query = select(Status).filter(Status.name == BaseStatus.CHINA)
            china_status_result = await db.execute(china_status_query)
            china_status = china_status_result.scalars().first()
            

            exists_query = select(Product).filter(Product.product_code == product_code)
            if client:
                exists_query = exists_query.filter(Product.client_id == client.id)
            else:
                exists_query = exists_query.filter(Product.client_id == None)
            exists_result = await db.execute(exists_query)
            if exists_result.scalars().first():
                products_skipped += 1
                continue

            product = Product(
                product_code=product_code,
                client_id=client.id if client else None,
                date=datetime.utcnow(),
                status_id=china_status.id,
                branch_id=client.branch_id if client else None
            )
            db.add(product)
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
    except Exception as e:
        return {"error": str(e)}