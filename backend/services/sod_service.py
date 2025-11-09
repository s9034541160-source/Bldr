"""
Сервис для работы с СОД (Среда общих данных)
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.models.document import Document, DocumentVersion, DocumentMetadata
from backend.models.project import Project
from backend.services.minio_service import minio_service
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger(__name__)


class SODService:
    """Сервис для управления документами в СОД"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_document(
        self,
        title: str,
        file_name: str,
        file_data: bytes,
        document_type: str,
        project_id: Optional[int] = None,
        created_by: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        Создание нового документа
        
        Args:
            title: Название документа
            file_name: Имя файла
            file_data: Данные файла
            document_type: Тип документа
            project_id: ID проекта (опционально)
            created_by: ID создателя
            metadata: Дополнительные метаданные
        """
        # Вычисление хеша файла
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # Определение MIME типа
        mime_type = self._detect_mime_type(file_name)
        
        # Генерация пути в MinIO
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        file_path = f"{document_type}/{timestamp}/{file_hash[:8]}/{file_name}"
        
        # Загрузка файла в MinIO
        minio_service.upload_file(
            bucket_name="documents",
            object_name=file_path,
            data=file_data,
            content_type=mime_type,
            metadata={"title": title, "document_type": document_type}
        )
        
        # Создание записи в БД
        document = Document(
            title=title,
            file_name=file_name,
            file_path=file_path,
            file_size=len(file_data),
            mime_type=mime_type,
            document_type=document_type,
            project_id=project_id,
            created_by=created_by,
            metadata=metadata or {}
        )
        
        self.db.add(document)
        self.db.flush()
        
        # Создание первой версии
        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            file_path=file_path,
            file_hash=file_hash,
            change_description="Initial version",
            changed_by=created_by
        )
        
        self.db.add(version)
        self.db.commit()
        self.db.refresh(document)
        
        logger.info(f"Created document {document.id}: {title}")
        return document
    
    def create_version(
        self,
        document_id: int,
        file_data: bytes,
        change_description: str,
        changed_by: int
    ) -> DocumentVersion:
        """Создание новой версии документа"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Вычисление хеша
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # Проверка на дубликат
        existing_version = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.file_hash == file_hash
        ).first()
        
        if existing_version:
            logger.warning(f"Duplicate version detected for document {document_id}")
            return existing_version
        
        # Генерация пути для новой версии
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        file_path = f"{document.document_type}/{timestamp}/{file_hash[:8]}/v{document.version + 1}_{document.file_name}"
        
        # Загрузка в MinIO
        minio_service.upload_file(
            bucket_name="documents",
            object_name=file_path,
            data=file_data,
            content_type=document.mime_type
        )
        
        # Обновление версии документа
        document.version += 1
        document.parent_version_id = document.id
        document.updated_by = changed_by
        
        # Создание записи версии
        version = DocumentVersion(
            document_id=document_id,
            version_number=document.version,
            file_path=file_path,
            file_hash=file_hash,
            change_description=change_description,
            changed_by=changed_by
        )
        
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        
        logger.info(f"Created version {version.version_number} for document {document_id}")
        return version
    
    def get_document(self, document_id: int) -> Optional[Document]:
        """Получение документа по ID"""
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def get_document_versions(self, document_id: int) -> List[DocumentVersion]:
        """Получение всех версий документа"""
        return self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.version_number.desc()).all()
    
    def search_documents(
        self,
        query: Optional[str] = None,
        document_type: Optional[str] = None,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Document]:
        """Поиск документов"""
        q = self.db.query(Document).filter(Document.is_active == True)
        
        if query:
            q = q.filter(Document.title.ilike(f"%{query}%"))
        
        if document_type:
            q = q.filter(Document.document_type == document_type)
        
        if project_id:
            q = q.filter(Document.project_id == project_id)
        
        if status:
            q = q.filter(Document.status == status)
        
        return q.order_by(Document.created_at.desc()).limit(limit).all()
    
    def delete_document(self, document_id: int, deleted_by: int) -> bool:
        """Мягкое удаление документа"""
        document = self.get_document(document_id)
        if not document:
            return False
        
        document.is_active = False
        document.updated_by = deleted_by
        self.db.commit()
        
        logger.info(f"Deleted document {document_id}")
        return True
    
    def _detect_mime_type(self, file_name: str) -> str:
        """Определение MIME типа по расширению файла"""
        ext = file_name.split(".")[-1].lower()
        mime_types = {
            "pdf": "application/pdf",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xls": "application/vnd.ms-excel",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "txt": "text/plain",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png"
        }
        return mime_types.get(ext, "application/octet-stream")

