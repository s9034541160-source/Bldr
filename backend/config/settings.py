"""
Настройки приложения BLDR.EMPIRE
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Общие настройки
    PROJECT_NAME: str = "BLDR.EMPIRE"
    VERSION: str = "3.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # База данных PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/bldr3"
    )
    
    # Neo4j
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # Qdrant
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # MinIO
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "False").lower() == "true"
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # LLM
    LLM_MODEL_PATH: Optional[str] = os.getenv("LLM_MODEL_PATH")
    LLM_CONTEXT_SIZE: int = int(os.getenv("LLM_CONTEXT_SIZE", "4096"))
    LLM_N_GPU_LAYERS: int = int(os.getenv("LLM_N_GPU_LAYERS", "0"))
    LLM_MODEL_TTL_SECONDS: int = int(os.getenv("LLM_MODEL_TTL_SECONDS", "300"))
    LLM_MAX_LOADED_MODELS: int = int(os.getenv("LLM_MAX_LOADED_MODELS", "3"))
    LLM_CONFIG_PATH: str = os.getenv(
        "LLM_CONFIG_PATH",
        os.path.join(os.path.dirname(__file__), "llm_models.json")
    )
    
    # RAG
    RAG_EMBEDDING_MODEL: str = os.getenv(
        "RAG_EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    RAG_COLLECTION_NAME: str = "bldr_documents"
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # 1С Integration
    ONEC_API_URL: Optional[str] = os.getenv("ONEC_API_URL")
    ONEC_API_TOKEN: Optional[str] = os.getenv("ONEC_API_TOKEN")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Глобальный экземпляр настроек
settings = Settings()

