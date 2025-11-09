"""
API эндпоинты для СОД (Среда общих данных)
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.models import get_db
from backend.services.sod_service import SODService
from backend.services.document_search import DocumentSearchService
from backend.services.document_permission_service import DocumentPermissionService
from backend.middleware.rbac import get_current_user, require_permission
from backend.middleware.document_permission import require_document_permission
from backend.models.auth import User
from backend.models.document import Document
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sod", tags=["sod"])


class DocumentResponse(BaseModel):
    """Ответ с информацией о документе"""
    id: int
    title: str
    file_name: str
    document_type: str
    version: int
    status: str
    created_at: str
    
    class Config:
        from_attributes = True


class VersionResponse(BaseModel):
    """Ответ с информацией о версии"""
    id: int
    version_number: int
    change_description: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("/documents", response_model=DocumentResponse, status_code=201)
@require_permission("document", "write")
async def create_document(
    title: str = Form(...),
    document_type: str = Form(...),
    project_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание нового документа"""
    try:
        file_data = await file.read()
        
        service = SODService(db)
        document = service.create_document(
            title=title,
            file_name=file.filename or "unknown",
            file_data=file_data,
            document_type=document_type,
            project_id=project_id,
            created_by=current_user.id
        )
        
        return DocumentResponse(
            id=document.id,
            title=document.title,
            file_name=document.file_name,
            document_type=document.document_type,
            version=document.version,
            status=document.status,
            created_at=document.created_at.isoformat()
        )
    except Exception as e:
        logger.error(f"Document creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document: Document = Depends(require_document_permission("read")),
    current_user: User = Depends(get_current_user)
):
    """Получение документа (с проверкой прав доступа)"""
    return DocumentResponse(
        id=document.id,
        title=document.title,
        file_name=document.file_name,
        document_type=document.document_type,
        version=document.version,
        status=document.status,
        created_at=document.created_at.isoformat()
    )


@router.get("/documents", response_model=List[DocumentResponse])
@require_permission("document", "read")
async def search_documents(
    query: Optional[str] = Query(None),
    document_type: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search_type: str = Query("fulltext"),  # fulltext, semantic, hybrid
    limit: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Поиск документов"""
    if query and search_type in ["semantic", "hybrid"]:
        # Использование семантического или гибридного поиска
        search_service = DocumentSearchService(db)
        
        if search_type == "semantic":
            results = search_service.semantic_search(
                query=query,
                document_type=document_type,
                project_id=project_id,
                limit=limit
            )
            documents = [r["document"] for r in results]
        else:  # hybrid
            results = search_service.hybrid_search(
                query=query,
                document_type=document_type,
                project_id=project_id,
                limit=limit
            )
            documents = [r["document"] for r in results]
    else:
        # Обычный поиск через SODService
        service = SODService(db)
        documents = service.search_documents(
            query=query,
            document_type=document_type,
            project_id=project_id,
            status=status,
            limit=limit
        )
    
    return [
        DocumentResponse(
            id=d.id,
            title=d.title,
            file_name=d.file_name,
            document_type=d.document_type,
            version=d.version,
            status=d.status,
            created_at=d.created_at.isoformat()
        )
        for d in documents
    ]


@router.get("/documents/{document_id}/versions", response_model=List[VersionResponse])
async def get_document_versions(
    document_id: int,
    document: Document = Depends(require_document_permission("read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение всех версий документа"""
    service = SODService(db)
    versions = service.get_document_versions(document_id)
    
    return [
        VersionResponse(
            id=v.id,
            version_number=v.version_number,
            change_description=v.change_description,
            created_at=v.created_at.isoformat()
        )
        for v in versions
    ]


@router.post("/documents/{document_id}/versions")
async def create_version(
    document_id: int,
    change_description: str = Form(...),
    file: UploadFile = File(...),
    document: Document = Depends(require_document_permission("write")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание новой версии документа (с проверкой прав доступа)"""
    try:
        file_data = await file.read()
        
        service = SODService(db)
        version = service.create_version(
            document_id=document_id,
            file_data=file_data,
            change_description=change_description,
            changed_by=current_user.id
        )
        
        return {
            "version_number": version.version_number,
            "file_hash": version.file_hash,
            "created_at": version.created_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Version creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/{document_id}/revert")
async def revert_document(
    document_id: int,
    version_number: int = Form(...),
    document: Document = Depends(require_document_permission("write")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Откат документа к предыдущей версии"""
    try:
        service = SODService(db)
        version = service.revert_to_version(
            document_id=document_id,
            version_number=version_number,
            reverted_by=current_user.id
        )
        
        return {
            "status": "reverted",
            "new_version_number": version.version_number,
            "reverted_to_version": version_number,
            "created_at": version.created_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Revert error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: int,
    version: Optional[int] = Query(None),
    document: Document = Depends(require_document_permission("read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Скачивание документа (с проверкой прав доступа)"""
    from fastapi.responses import Response
    
    service = SODService(db)
    
    # Определение версии для скачивания
    if version:
        versions = service.get_document_versions(document_id)
        target_version = next((v for v in versions if v.version_number == version), None)
        if not target_version:
            raise HTTPException(status_code=404, detail="Version not found")
        file_path = target_version.file_path
    else:
        file_path = document.file_path
    
    # Скачивание из MinIO
    try:
        from backend.services.minio_service import minio_service
        file_data = minio_service.download_file("documents", file_path)
        
        return Response(
            content=file_data,
            media_type=document.mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{document.file_name}"'
            }
        )
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    document: Document = Depends(require_document_permission("delete")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Мягкое удаление документа"""
    try:
        service = SODService(db)
        service.delete_document(document_id, current_user.id)
        return {"status": "deleted"}
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
