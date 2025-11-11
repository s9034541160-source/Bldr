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
from backend.models.document import Document, DocumentVersion, DocumentMetadata
from backend.models.project import Project
from backend.models.project_request import ProjectRequest
from backend.models.training import TrainingDataset, TrainingJob
from backend.models.gesn import (
    GESNSection,
    GESNNorm,
    GESNNormComponent,
    GESNNormResource,
)
from backend.models.document_permission import DocumentPermission, DocumentAccessLog

__all__ = [
    "Base", "engine", "SessionLocal", "get_db",
    "User", "Role", "Permission",
    "Document", "DocumentVersion", "DocumentMetadata",
    "Project",
    "ProjectRequest",
    "TrainingDataset",
    "TrainingJob",
    "DocumentPermission",
    "DocumentAccessLog",
    "GESNSection",
    "GESNNorm",
    "GESNNormComponent",
    "GESNNormResource",
]
