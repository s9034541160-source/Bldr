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
from backend.services.training.pipeline import TrainingPipelineService

router = APIRouter(prefix="/training", tags=["training"])


class DatasetCreateRequest(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    document_ids: List[int]
    questions_per_chunk: int = Field(2, ge=1, le=10)
    max_examples: int = Field(200, ge=1, le=2000)
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
    dataset_id: int
    base_model_id: str
    hyperparameters: Optional[Dict[str, Any]] = None


class JobResponse(BaseModel):
    id: int
    dataset_id: int
    base_model_id: str
    status: str
    metrics: Optional[Dict[str, Any]]
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    output_path: Optional[str]


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
        "max_examples": request.max_examples,
        "qa_model_id": request.qa_model_id,
    }
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
        hyperparameters=request.hyperparameters,
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

