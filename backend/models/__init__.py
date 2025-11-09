"""SQLAlchemy models"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from backend.config.settings import settings

Base = declarative_base()

# Создание движка БД
engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Импорт моделей для Alembic (после определения Base)
from backend.models.auth import User, Role, Permission

__all__ = ["Base", "engine", "SessionLocal", "get_db", "User", "Role", "Permission"]
