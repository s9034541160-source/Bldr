#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG API Models and Endpoints
=============================
Модели данных и эндпоинты для RAG системы
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# ===============================
# RAG REQUEST/RESPONSE MODELS
# ===============================

class RAGSearchRequest(BaseModel):
    """Запрос для RAG поиска"""
    query: str = Field(..., description="Поисковый запрос")
    k: int = Field(default=5, ge=1, le=20, description="Количество результатов")
    threshold: float = Field(default=0.3, ge=0.0, le=1.0, description="Порог релевантности")
    doc_types: Optional[List[str]] = Field(default=None, description="Фильтр по типам документов")
    include_metadata: bool = Field(default=True, description="Включать метаданные в ответ")

class RAGSearchResult(BaseModel):
    """Результат RAG поиска"""
    content: str = Field(..., description="Текст найденного фрагмента")
    score: float = Field(..., description="Оценка релевантности (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные документа")
    section_id: Optional[str] = Field(default=None, description="ID секции")
    chunk_type: str = Field(default="paragraph", description="Тип чанка")

class RAGSearchResponse(BaseModel):
    """Ответ на RAG поиск"""
    query: str = Field(..., description="Исходный запрос")
    results: List[RAGSearchResult] = Field(..., description="Найденные результаты")
    total_found: int = Field(..., description="Всего найдено результатов")
    processing_time: float = Field(..., description="Время обработки в секундах")
    search_method: str = Field(default="sbert", description="Метод поиска")

class RAGTrainingRequest(BaseModel):
    """Запрос на запуск RAG тренировки"""
    base_dir: Optional[str] = Field(default=None, description="Директория с документами")
    max_files: Optional[int] = Field(default=None, description="Максимум файлов для обработки")
    force_retrain: bool = Field(default=False, description="Принудительная переобработка")
    doc_types: Optional[List[str]] = Field(default=None, description="Типы документов для обработки")

class RAGTrainingResponse(BaseModel):
    """Ответ на запуск RAG тренировки"""
    task_id: str = Field(..., description="ID задачи тренировки")
    status: str = Field(..., description="Статус запуска")
    message: str = Field(..., description="Сообщение о результате")
    estimated_time: Optional[str] = Field(default=None, description="Примерное время выполнения")

class RAGStatusResponse(BaseModel):
    """Статус RAG системы"""
    is_training: bool = Field(..., description="Идет ли обучение")
    progress: int = Field(..., description="Прогресс обучения (0-100)")
    current_stage: str = Field(..., description="Текущий этап")
    message: str = Field(..., description="Текущее сообщение")
    total_documents: int = Field(default=0, description="Всего документов в базе")
    total_chunks: int = Field(default=0, description="Всего чанков в базе")
    last_update: Optional[datetime] = Field(default=None, description="Последнее обновление")

# ===============================
# AI CHAT MODELS
# ===============================

class AIChatMessage(BaseModel):
    """Сообщение для AI чата"""
    message: str = Field(..., description="Текст сообщения")
    context_search: bool = Field(default=True, description="Использовать контекст из RAG")
    max_context: int = Field(default=3, ge=1, le=10, description="Максимум контекстных документов")
    agent_role: Optional[str] = Field(default="coordinator", description="Роль агента")
    
class AIChatResponse(BaseModel):
    """Ответ AI чата"""
    response: str = Field(..., description="Ответ AI")
    context_used: List[RAGSearchResult] = Field(default_factory=list, description="Использованный контекст")
    agent_used: str = Field(..., description="Использованный агент")
    processing_time: float = Field(..., description="Время обработки")

# ===============================
# TELEGRAM BOT MODELS
# ===============================

class TelegramUpdate(BaseModel):
    """Telegram webhook update"""
    update_id: int
    message: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None
    
class TelegramResponse(BaseModel):
    """Ответ на Telegram webhook"""
    status: str = Field(..., description="Статус обработки")
    message: str = Field(..., description="Сообщение о результате")

# ===============================
# DOCUMENT ANALYSIS MODELS
# ===============================

class DocumentAnalysisRequest(BaseModel):
    """Запрос на анализ документа"""
    file_path: str = Field(..., description="Путь к файлу")
    analysis_type: str = Field(default="full", description="Тип анализа (full, quick, metadata)")
    extract_works: bool = Field(default=True, description="Извлекать рабочие процессы")
    
class DocumentAnalysisResponse(BaseModel):
    """Результат анализа документа"""
    file_path: str = Field(..., description="Путь к файлу")
    doc_type: str = Field(..., description="Тип документа")
    confidence: float = Field(..., description="Уверенность в типе")
    sections_count: int = Field(..., description="Количество секций")
    works_found: int = Field(..., description="Найдено работ")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Извлеченные метаданные")
    quality_score: float = Field(..., description="Оценка качества")
    processing_time: float = Field(..., description="Время обработки")