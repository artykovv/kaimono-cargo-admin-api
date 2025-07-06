from fastapi import APIRouter, File, UploadFile, Depends
from typing import List
from auth.fastapi_users_instance import fastapi_users
from .s3 import S3Client
from config.config import ACCESS_KEY, SECRET_KEY, ENDPOINT_URL, BUCKET_NAME
from models import User
import aiofiles
import uuid
import asyncio
import os

router = APIRouter(prefix="/storage", tags=["storage"])

s3_client = S3Client(
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    endpoint_url=ENDPOINT_URL,
    bucket_name=BUCKET_NAME,
)

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...), 
    current_user: User = Depends(fastapi_users.current_user(superuser=True))
):
    async def process_file(file: UploadFile):
        temp_filename = f"temp_{uuid.uuid4()}_{file.filename}"
        async with aiofiles.open(temp_filename, "wb") as w:
            while chunk := await file.read(1024 * 1024):
                await w.write(chunk)

        url = await s3_client.upload_file(temp_filename, folder="kaimono/cargo/docs")
        return url

    uploaded_urls = await asyncio.gather(*[process_file(f) for f in files])
    return {"uploaded_urls": uploaded_urls}