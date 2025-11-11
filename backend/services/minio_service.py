"""
Сервис для работы с MinIO (S3-compatible storage)
"""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Optional, BinaryIO

from minio import Minio
from minio.error import S3Error

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class MinIOService:
    """Сервис для работы с MinIO"""
    
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
    
    def ensure_bucket(self, bucket_name: str):
        """Создание bucket если не существует"""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
            else:
                logger.info(f"Bucket {bucket_name} already exists")
        except S3Error as e:
            logger.error(f"Error creating bucket {bucket_name}: {e}")
            raise
    
    def init_buckets(self):
        """Инициализация всех необходимых buckets"""
        buckets = [
            "documents",  # Документы СОД
            "templates",  # Шаблоны документов
            "models",     # Модели ИИ
            "exports",    # Экспортированные файлы
            "temp"        # Временные файлы
        ]
        
        for bucket in buckets:
            try:
                self.ensure_bucket(bucket)
            except Exception as e:
                logger.error(f"Failed to create bucket {bucket}: {e}")
    
    def upload_file(
        self,
        *,
        bucket_name: str,
        object_name: str,
        data: Optional[bytes] = None,
        data_stream: Optional[BinaryIO] = None,
        length: Optional[int] = None,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> None:
        """Загрузка файла (поддерживает потоковую передачу для больших файлов)"""
        if data is None and data_stream is None:
            raise ValueError("Either data or data_stream must be provided")

        stream: BinaryIO
        if data is not None:
            stream = BytesIO(data)
            length = len(data)
        else:
            if not hasattr(data_stream, "read"):
                raise ValueError("data_stream must be a file-like object")
            stream = data_stream  # type: ignore[assignment]

        if length is None:
            if hasattr(stream, "seek") and hasattr(stream, "tell"):
                current_pos = stream.tell()
                stream.seek(0, 2)
                length = stream.tell()
                stream.seek(current_pos)
            else:
                raise ValueError("length is required for streaming uploads without seekable stream")

        if stream is data_stream and hasattr(stream, "seek"):
            stream.seek(0)

        try:
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=stream,
                length=length,
                content_type=content_type,
                metadata=metadata,
            )
            logger.info("Uploaded %s to bucket %s (size=%s)", object_name, bucket_name, length)
        except S3Error as exc:
            logger.error("Error uploading file %s: %s", object_name, exc)
            raise
    
    def download_file(self, bucket_name: str, object_name: str) -> bytes:
        """Скачивание файла"""
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    def delete_file(self, bucket_name: str, object_name: str):
        """Удаление файла"""
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"Deleted {object_name} from {bucket_name}")
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            raise
    
    def list_files(self, bucket_name: str, prefix: str = ""):
        """Список файлов в bucket"""
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Error listing files: {e}")
            raise
    
    def get_file_url(self, bucket_name: str, object_name: str, expires_seconds: int = 3600) -> str:
        """Получение временной ссылки на файл"""
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                bucket_name,
                object_name,
                expires=timedelta(seconds=expires_seconds)
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating URL: {e}")
            raise

    def ensure_project_structure(self, project_prefix: str) -> None:
        """
        Создаёт базовую структуру папок проекта во всех необходимых бакетах.

        Args:
            project_prefix: каталог проекта (например, projects/<uuid>)
        """
        placeholders = {
            "documents": ["incoming", "processed", "contracts"],
            "templates": [project_prefix],
            "exports": [project_prefix],
        }

        for bucket, folders in placeholders.items():
            try:
                self.ensure_bucket(bucket)
                for folder in folders:
                    prefix = f"{project_prefix}/{folder}".rstrip("/") if bucket != "templates" else folder.rstrip("/")
                    object_name = f"{prefix}/.keep"
                    try:
                        self.client.put_object(
                            bucket,
                            object_name,
                            data=BytesIO(b""),
                            length=0,
                        )
                    except S3Error as exc:
                        if exc.code != "BucketAlreadyOwnedByYou":
                            logger.debug("Placeholder upload failed for %s/%s: %s", bucket, object_name, exc)
            except Exception as exc:
                logger.warning("Failed to ensure project structure in bucket %s: %s", bucket, exc)


# Глобальный экземпляр сервиса
minio_service = MinIOService()

