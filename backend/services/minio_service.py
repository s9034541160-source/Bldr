"""
Сервис для работы с MinIO (S3-compatible storage)
"""

from minio import Minio
from minio.error import S3Error
from backend.config.settings import settings
import logging
from io import BytesIO
from typing import Optional

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
    
    def upload_file(self, bucket_name: str, object_name: str, 
                   data: bytes, content_type: str = "application/octet-stream",
                   metadata: Optional[dict] = None):
        """Загрузка файла"""
        try:
            data_stream = BytesIO(data)
            length = len(data)
            
            self.client.put_object(
                bucket_name,
                object_name,
                data_stream,
                length,
                content_type=content_type,
                metadata=metadata
            )
            logger.info(f"Uploaded {object_name} to {bucket_name}")
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
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


# Глобальный экземпляр сервиса
minio_service = MinIOService()

