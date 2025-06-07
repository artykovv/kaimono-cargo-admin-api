from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth.fastapi_users_instance import fastapi_users
from config.database import get_async_session
from services.text import TextServices
from schemas.text import TextBase, TextCreate, TextUpdate, TextResponse

from models import User

router = APIRouter(prefix="/textes", tags=["textes"])

@router.get("/", response_model=List[TextResponse])
async def textes_all(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    textes = await TextServices.all(session=session)
    return textes

@router.get("/{text_id}", response_model=TextResponse)
async def text_by_id(
    text_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    text = await TextServices.get(text_id=text_id, session=session)
    return text

@router.get("/{key}", response_model=TextResponse)
async def text_by_key(
    key: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    text = await TextServices.key(key=key, session=session)
    return text


@router.post("/", response_model=TextResponse)
async def creaate_text(
    text_date: TextCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    text = await TextServices.create(data=text_date, session=session)
    return text

@router.put("/{text_id}", response_model=TextResponse)
async def update_text(
    text_id: int,
    text_data: TextUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user())
):
    text = await TextServices.update(text_id=text_id, data=text_data, session=session)
    return text

# @router.delete("/{text_id}", response_model=TextResponse)
# async def delete_text(
#     text_id: int,
#     session: AsyncSession = Depends(get_async_session),
#     current_user: User = Depends(fastapi_users.current_user())
# ):
#     delete = await TextServices.delete(text_id)
#     return delete