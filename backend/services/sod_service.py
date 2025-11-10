"""
Сервис для работы с СОД (Среда общих данных)
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.models.document import Document, DocumentVersion, DocumentMetadata
from backend.models.project import Project
from backend.services.minio_service import minio_service
from backend.services.document_classifier import document_classifier
from datetime import datetime
import hashlib
import logging
import difflib

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
        metadata: Optional[Dict[str, Any]] = None,
        auto_grant_permissions: bool = True
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
        
        # Классификация документа
        classification = document_classifier.classify_document(
            title=title,
            file_name=file_name
        )
        
        # Извлечение метаданных
        extracted_metadata = document_classifier.extract_metadata(
            file_name=file_name
        )
        
        # Объединение метаданных
        final_metadata = {
            **(metadata or {}),
            "classification": classification,
            "extracted": extracted_metadata
        }
        
        # Использование классификации для document_type если не указан
        if not document_type or document_type == "unknown":
            document_type = classification.get("classification", "other")
        
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
            metadata=final_metadata
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
        
        # Автоматическое предоставление прав создателю
        if auto_grant_permissions:
            try:
                from backend.services.document_permission_service import DocumentPermissionService
                permission_service = DocumentPermissionService(self.db)
                permission_service.grant_permission(
                    document_id=document.id,
                    subject_type="user",
                    subject_id=created_by,
                    permission_type="admin"
                )
                
                # Наследование прав от проекта, если указан
                if project_id:
                    permission_service.inherit_from_project(document.id, project_id)
            except Exception as e:
                logger.warning(f"Failed to grant permissions: {e}")
        
        logger.info(f"Created document {document.id}: {title}")
        return document
    
    def revert_to_version(
        self,
        document_id: int,
        version_number: int,
        reverted_by: int
    ) -> DocumentVersion:
        """Откат документа к предыдущей версии"""
        document = self.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Получение версии для отката
        version = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version_number
        ).first()
        
        if not version:
            raise ValueError(f"Version {version_number} not found for document {document_id}")
        
        # Скачивание файла версии
        from backend.services.minio_service import minio_service
        file_data = minio_service.download_file("documents", version.file_path)
        
        # Создание новой версии с содержимым старой
        new_version = self.create_version(
            document_id=document_id,
            file_data=file_data,
            change_description=f"Reverted to version {version_number}",
            changed_by=reverted_by
        )
        
        logger.info(f"Reverted document {document_id} to version {version_number}")
        return new_version

    def compare_versions(
        self,
        document_id: int,
        base_version: int,
        target_version: int,
    ) -> Dict[str, Any]:
        """Сравнение двух версий документа"""
        document = self.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        base = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == base_version
        ).first()
        target = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == target_version
        ).first()

        if not base or not target:
            raise ValueError("One or both versions were not found")

        base_data = minio_service.download_file("documents", base.file_path)
        target_data = minio_service.download_file("documents", target.file_path)

        base_hash = hashlib.sha256(base_data).hexdigest()
        target_hash = hashlib.sha256(target_data).hexdigest()
        base_size = len(base_data)
        target_size = len(target_data)

        diff_preview: List[str] = []
        if self._is_text_mime(document.mime_type):
            base_lines = base_data.decode("utf-8", errors="ignore").splitlines()
            target_lines = target_data.decode("utf-8", errors="ignore").splitlines()
            diff_lines = difflib.unified_diff(
                base_lines,
                target_lines,
                fromfile=f"v{base_version}",
                tofile=f"v{target_version}",
                lineterm=""
            )
            for idx, line in enumerate(diff_lines):
                if idx >= 200:
                    diff_preview.append("... (diff truncated)")
                    break
                diff_preview.append(line)
        else:
            diff_preview.append("Binary content; textual diff unavailable.")

        size_diff = target_size - base_size
        return {
            "document_id": document_id,
            "base_version": {
                "version_number": base_version,
                "file_hash": base_hash,
                "file_size": base_size,
                "change_description": base.change_description,
                "created_at": base.created_at.isoformat() if base.created_at else None,
            },
            "target_version": {
                "version_number": target_version,
                "file_hash": target_hash,
                "file_size": target_size,
                "change_description": target.change_description,
                "created_at": target.created_at.isoformat() if target.created_at else None,
            },
            "hash_equal": base_hash == target_hash,
            "size_difference": size_diff,
            "diff_preview": diff_preview,
        }
    
    def create_version(
        self,
        document_id: int,
        file_data: bytes,
        change_description: str,
        changed_by: int,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
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
        
        new_file_name = file_name or document.file_name
        new_mime_type = mime_type or self._detect_mime_type(new_file_name)
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        next_version_number = document.version + 1
        file_path = f"{document.document_type}/{timestamp}/{file_hash[:8]}/v{next_version_number}_{new_file_name}"
        
        minio_service.upload_file(
            bucket_name="documents",
            object_name=file_path,
            data=file_data,
            content_type=new_mime_type
        )
        
        document.file_name = new_file_name
        document.file_path = file_path
        document.file_size = len(file_data)
        document.mime_type = new_mime_type
        document.version = next_version_number
        document.updated_by = changed_by
        
        classification = document_classifier.classify_document(
            file_name=new_file_name,
            title=document.title
        )
        extracted_metadata = document_classifier.extract_metadata(
            file_name=new_file_name,
            file_path=file_path,
            mime_type=new_mime_type
        )
        document.metadata = {
            **(document.metadata or {}),
            **(metadata or {}),
            "classification": classification,
            "extracted": extracted_metadata,
        }
        document.document_type = classification.get("document_type", document.document_type)
        
        version = DocumentVersion(
            document_id=document_id,
            version_number=next_version_number,
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
        limit: int = 50,
        use_fulltext: bool = True
    ) -> List[Document]:
        """Поиск документов"""
        from backend.services.fulltext_search import FulltextSearchService
        
        # Использование полнотекстового поиска если есть запрос
        if query and use_fulltext:
            search_service = FulltextSearchService(self.db)
            return search_service.search(
                query=query,
                document_type=document_type,
                project_id=project_id,
                limit=limit
            )
        
        # Простой поиск
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

    def _is_text_mime(self, mime_type: str) -> bool:
        """Проверка, является ли MIME тип текстовым"""
        if not mime_type:
            return False
        if mime_type.startswith("text/"):
            return True
        text_like = {"application/json", "application/xml", "application/javascript"}
        return mime_type.lower() in text_like

