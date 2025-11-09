"""
API эндпоинты для проверки здоровья сервисов
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models import get_db
from backend.services.neo4j_service import neo4j_service
from backend.services.qdrant_service import qdrant_service
from backend.services.redis_service import redis_service
from backend.services.minio_service import minio_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """Общая проверка здоровья API"""
    return {
        "status": "healthy",
        "service": "BLDR.EMPIRE API"
    }


@router.get("/db")
async def check_database(db: Session = Depends(get_db)):
    """Проверка подключения к PostgreSQL"""
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "postgresql"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


@router.get("/neo4j")
async def check_neo4j():
    """Проверка подключения к Neo4j"""
    try:
        result = neo4j_service.execute_query("RETURN 1 as test")
        return {"status": "healthy", "database": "neo4j"}
    except Exception as e:
        logger.error(f"Neo4j health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {str(e)}")


@router.get("/qdrant")
async def check_qdrant():
    """Проверка подключения к Qdrant"""
    try:
        collections = qdrant_service.client.get_collections()
        return {"status": "healthy", "database": "qdrant", "collections": len(collections.collections)}
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Qdrant unavailable: {str(e)}")


@router.get("/redis")
async def check_redis():
    """Проверка подключения к Redis"""
    try:
        if redis_service.ping():
            return {"status": "healthy", "database": "redis"}
        else:
            raise HTTPException(status_code=503, detail="Redis ping failed")
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {str(e)}")


@router.get("/minio")
async def check_minio():
    """Проверка подключения к MinIO"""
    try:
        # Попытка получить список buckets
        buckets = minio_service.client.list_buckets()
        return {"status": "healthy", "storage": "minio", "buckets": len(buckets)}
    except Exception as e:
        logger.error(f"MinIO health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"MinIO unavailable: {str(e)}")


@router.get("/all")
async def check_all(db: Session = Depends(get_db)):
    """Проверка всех сервисов"""
    results = {
        "api": {"status": "healthy"},
        "postgresql": None,
        "neo4j": None,
        "qdrant": None,
        "redis": None,
        "minio": None
    }
    
    # PostgreSQL
    try:
        db.execute("SELECT 1")
        results["postgresql"] = {"status": "healthy"}
    except Exception as e:
        results["postgresql"] = {"status": "unhealthy", "error": str(e)}
    
    # Neo4j
    try:
        neo4j_service.execute_query("RETURN 1 as test")
        results["neo4j"] = {"status": "healthy"}
    except Exception as e:
        results["neo4j"] = {"status": "unhealthy", "error": str(e)}
    
    # Qdrant
    try:
        qdrant_service.client.get_collections()
        results["qdrant"] = {"status": "healthy"}
    except Exception as e:
        results["qdrant"] = {"status": "unhealthy", "error": str(e)}
    
    # Redis
    try:
        if redis_service.ping():
            results["redis"] = {"status": "healthy"}
        else:
            results["redis"] = {"status": "unhealthy", "error": "Ping failed"}
    except Exception as e:
        results["redis"] = {"status": "unhealthy", "error": str(e)}
    
    # MinIO
    try:
        minio_service.client.list_buckets()
        results["minio"] = {"status": "healthy"}
    except Exception as e:
        results["minio"] = {"status": "unhealthy", "error": str(e)}
    
    # Общий статус
    all_healthy = all(
        result.get("status") == "healthy" 
        for result in results.values() 
        if result
    )
    
    status_code = 200 if all_healthy else 503
    
    return results

