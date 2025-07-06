from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from config.database import get_async_session
from auth.fastapi_users_instance import fastapi_users

from models import User, AddressPhoto, AddressVideo
from schemas.address_file import (
    AddressPhotoCreate, AddressPhotoRead, AddressPhotoUpdate,
    AddressVideoCreate, AddressVideoRead, AddressVideoUpdate
)
router = APIRouter(prefix="/address-file", tags=["address-file"])

# --------------------- PHOTO ---------------------

@router.post("/photo", response_model=AddressPhotoRead)
async def create_photo(
    data: AddressPhotoCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    obj = AddressPhoto(**data.dict())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/photo", response_model=list[AddressPhotoRead])
async def list_photos(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    result = await db.execute(select(AddressPhoto))
    return result.scalars().all()


@router.get("/photo/{photo_id}", response_model=AddressPhotoRead)
async def get_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    result = await db.execute(select(AddressPhoto).where(AddressPhoto.id == photo_id))
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@router.delete("/photo/{photo_id}")
async def delete_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    result = await db.execute(select(AddressPhoto).where(AddressPhoto.id == photo_id))
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    await db.delete(photo)
    await db.commit()
    return {"detail": "Photo deleted"}

@router.put("/photo/{photo_id}", response_model=AddressPhotoRead)
async def update_photo(
    photo_id: int,
    data: AddressPhotoUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    result = await db.execute(select(AddressPhoto).where(AddressPhoto.id == photo_id))
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    for field, value in data.dict(exclude_unset=True).items():
        setattr(photo, field, value)

    await db.commit()
    await db.refresh(photo)
    return photo

# --------------------- VIDEO ---------------------

@router.post("/video", response_model=AddressVideoRead)
async def create_video(
    data: AddressVideoCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    obj = AddressVideo(**data.dict())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/video", response_model=list[AddressVideoRead])
async def list_videos(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    result = await db.execute(select(AddressVideo))
    return result.scalars().all()


@router.get("/video/{video_id}", response_model=AddressVideoRead)
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    result = await db.execute(select(AddressVideo).where(AddressVideo.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.delete("/video/{video_id}")
async def delete_video(
    video_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    result = await db.execute(select(AddressVideo).where(AddressVideo.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    await db.delete(video)
    await db.commit()
    return {"detail": "Video deleted"}

@router.put("/video/{video_id}", response_model=AddressVideoRead)
async def update_video(
    video_id: int,
    data: AddressVideoUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user(verified=True))
):
    result = await db.execute(select(AddressVideo).where(AddressVideo.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    for field, value in data.dict(exclude_unset=True).items():
        setattr(video, field, value)

    await db.commit()
    await db.refresh(video)
    return video