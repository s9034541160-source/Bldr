"""
API эндпоинты для СОД (Среда общих данных)
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.models import get_db
from backend.services.sod_service import SODService
from backend.middleware.rbac import get_current_user, require_permission
from backend.models.auth import User
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
@require_permission("document", "read")
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение документа"""
    service = SODService(db)
    document = service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
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
    query: Optional[str] = None,
    document_type: Optional[str] = None,
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Поиск документов"""
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


@router.post("/documents/{document_id}/versions")
@require_permission("document", "write")
async def create_version(
    document_id: int,
    change_description: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание новой версии документа"""
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


@router.get("/documents/{document_id}/download")
@require_permission("document", "read")
async def download_document(
    document_id: int,
    version: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Скачивание документа"""
    from fastapi.responses import Response
    
    service = SODService(db)
    document = service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
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

