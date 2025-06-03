from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from auth.fastapi_users_instance import fastapi_users
from schemas.client import ClientCreate, ClientUpdate, ClientResponse, PaginatedClientsResponse, ClientDataResponse
from services.client import ClientService
from config.database import get_async_session
from models import User, Client, Product
from typing import Optional
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/clients", tags=["clients"])

# Create
@router.post("/", response_model=ClientResponse)
async def create_client(
    client: ClientCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    db_client = await ClientService.create_client(db, client)
    return db_client

# Read (one)
@router.get("/{client_id}", response_model=ClientResponse)
async def read_client(
    client_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    db_client = await ClientService.get_client(db, client_id)
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client

# Read (all)
@router.get("/", response_model=PaginatedClientsResponse)
async def read_clients(
    search: str = Query("", description="Поиск по имени, номеру или коду"),
    # branch_id: Optional[int] = Query(None, description="Фильтр по ID филиала"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(30, ge=1, le=100, description="Количество записей на странице"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    # Определяем филиалы пользователя
    user_branches = [] if current_user.is_superuser else [b.id for b in current_user.branches]

    # Получаем клиентов с фильтрацией и пагинацией
    result = await ClientService.get_all_clients(
        db=db,
        user_branches=user_branches,
        search_query=search,
        page=page,
        page_size=page_size,
    )
    
    return result

# Update
@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client: ClientUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    db_client = await ClientService.update_client(db, client_id, client)
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client

# Delete
@router.delete("/{client_id}")
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    db_client = await ClientService.delete_client(db, client_id)
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted successfully"}

@router.get("/{client_id}/data")
async def read_client(
    client_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    # Запрос с загрузкой связанных товаров
    query = (
        select(Client)
        .options(
            selectinload(Client.products)
        )  # Загружаем все товары клиента
        .filter(Client.id == client_id)
    )
    result = await db.execute(query)
    client = result.scalars().first()

    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")


    return client


