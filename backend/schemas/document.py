"""
Pydantic схемы для работы с документами (СОД).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    """Схема ответа с информацией о документе."""

    id: int
    title: str
    file_name: str
    document_type: str
    version: int
    status: str
    created_at: datetime
    mime_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="metadata_json")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentListResponse(BaseModel):
    """Список документов с пагинацией (если потребуется)."""

    items: List[DocumentResponse]
    total: int


class DocumentVersionResponse(BaseModel):
    """Информация о версии документа."""

    id: int
    version_number: int
    change_description: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentVersionCompareResponse(BaseModel):
    """Результат сравнения двух версий документа."""

    document_id: int
    base_version: Dict[str, Any]
    target_version: Dict[str, Any]
    hash_equal: bool
    size_difference: int
    diff_preview: List[str]


class DocumentMetadataUpdate(BaseModel):
    """Запрос на обновление пользовательских метаданных документа."""

    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    linked_document_ids: Optional[List[int]] = None


