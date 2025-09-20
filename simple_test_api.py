#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Test API
===============
Упрощенный API для тестирования RAG эндпоинтов без тяжелых зависимостей
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
import jwt
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

# Добавить путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импорт наших RAG моделей
from rag_api_models import (
    RAGSearchRequest, RAGSearchResponse, RAGSearchResult,
    RAGTrainingRequest, RAGTrainingResponse, RAGStatusResponse,
    AIChatMessage, AIChatResponse,
    DocumentAnalysisRequest, DocumentAnalysisResponse
)

# Создать приложение FastAPI
app = FastAPI(title="Simple RAG API Test", version="1.0.0")

# Добавить CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Настройки безопасности
security = HTTPBearer()
SECRET_KEY = "your-secret-key-change-in-production"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Проверка JWT токена"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Мок данные для тестирования
mock_training_status = {
    "is_training": False,
    "progress": 0,
    "current_stage": "idle",
    "message": "RAG system ready",
    "total_documents": 42,
    "total_chunks": 1337
}

# ===============================
# API ENDPOINTS
# ===============================

@app.get("/health")
async def health_check():
    """Проверка здоровья сервера"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "message": "Simple RAG API Test is running"
    }

@app.post("/api/rag/search", response_model=RAGSearchResponse)
async def rag_search(request_data: RAGSearchRequest, credentials: dict = Depends(verify_token)):
    """Тестовый RAG поиск (мок данные)"""
    
    # Симуляция поиска
    time.sleep(0.1)  # Симуляция времени обработки
    
    # Создать мок результаты
    mock_results = []
    for i in range(min(request_data.k, 3)):
        result = RAGSearchResult(
            content=f"Тестовый результат {i+1} для запроса '{request_data.query}'. Это содержимое документа с релевантной информацией о строительных нормах и технических требованиях.",
            score=0.9 - (i * 0.1),
            metadata={
                "doc_id": f"test_doc_{i+1}",
                "source": "test_database",
                "category": "строительство",
                "type": "норма"
            },
            section_id=f"section_{i+1}",
            chunk_type="paragraph"
        )
        mock_results.append(result)
    
    response = RAGSearchResponse(
        query=request_data.query,
        results=mock_results,
        total_found=len(mock_results),
        processing_time=0.12,
        search_method="sbert_mock"
    )
    
    return response

@app.post("/api/rag/train", response_model=RAGTrainingResponse)
async def rag_train(request_data: RAGTrainingRequest, credentials: dict = Depends(verify_token)):
    """Тестовый запуск обучения RAG"""
    
    # Обновить статус (мок)
    global mock_training_status
    mock_training_status["is_training"] = True
    mock_training_status["current_stage"] = "starting"
    mock_training_status["message"] = "Начинается обучение RAG системы..."
    
    task_id = f"mock_training_{int(time.time())}"
    
    response = RAGTrainingResponse(
        task_id=task_id,
        status="started",
        message="RAG training started successfully (mock)",
        estimated_time="2-5 minutes (mock)"
    )
    
    return response

@app.get("/api/rag/status", response_model=RAGStatusResponse)
async def rag_status(credentials: dict = Depends(verify_token)):
    """Получить статус RAG системы (мок)"""
    
    global mock_training_status
    
    response = RAGStatusResponse(
        is_training=mock_training_status["is_training"],
        progress=mock_training_status["progress"],
        current_stage=mock_training_status["current_stage"],
        message=mock_training_status["message"],
        total_documents=mock_training_status["total_documents"],
        total_chunks=mock_training_status["total_chunks"],
        last_update=datetime.now()
    )
    
    return response

@app.post("/api/ai/chat", response_model=AIChatResponse)
async def ai_chat(request_data: AIChatMessage, credentials: dict = Depends(verify_token)):
    """Тестовый AI чат (мок)"""
    
    # Симуляция контекста
    context_used = []
    if request_data.context_search:
        for i in range(min(request_data.max_context, 2)):
            context_result = RAGSearchResult(
                content=f"Контекстный документ {i+1}: информация о {request_data.message[:20]}...",
                score=0.8 - (i * 0.1),
                metadata={"source": f"context_doc_{i+1}"},
                section_id=f"ctx_section_{i+1}",
                chunk_type="context"
            )
            context_used.append(context_result)
    
    # Мок ответ AI
    ai_response = f"Это тестовый ответ на ваш вопрос: '{request_data.message}'. Система работает корректно."
    
    if context_used:
        ai_response += f" Использован контекст из {len(context_used)} документов."
    
    response = AIChatResponse(
        response=ai_response,
        context_used=context_used,
        agent_used="mock_agent",
        processing_time=0.5
    )
    
    return response

@app.post("/api/document/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(request_data: DocumentAnalysisRequest, credentials: dict = Depends(verify_token)):
    """Тестовый анализ документа (мок)"""
    
    # Проверить существование файла
    if not os.path.exists(request_data.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Мок анализ
    response = DocumentAnalysisResponse(
        file_path=request_data.file_path,
        doc_type="строительная_документация",
        confidence=0.95,
        sections_count=5,
        works_found=3,
        metadata={
            "file_size": os.path.getsize(request_data.file_path),
            "analysis_date": datetime.now().isoformat(),
            "mock": True
        },
        quality_score=0.88,
        processing_time=0.3
    )
    
    return response

# Дополнительный эндпоинт для сравнения с оригинальным
@app.post("/query")
async def original_query(query_data: dict, credentials: dict = Depends(verify_token)):
    """Имитация оригинального query эндпоинта"""
    query = query_data.get("query", "")
    k = query_data.get("k", 4)
    
    # Мок результаты в оригинальном формате
    results = []
    for i in range(min(k, 3)):
        result = {
            "chunk": f"Оригинальный результат {i+1} для запроса '{query}'",
            "score": 0.95 - (i * 0.05),
            "meta": {
                "doc_id": f"orig_doc_{i+1}",
                "entities": {
                    "ORG": ["СП31", "ГОСТ"],
                    "MONEY": ["300млн"],
                    "PERCENT": ["95%"]
                }
            },
            "tezis": f"profit ROI rec conf0.{95-i*5}",
            "viol": 95 - (i * 5)
        }
        results.append(result)
    
    return {
        "results": results,
        "ndcg": 0.92
    }

if __name__ == "__main__":
    print("🚀 Starting Simple RAG Test API...")
    print("   Port: 8001")
    print("   Host: 127.0.0.1")
    print("   Mock data enabled")
    print()
    
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")