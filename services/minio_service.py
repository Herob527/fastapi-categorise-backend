import io
import os
from typing import BinaryIO
from minio import Minio
from minio.commonconfig import CopySource
from minio.error import S3Error
from fastapi import HTTPException
import uuid
from datetime import timedelta

__all__ = ["minio_service"]


class MinIOService:
    bucket_name: str
    client: Minio
    endpoint: str

    def __init__(self):
        self.client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
        )
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "categorize-files")
        self.endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            print(f"Error creating bucket: {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize storage")

    def remove_dir(self, dir: str):
        try:
            files = self.list_files(dir)
            for file in files:
                self.delete_file(file)

            print(f"Removed bucket: {self.bucket_name}")
        except S3Error as e:
            print(f"Error removing bucket: {e}")
            raise HTTPException(status_code=500, detail="Failed to remove bucket")

    def append_to_text(self, object_name: str, text: str):
        try:
            self.client.put_object(
                self.bucket_name, object_name, io.BytesIO(text.encode()), len(text)
            )
        except S3Error as e:
            print(f"Error appending text: {e}")
            raise HTTPException(status_code=500, detail="Failed to append text")

    def copy_file(self, source_object_name: str, destination_object_name: str):
        copy_source = CopySource(self.bucket_name, source_object_name)
        try:
            self.client.copy_object(
                bucket_name=self.bucket_name,
                object_name=destination_object_name,
                source=copy_source,
            )
        except S3Error as e:
            print(f"Error copying file: {e}")
            raise HTTPException(status_code=500, detail="Failed to copy file")

    async def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream",
        folder: str = "",
    ) -> str:
        """
        Upload file to MinIO and return the object name
        """
        try:
            # Generate unique filename to avoid conflicts
            file_extension = filename.split(".")[-1] if "." in filename else ""
            unique_filename = (
                f"{uuid.uuid4()}.{file_extension}"
                if file_extension
                else str(uuid.uuid4())
            )

            # Add folder prefix if specified
            object_name = f"{folder}/{unique_filename}" if folder else unique_filename

            # Get file size
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            file_data.seek(0)  # Reset to beginning

            # Upload file
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type,
            )

            return object_name

        except S3Error as e:
            print(f"Error uploading file: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload file")

    async def download_file(self, object_name: str) -> bytes:
        """
        Download file from MinIO
        """
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            print(f"Error downloading file: {e}")
            raise HTTPException(status_code=404, detail="File not found")

    async def delete_file(self, object_name: str) -> bool:
        """
        Delete file from MinIO
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            print(f"Error deleting file: {e}")
            return False

    async def get_file_url(self, object_name: str, expires: int = 3600) -> str:
        """
        Generate presigned URL for file access
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(seconds=expires),
            )
            return url
        except S3Error as e:
            print(f"Error generating URL: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate file URL")

    async def list_files(self, prefix: str = "") -> list:
        """
        List files in bucket with optional prefix
        """
        try:
            objects = self.client.list_objects(
                bucket_name=self.bucket_name, prefix=prefix, recursive=True
            )
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"Error listing files: {e}")
            raise HTTPException(status_code=500, detail="Failed to list files")


# Create singleton instance
minio_service = MinIOService()
