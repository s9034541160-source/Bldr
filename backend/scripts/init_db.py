"""
Скрипт для инициализации базы данных
"""

import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.database import init_db
from backend.services.neo4j_service import neo4j_service
from backend.services.qdrant_service import qdrant_service
from backend.services.redis_service import redis_service
from backend.services.minio_service import minio_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Инициализация всех баз данных и хранилищ"""
    logger.info("Starting database initialization...")
    
    # PostgreSQL
    try:
        logger.info("Initializing PostgreSQL...")
        init_db()
        logger.info("PostgreSQL initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")
        return False
    
    # Neo4j
    try:
        logger.info("Initializing Neo4j...")
        neo4j_service.init_constraints()
        logger.info("Neo4j initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j: {e}")
        return False
    
    # Qdrant
    try:
        logger.info("Initializing Qdrant...")
        qdrant_service.init_collection()
        logger.info("Qdrant initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant: {e}")
        return False
    
    # Redis
    try:
        logger.info("Checking Redis...")
        if redis_service.ping():
            logger.info("Redis is available")
        else:
            logger.warning("Redis ping failed")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return False
    
    # MinIO
    try:
        logger.info("Initializing MinIO buckets...")
        minio_service.init_buckets()
        logger.info("MinIO initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MinIO: {e}")
        return False
    
    logger.info("All databases initialized successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

