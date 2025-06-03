from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from auth.fastapi_users_instance import fastapi_users
from schemas.status import StatusCreate, StatusUpdate, StatusResponse
from services.status import StatusService
from config.database import get_async_session
from models.user import User

router = APIRouter(prefix="/statuses", tags=["statuses"])


# Create
@router.post("/", response_model=StatusResponse)
async def create_status(
    status: StatusCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    db_status = await StatusService.create_status(db, status)
    return db_status

# Read (one)
@router.get("/{status_id}", response_model=StatusResponse)
async def read_status(
    status_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    db_status = await StatusService.get_status(db, status_id)
    if db_status is None:
        raise HTTPException(status_code=404, detail="Status not found")
    return db_status

# Read (all)
@router.get("/", response_model=list[StatusResponse])
async def read_statuses(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    statuses = await StatusService.get_all_statuses(db, skip=skip, limit=limit)
    return statuses

# Update
@router.patch("/{status_id}", response_model=StatusResponse)
async def update_status(
    status_id: int,
    status: StatusUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    db_status = await StatusService.update_status(db, status_id, status)
    if db_status is None:
        raise HTTPException(status_code=404, detail="Status not found")
    return db_status

# Delete
@router.delete("/{status_id}")
async def delete_status(
    status_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    db_status = await StatusService.delete_status(db, status_id)
    if db_status is None:
        raise HTTPException(status_code=404, detail="Status not found")
    return {"message": "Status deleted successfully"}