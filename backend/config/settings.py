"""
Настройки приложения BLDR.EMPIRE
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings

_DEFAULT_MANAGER_ENV = os.getenv("DEFAULT_PROJECT_MANAGER_ID")


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
    REDIS_BROKER_DB: int = int(os.getenv("REDIS_BROKER_DB", "1"))
    REDIS_RESULT_DB: int = int(os.getenv("REDIS_RESULT_DB", "2"))
    
    # Celery / Task Queue
    CELERY_BROKER_URL: Optional[str] = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: Optional[str] = os.getenv("CELERY_RESULT_BACKEND")
    CELERY_DEFAULT_QUEUE: str = os.getenv("CELERY_DEFAULT_QUEUE", "bldr_default")
    CELERY_MODEL_QUEUE: str = os.getenv("CELERY_MODEL_QUEUE", "models")
    CELERY_DOCUMENT_QUEUE: str = os.getenv("CELERY_DOCUMENT_QUEUE", "documents")
    CELERY_PROCESS_QUEUE: str = os.getenv("CELERY_PROCESS_QUEUE", "processes")
    CELERY_MONITORING_QUEUE: str = os.getenv("CELERY_MONITORING_QUEUE", "monitoring")
    CELERY_TASK_TIME_LIMIT: int = int(os.getenv("CELERY_TASK_TIME_LIMIT", "900"))
    CELERY_TASK_SOFT_TIME_LIMIT: int = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "600"))
    CELERY_RESULT_EXPIRES: int = int(os.getenv("CELERY_RESULT_EXPIRES", "3600"))
    
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
    RAG_BATCH_SIZE: int = int(os.getenv("RAG_BATCH_SIZE", "64"))
    RAG_PARALLEL_WORKERS: int = int(os.getenv("RAG_PARALLEL_WORKERS", "4"))
    RAG_ENABLE_QUANTIZATION: bool = os.getenv("RAG_ENABLE_QUANTIZATION", "True").lower() == "true"
    RAG_QUANTIZATION_QUANTILE: float = float(os.getenv("RAG_QUANTIZATION_QUANTILE", "0.99"))
    RAG_CACHE_TTL_SECONDS: int = int(os.getenv("RAG_CACHE_TTL_SECONDS", "3600"))
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_WEBHOOK_URL: Optional[str] = os.getenv("TELEGRAM_WEBHOOK_URL")
    TELEGRAM_PRICE_REQUEST_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_PRICE_REQUEST_CHAT_ID")
    TEO_APPROVAL_CHAT_IDS: List[str] = (
        os.getenv("TEO_APPROVAL_CHAT_IDS", "").split(",") if os.getenv("TEO_APPROVAL_CHAT_IDS") else []
    )
    TEO_APPROVAL_ROUTE: Optional[str] = os.getenv("TEO_APPROVAL_ROUTE")
    
    # SMTP / Email notifications
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "True").lower() == "true"
    EMAIL_FROM: Optional[str] = os.getenv("EMAIL_FROM")
    EMAIL_REPLY_TO: Optional[str] = os.getenv("EMAIL_REPLY_TO")
    LEADERSHIP_NOTIFICATION_EMAILS: List[str] = (
        os.getenv("LEADERSHIP_NOTIFICATION_EMAILS", "").split(",")
        if os.getenv("LEADERSHIP_NOTIFICATION_EMAILS")
        else []
    )

    # Email intake (IMAP)
    IMAP_HOST: Optional[str] = os.getenv("IMAP_HOST")
    IMAP_PORT: int = int(os.getenv("IMAP_PORT", "993"))
    IMAP_USE_SSL: bool = os.getenv("IMAP_USE_SSL", "True").lower() == "true"
    IMAP_USERNAME: Optional[str] = os.getenv("IMAP_USERNAME")
    IMAP_PASSWORD: Optional[str] = os.getenv("IMAP_PASSWORD")
    IMAP_MAILBOX: str = os.getenv("IMAP_MAILBOX", "INBOX")
    
    # Google Forms
    GOOGLE_SERVICE_ACCOUNT_JSON: Optional[str] = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    GOOGLE_FORMS_SPREADSHEET_ID: Optional[str] = os.getenv("GOOGLE_FORMS_SPREADSHEET_ID")
    GOOGLE_FORMS_RANGE: str = os.getenv("GOOGLE_FORMS_RANGE", "Форма!A:Z")
    
    # Yandex Geocoder
    YANDEX_GEOCODER_API_KEY: Optional[str] = os.getenv("YANDEX_GEOCODER_API_KEY")
    YANDEX_GEOCODER_LANG: str = os.getenv("YANDEX_GEOCODER_LANG", "ru_RU")
    YANDEX_GEOCODER_URL: str = os.getenv("YANDEX_GEOCODER_URL", "https://geocode-maps.yandex.ru/1.x/")

    # Проекты
    PROJECT_CODE_PREFIX: str = os.getenv("PROJECT_CODE_PREFIX", "PRJ")
    DEFAULT_PROJECT_OWNER_ID: int = int(os.getenv("DEFAULT_PROJECT_OWNER_ID", "1"))
    DEFAULT_PROJECT_MANAGER_ID: Optional[int] = (
        int(_DEFAULT_MANAGER_ENV) if _DEFAULT_MANAGER_ENV else None
    )
    PROJECT_MANAGER_ROTATION_WINDOW_DAYS: int = int(os.getenv("PROJECT_MANAGER_ROTATION_WINDOW_DAYS", "30"))
    
    # LLM Providers
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "local")
    LLM_LOCAL_API_URL: str = os.getenv("LLM_LOCAL_API_URL", "http://localhost:1234/v1")
    LLM_LOCAL_MODEL: str = os.getenv("LLM_LOCAL_MODEL", "LMStudio")
    LLM_REMOTE_API_URL: str = os.getenv("LLM_REMOTE_API_URL", "https://api.openai.com/v1")
    LLM_REMOTE_API_KEY: str = os.getenv("LLM_REMOTE_API_KEY", "")
    LLM_REMOTE_MODEL: str = os.getenv("LLM_REMOTE_MODEL", "gpt-4o-mini")
    # 1С Integration
    ONEC_API_URL: Optional[str] = os.getenv("ONEC_API_URL")
    ONEC_API_TOKEN: Optional[str] = os.getenv("ONEC_API_TOKEN")

    # Development Zones
    ALLOWED_DEVELOPMENT_ZONES: List[str] = (
        os.getenv("ALLOWED_DEVELOPMENT_ZONES", "жил,пром,технопарк").split(",")
    )
    RESTRICTED_DEVELOPMENT_ZONES: List[str] = (
        os.getenv("RESTRICTED_DEVELOPMENT_ZONES", "заповед,лес,садов,природ").split(",")
    )

    # DeepSeek OCR / Unsloth
    DEEPSEEK_OCR_MODEL: str = os.getenv("DEEPSEEK_OCR_MODEL", "deepseek-ai/DeepSeek-VL2")
    DEEPSEEK_OCR_MAX_NEW_TOKENS: int = int(os.getenv("DEEPSEEK_OCR_MAX_NEW_TOKENS", "512"))
    DEEPSEEK_OCR_PROMPT: str = os.getenv(
        "DEEPSEEK_OCR_PROMPT",
        "You are an accurate OCR assistant. Extract text from the provided image without explanations.",
    )
    DEEPSEEK_OCR_LOAD_IN_4BIT: bool = os.getenv("DEEPSEEK_OCR_LOAD_IN_4BIT", "True").lower() == "true"
    DEEPSEEK_OCR_DEVICE: str = os.getenv("DEEPSEEK_OCR_DEVICE", "cuda")

    UNSLOTH_DEFAULT_MODEL: str = os.getenv("UNSLOTH_DEFAULT_MODEL", "unsloth/llama-3-8b-Instruct-bnb-4bit")
    UNSLOTH_OUTPUT_DIR: str = os.getenv("UNSLOTH_OUTPUT_DIR", "outputs/unsloth")
    UNSLOTH_LORA_R: int = int(os.getenv("UNSLOTH_LORA_R", "16"))
    UNSLOTH_LORA_ALPHA: int = int(os.getenv("UNSLOTH_LORA_ALPHA", "32"))
    UNSLOTH_LORA_DROPOUT: float = float(os.getenv("UNSLOTH_LORA_DROPOUT", "0.05"))
    UNSLOTH_MAX_SEQ_LENGTH: int = int(os.getenv("UNSLOTH_MAX_SEQ_LENGTH", "4096"))
    UNSLOTH_BATCH_SIZE: int = int(os.getenv("UNSLOTH_BATCH_SIZE", "2"))
    UNSLOTH_GRADIENT_ACCUMULATION: int = int(os.getenv("UNSLOTH_GRADIENT_ACCUMULATION", "8"))
    UNSLOTH_LEARNING_RATE: float = float(os.getenv("UNSLOTH_LEARNING_RATE", "2e-4"))
    UNSLOTH_EPOCHS: int = int(os.getenv("UNSLOTH_EPOCHS", "3"))
    UNSLOTH_GGUF_OUTTYPE: str = os.getenv("UNSLOTH_GGUF_OUTTYPE", "q4_0")
    UNSLOTH_VALIDATION_MAX_TOKENS: int = int(os.getenv("UNSLOTH_VALIDATION_MAX_TOKENS", "256"))
    UNSLOTH_VALIDATION_TEMPERATURE: float = float(os.getenv("UNSLOTH_VALIDATION_TEMPERATURE", "0.2"))
    UNSLOTH_DEFAULT_VALIDATION_PROMPTS: str = os.getenv(
        "UNSLOTH_DEFAULT_VALIDATION_PROMPTS",
        "Кратко опиши ключевые выводы по документации||Перечисли основные разделы строительного проекта",
    )

    # Финансовые параметры по умолчанию
    FINANCIAL_DISCOUNT_RATE: float = float(os.getenv("FINANCIAL_DISCOUNT_RATE", "0.12"))
    FINANCIAL_OPERATION_PERIOD_MONTHS: int = int(os.getenv("FINANCIAL_OPERATION_PERIOD_MONTHS", "24"))
    FINANCIAL_DEFAULT_MARGIN_RATE: float = float(os.getenv("FINANCIAL_DEFAULT_MARGIN_RATE", "0.25"))
    FINANCIAL_DEFAULT_OPERATING_COST_RATE: float = float(os.getenv("FINANCIAL_DEFAULT_OPERATING_COST_RATE", "0.08"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def redis_broker_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_BROKER_DB}"

    @property
    def redis_result_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_RESULT_DB}"

    @property
    def celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or self.redis_broker_url

    @property
    def celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.redis_result_url


# Глобальный экземпляр настроек
settings = Settings()

