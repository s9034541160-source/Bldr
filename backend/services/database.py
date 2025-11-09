"""
Сервисы для работы с базами данных
"""

from sqlalchemy.orm import Session
from backend.models import engine, SessionLocal
from backend.config.settings import settings
import logging

logger = logging.getLogger(__name__)


def init_db():
    """Инициализация базы данных - создание всех таблиц"""
    from backend.models import Base
    from backend.models.auth import User, Role, Permission
    
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def get_db_session() -> Session:
    """Получение сессии БД"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Сессия будет закрыта вызывающим кодом

