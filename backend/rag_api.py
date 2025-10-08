#!/usr/bin/env python3
"""
RAG API - API для работы с RAG системой
Предоставляет endpoints для метрик, сводок и списков документов
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import os

logger = logging.getLogger(__name__)

# Импортируем Qdrant и Neo4j
try:
    from qdrant_client import QdrantClient
    HAS_QDRANT = True
except ImportError:
    logger.warning("Qdrant not available")
    HAS_QDRANT = False

try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    logger.warning("Neo4j not available")
    HAS_NEO4J = False

def get_qdrant_client():
    """Получение подключения к Qdrant"""
    if not HAS_QDRANT:
        raise HTTPException(status_code=503, detail="Qdrant not available")
    
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    
    try:
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        raise HTTPException(status_code=503, detail=f"Qdrant connection failed: {str(e)}")

def get_neo4j_db():
    """Получение подключения к Neo4j"""
    if not HAS_NEO4J:
        raise HTTPException(status_code=503, detail="Neo4j not available")
    
    neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "neopassword")
    
    try:
        if neo4j_user and neo4j_password:
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        else:
            driver = GraphDatabase.driver(neo4j_uri)
        return driver
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        raise HTTPException(status_code=503, detail=f"Neo4j connection failed: {str(e)}")

# Pydantic модели для API
class MetricsData(BaseModel):
    total_chunks: int
    avg_ndcg: float
    coverage: float
    conf: float
    viol: int
    entities: Optional[Dict[str, int]] = None

class NormsSummary(BaseModel):
    total_documents: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    recent_documents: List[Dict[str, Any]]

class NormDoc(BaseModel):
    id: str
    name: str
    category: str
    type: str
    status: str
    issue_date: str
    check_date: str
    source: str
    link: str
    description: str

class NormsListResponse(BaseModel):
    data: List[NormDoc]
    pagination: Dict[str, Any]

# Создаем роутер
rag_router = APIRouter(prefix="/rag", tags=["RAG System"])

@rag_router.get("/metrics", response_model=MetricsData)
async def get_metrics(qdrant_client = Depends(get_qdrant_client)):
    """Получает метрики RAG системы"""
    try:
        # Получаем информацию о коллекции
        collections = qdrant_client.get_collections()
        
        total_chunks = 0
        for collection in collections.collections:
            collection_info = qdrant_client.get_collection(collection.name)
            total_chunks += collection_info.points_count
        
        # Базовые метрики (можно расширить)
        metrics = MetricsData(
            total_chunks=total_chunks,
            avg_ndcg=0.75,  # Примерное значение
            coverage=0.85,  # Примерное значение
            conf=0.80,      # Примерное значение
            viol=0,          # Примерное значение
            entities={"СП": 150, "СНиП": 200, "ГОСТ": 100}  # Примерные данные
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting RAG metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting RAG metrics: {str(e)}")

@rag_router.get("/norms/summary", response_model=NormsSummary)
async def get_norms_summary(neo4j_driver = Depends(get_neo4j_db)):
    """Получает сводку по нормам"""
    try:
        with neo4j_driver.session() as session:
            # Общее количество документов
            total_result = session.run("MATCH (d:Document) RETURN count(d) as total")
            total_record = total_result.single()
            total_documents = total_record["total"] if total_record else 0
            
            # Статистика по типам
            type_result = session.run("""
                MATCH (d:Document) 
                RETURN d.document_type as type, count(d) as count
                ORDER BY count DESC
            """)
            by_type = {record["type"]: record["count"] for record in type_result}
            
            # Статистика по статусам
            status_result = session.run("""
                MATCH (d:Document) 
                WHERE d.status IS NOT NULL
                RETURN d.status as status, count(d) as count
                ORDER BY count DESC
            """)
            by_status = {record["status"]: record["count"] for record in status_result}
            
            # Последние документы
            recent_result = session.run("""
                MATCH (d:Document) 
                RETURN d.title as title, d.document_type as type, d.created_at as created_at
                ORDER BY d.created_at DESC
                LIMIT 5
            """)
            recent_documents = [
                {
                    "title": record["title"],
                    "type": record["type"],
                    "created_at": record["created_at"]
                }
                for record in recent_result
            ]
            
            summary = NormsSummary(
                total_documents=total_documents,
                by_type=by_type,
                by_status=by_status,
                recent_documents=recent_documents
            )
            
            return summary
            
    except Exception as e:
        logger.error(f"Error getting norms summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting norms summary: {str(e)}")

@rag_router.get("/norms/list", response_model=NormsListResponse)
async def get_norms_list(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    neo4j_driver = Depends(get_neo4j_db)
):
    """Получает список документов с пагинацией"""
    try:
        with neo4j_driver.session() as session:
            # Общее количество
            total_result = session.run("MATCH (d:Document) RETURN count(d) as total")
            total_record = total_result.single()
            total = total_record["total"] if total_record else 0
            
            # Получаем документы с пагинацией
            offset = (page - 1) * limit
            docs_result = session.run(f"""
                MATCH (d:Document) 
                RETURN d.id as id, d.title as name, d.category as category, 
                       d.document_type as type, d.status as status,
                       d.issue_date as issue_date, d.check_date as check_date,
                       d.source as source, d.link as link, d.description as description
                ORDER BY d.created_at DESC
                SKIP {offset}
                LIMIT {limit}
            """)
            
            documents = []
            for record in docs_result:
                doc = NormDoc(
                    id=record["id"] or "",
                    name=record["name"] or "Без названия",
                    category=record["category"] or "Неизвестно",
                    type=record["type"] or "Неизвестно",
                    status=record["status"] or "Неизвестно",
                    issue_date=record["issue_date"] or "",
                    check_date=record["check_date"] or "",
                    source=record["source"] or "",
                    link=record["link"] or "",
                    description=record["description"] or ""
                )
                documents.append(doc)
            
            response = NormsListResponse(
                data=documents,
                pagination={
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            )
            
            return response
            
    except Exception as e:
        logger.error(f"Error getting norms list: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting norms list: {str(e)}")

# Health check endpoint
@rag_router.get("/health")
async def health_check():
    """Проверка состояния RAG API"""
    return {"status": "healthy", "service": "RAG System API"}
