"""
Сервис для полнотекстового поиска документов
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from backend.models.document import Document, DocumentMetadata
import logging

logger = logging.getLogger(__name__)


class FulltextSearchService:
    """Сервис для полнотекстового поиска"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def search(
        self,
        query: str,
        document_type: Optional[str] = None,
        project_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Document]:
        """
        Полнотекстовый поиск документов
        
        Args:
            query: Поисковый запрос
            document_type: Фильтр по типу документа
            project_id: Фильтр по проекту
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных документов
        """
        # Базовый запрос
        q = self.db.query(Document).filter(Document.is_active == True)
        
        # Разбиение запроса на слова
        query_words = query.lower().split()
        
        # Поиск по названию и описанию
        title_conditions = [
            Document.title.ilike(f"%{word}%") for word in query_words
        ]
        description_conditions = [
            Document.description.ilike(f"%{word}%") for word in query_words
        ]
        
        # Поиск по метаданным
        metadata_conditions = [
            DocumentMetadata.value.ilike(f"%{word}%") for word in query_words
        ]
        
        # Объединение условий
        search_conditions = or_(
            and_(*title_conditions),
            and_(*description_conditions),
            Document.id.in_(
                self.db.query(DocumentMetadata.document_id).filter(
                    or_(*metadata_conditions)
                )
            )
        )
        
        q = q.filter(search_conditions)
        
        # Фильтры
        if document_type:
            q = q.filter(Document.document_type == document_type)
        
        if project_id:
            q = q.filter(Document.project_id == project_id)
        
        # Сортировка по релевантности (упрощенная)
        # В будущем можно использовать ts_rank для PostgreSQL
        results = q.order_by(Document.created_at.desc()).limit(limit).all()
        
        return results
    
    def search_by_metadata(
        self,
        metadata_key: str,
        metadata_value: str,
        limit: int = 50
    ) -> List[Document]:
        """
        Поиск документов по метаданным
        
        Args:
            metadata_key: Ключ метаданных
            metadata_value: Значение метаданных
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных документов
        """
        document_ids = self.db.query(DocumentMetadata.document_id).filter(
            DocumentMetadata.key == metadata_key,
            DocumentMetadata.value.ilike(f"%{metadata_value}%")
        ).all()
        
        ids = [id[0] for id in document_ids]
        
        return self.db.query(Document).filter(
            Document.id.in_(ids),
            Document.is_active == True
        ).limit(limit).all()

