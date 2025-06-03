# routers/product.py
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from auth.fastapi_users_instance import fastapi_users
from schemas.product import ProductCreate, ProductUpdate, ProductResponse, PaginatedProductsResponse, BulkRequest
from services.product import ProductService
from config.database import get_async_session
from models import User, Product
from typing import Optional, List
from datetime import date
from sqlalchemy import select
from fastapi import Form
from sqlalchemy.orm import selectinload

from tasks.product.create_china import process_china_products
from tasks.product.create_bishkek import process_bishkek_products

router = APIRouter(prefix="/products", tags=["products"])



# Create
@router.post("/")
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    db_product = await ProductService.create_product(db, product, current_user)
    return db_product

# Read (one)
@router.get("/{product_id}", response_model=ProductResponse)
async def read_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    db_product = await ProductService.get_product(db, product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

# Read (all)
@router.get("/", response_model=PaginatedProductsResponse)
async def read_products(
    search: str = Query("", description="Поиск по коду товара, статусу или имени клиента"),
    status_id: Optional[int] = Query(None, description="Фильтр по ID статуса"),
    start_date: Optional[date] = Query(None, description="Начальная дата (гггг-мм-дд)"),
    end_date: Optional[date] = Query(None, description="Конечная дата (гггг-мм-дд)"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(30, ge=1, le=100, description="Количество записей на странице"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    user_branches = [] if current_user.is_superuser else [b.id for b in current_user.branches]
    result = await ProductService.get_products(
        db=db,
        user_branches=user_branches,
        search_query=search,
        status_id=status_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return result

# Update
@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product: ProductUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    db_product = await ProductService.update_product(db, product_id, product, current_user)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

# Delete
@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    db_product = await ProductService.delete_product(db, product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}


# API маршрут для массового обновления статуса товаров
@router.post("/update")
async def update_products(
    request: BulkRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    if not request.product_ids:
        raise HTTPException(status_code=400, detail="Не указаны ID товаров")
    if request.status_id is None:
        raise HTTPException(status_code=400, detail="Не указан статус для обновления")

    try:
        updated_products = await ProductService.update_products_status(db, request.product_ids, request.status_id, current_user)
        return {"message": f"Успешно обновлено {len(updated_products)} товаров"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
# API маршрут для массового удаления товаров
@router.post("/delete")
async def delete_products(
    product_ids: List[int] = Form(...),  # Принимаем product_ids как список из FormData
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    if not product_ids:
        raise HTTPException(status_code=400, detail="Не указаны ID товаров")

    try:
        deleted_count = await ProductService.delete_products(db, product_ids)
        return {"message": f"Успешно удалено {deleted_count} товаров"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

@router.post("/ids")
async def get_products_from_ids(
    request: BulkRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    if not request.product_ids:
        raise HTTPException(status_code=400, detail="Не указаны ID товаров")
    
    query = (
        select(Product)
        .where(Product.id.in_(request.product_ids))
        .options(
            selectinload(Product.status),
            selectinload(Product.client),
            selectinload(Product.branch),
            selectinload(Product.payments)
        )
    )
    
    result = await db.execute(query)
    products = result.scalars().all()
    
    return products




@router.post("/process-china")
async def process_china(
    file_content: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    user_id = str(current_user.id)  # Получаем ID текущего пользователя
    file_data = await file_content.read()  # Читаем содержимое файла в байтах
    
    # Запускаем обработку файла асинхронно
    # task = asyncio.create_task(process_china_products(file_data, db, user_id))
    task = await process_china_products(file_data, db, current_user)

    return task

@router.post("/process-bishkek")
async def process_bishkek(
    file_content: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    user_id = str(current_user.id)  # Получаем ID текущего пользователя
    file_data = await file_content.read()  # Читаем содержимое файла в байтах
    
    # Запускаем обработку файла асинхронно
    # task = asyncio.create_task(process_bishkek_products(file_data, db, current_user))
    task = await process_bishkek_products(file_data, db, current_user)

    return task