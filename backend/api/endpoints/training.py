"""
API endpoints for automated fine-tuning pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from backend.middleware.rbac import get_current_user
from backend.models import get_db
from backend.models.auth import User
from backend.models.training import TrainingDataset, TrainingJob
from backend.services.minio_service import minio_service
from backend.services.training.pipeline import TrainingPipelineService

router = APIRouter(prefix="/training", tags=["training"])


class DatasetCreateRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    document_ids: List[int]
    questions_per_chunk: int = Field(2, ge=1, le=10)
    total_pairs_target: Optional[int] = Field(0, ge=0)
    qa_model_id: Optional[str] = None
    prompt_template: Optional[str] = None

    @validator("document_ids")
    def validate_documents(cls, value: List[int]) -> List[int]:
        if not value:
            raise ValueError("At least one document must be provided")
        return value


class DatasetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    total_examples: int
    created_at: Optional[str]
    updated_at: Optional[str]
    config: Optional[Dict[str, Any]]
    sample_preview: Optional[List[Dict[str, Any]]]


class JobCreateRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    dataset_id: int
    base_model_id: str
    model_id: Optional[str] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    validation_prompts: Optional[List[str]] = None


class JobResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    id: int
    dataset_id: int
    base_model_id: str
    status: str
    metrics: Optional[Dict[str, Any]]
    adapter_path: Optional[str]
    artifact_path: Optional[str]
    gguf_path: Optional[str]
    model_id: Optional[str]
    validation_status: Optional[str]
    validation_metrics: Optional[Dict[str, Any]]
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    output_path: Optional[str]


class JobArtifactsResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    job_id: int
    model_id: Optional[str]
    adapter_url: Optional[str]
    gguf_url: Optional[str]


def _ensure_admin(user: User) -> None:
    roles = {role.name for role in user.roles}
    if "admin" not in roles:
        raise HTTPException(status_code=403, detail="Only admins can manage fine-tuning pipeline")


def _dataset_to_response(dataset: TrainingDataset) -> DatasetResponse:
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        status=dataset.status,
        total_examples=dataset.total_examples,
        created_at=dataset.created_at.isoformat() if dataset.created_at else None,
        updated_at=dataset.updated_at.isoformat() if dataset.updated_at else None,
        config=dataset.config,
        sample_preview=dataset.sample_preview,
    )


def _job_to_response(job: TrainingJob) -> JobResponse:
    return JobResponse(
        id=job.id,
        dataset_id=job.dataset_id,
        base_model_id=job.base_model_id,
        status=job.status,
        metrics=job.metrics,
        adapter_path=job.adapter_path,
        artifact_path=job.artifact_path,
        gguf_path=job.gguf_path,
        model_id=job.model_id,
        validation_status=job.validation_status,
        validation_metrics=job.validation_metrics,
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        output_path=job.output_path,
    )


@router.post("/datasets", response_model=DatasetResponse, status_code=201)
def create_dataset(
    request: DatasetCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin(current_user)
    service = TrainingPipelineService(db)
    config = {
        "questions_per_chunk": request.questions_per_chunk,
        "qa_model_id": request.qa_model_id,
    }
    if request.total_pairs_target is not None:
        config["total_pairs_target"] = request.total_pairs_target
    if request.prompt_template:
        config["prompt_template"] = request.prompt_template
    dataset = service.create_dataset(
        name=request.name,
        description=request.description,
        document_ids=request.document_ids,
        config=config,
    )
    return _dataset_to_response(dataset)


@router.get("/datasets", response_model=List[DatasetResponse])
def list_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin(current_user)
    service = TrainingPipelineService(db)
    datasets = service.list_datasets()
    return [_dataset_to_response(ds) for ds in datasets]


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin(current_user)
    service = TrainingPipelineService(db)
    dataset = service.get_dataset(dataset_id)
    return _dataset_to_response(dataset)


@router.post("/jobs", response_model=JobResponse, status_code=201)
def create_job(
    request: JobCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin(current_user)
    service = TrainingPipelineService(db)
    job = service.create_job(
        dataset_id=request.dataset_id,
        base_model_id=request.base_model_id,
        model_id=request.model_id,
        hyperparameters=request.hyperparameters,
        validation_prompts=request.validation_prompts,
    )
    return _job_to_response(job)


@router.get("/jobs", response_model=List[JobResponse])
def list_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin(current_user)
    service = TrainingPipelineService(db)
    jobs = service.list_jobs()
    return [_job_to_response(job) for job in jobs]


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin(current_user)
    service = TrainingPipelineService(db)
    job = service.get_job(job_id)
    return _job_to_response(job)


@router.get("/jobs/{job_id}/artifacts", response_model=JobArtifactsResponse)
def get_job_artifacts(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin(current_user)
    job = (
        db.query(TrainingJob)
        .filter(TrainingJob.id == job_id)
        .one_or_none()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")

    adapter_url = (
        minio_service.get_file_url("models", job.adapter_path)
        if job.adapter_path
        else None
    )
    gguf_remote_path = job.gguf_path or job.artifact_path
    gguf_url = (
        minio_service.get_file_url("models", gguf_remote_path)
        if gguf_remote_path
        else None
    )
    return JobArtifactsResponse(
        job_id=job.id,
        model_id=job.model_id,
        adapter_url=adapter_url,
        gguf_url=gguf_url,
    )

