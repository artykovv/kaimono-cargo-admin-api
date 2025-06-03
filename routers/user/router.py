from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from auth.fastapi_users_instance import fastapi_users
from auth.auth import auth_backend
from schemas.user import UserRead, UserCreate, UserUpdate
from services.user import UserService
from config.database import get_async_session
from models import User
from uuid import UUID

from auth.fastapi_users_instance import fastapi_users
from auth.auth import auth_backend

from schemas.user import UserRead, UserCreate

router = APIRouter()

router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

@router.get("/auth/validate-token", tags=["auth"])
async def validate_token(current_user: User = Depends(fastapi_users.current_user())):
    return {
        "message": "Token is valid", 
        # "user_id": current_user
    }


@router.get("/user/{user_id}", tags=["user"], response_model=UserRead)
async def read_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    db_user = await UserService.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Ограничение: пользователь видит только себя или суперпользователь видит всех
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Forbidden")
    return db_user

@router.get("/users/", tags=["user"], response_model=list[UserRead])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    users = await UserService.get_all_users(db, skip=skip, limit=limit)
    return users

@router.patch("/user/{user_id}", tags=["user"], response_model=UserRead)
async def update_user(
    user_id: UUID,
    user: UserUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    db_user = await UserService.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Ограничение: пользователь обновляет только себя или суперпользователь обновляет всех
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated_user = await UserService.update_user(db, user_id, user)
    return updated_user

@router.delete("/user/{user_id}", tags=["user"])
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    db_user = await UserService.delete_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}