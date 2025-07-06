import os
import aiofiles
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from aiobotocore.config import AioConfig
from contextlib import asynccontextmanager

class S3Client:
    def __init__(self, access_key, secret_key, endpoint_url, bucket_name):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
            "use_ssl": False,
        }
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self.session = get_session()
        self.aio_config = AioConfig(max_pool_connections=50)  # Увеличение одновременных подключений

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client(
            "s3",
            region_name="ru-1",
            config=self.aio_config,
            **self.config
        ) as client:
            yield client

    async def _multipart_upload(self, client, file_path, key, part_size=5 * 1024 * 1024):
        mpu = await client.create_multipart_upload(Bucket=self.bucket_name, Key=key)
        parts = []
        async with aiofiles.open(file_path, 'rb') as f:
            part_number = 1
            while True:
                data = await f.read(part_size)
                if not data:
                    break
                response = await client.upload_part(
                    Bucket=self.bucket_name,
                    Key=key,
                    PartNumber=part_number,
                    UploadId=mpu["UploadId"],
                    Body=data
                )
                parts.append({
                    'ETag': response['ETag'],
                    'PartNumber': part_number,
                })
                part_number += 1
        await client.complete_multipart_upload(
            Bucket=self.bucket_name,
            Key=key,
            UploadId=mpu["UploadId"],
            MultipartUpload={'Parts': parts}
        )

    async def upload_file(self, file_path: str, folder: str = None):
        object_name = os.path.basename(file_path)
        if folder:
            folder = folder.strip("/")
            object_name = f"{folder}/{object_name}"
        try:
            async with self.get_client() as client:
                file_size = os.path.getsize(file_path)
                if file_size > 5 * 1024 * 1024:  # 5 MB threshold for multipart
                    await self._multipart_upload(client, file_path, object_name)
                else:
                    async with aiofiles.open(file_path, "rb") as file:
                        content = await file.read()
                        await client.put_object(
                            Bucket=self.bucket_name,
                            Key=object_name,
                            Body=content,
                        )
                url = f"{self.endpoint_url}/{self.bucket_name}/{object_name}"
                os.remove(file_path)
                return url
        except ClientError as e:
            print(f"Error uploading file: {e}")
            return None