"""
Celery tasks for model fine-tuning and maintenance via Unsloth.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

import torch
from celery import shared_task
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from backend.config.settings import settings
from backend.core.model_manager import model_manager
from backend.models import SessionLocal
from backend.models.training import TrainingDataset, TrainingJob
from backend.services.minio_service import minio_service
from backend.services.task_queue import task_queue
from backend.services.training.unsloth_trainer import (
    FineTuneRequest,
    UnslothFineTuner,
)

logger = logging.getLogger(__name__)

GGUF_FILENAME = "model.gguf"
ADAPTER_ARCHIVE = "adapter.zip"


@shared_task(
    name="models.fine_tune_unsloth",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def fine_tune_unsloth(self, job_id: int) -> Dict[str, str]:  # type: ignore[override]
    """Фоновая задача дообучения модели через Unsloth."""
    session = SessionLocal()
    job: Optional[TrainingJob] = None
    try:
        job = (
            session.query(TrainingJob)
            .filter(TrainingJob.id == job_id)
            .with_for_update()
            .one_or_none()
        )
        if not job:
            raise ValueError(f"TrainingJob {job_id} not found")
        dataset = session.query(TrainingDataset).filter(TrainingDataset.id == job.dataset_id).one()

        dataset_path = _ensure_dataset_local(dataset, session)

        job.status = "running"
        job.started_at = datetime.utcnow()
        session.commit()

        payload = _build_request_payload(job, dataset_path)
        config = FineTuneRequest(**payload)
        logger.info(
            "Starting unsloth fine-tune for job=%s model=%s dataset=%s",
            job.id,
            config.base_model_id or "default",
            config.dataset_path,
        )

        tuner = UnslothFineTuner()
        result = tuner.train(config)

        adapter_dir = Path(result.adapter_dir)
        merged_dir = Path(settings.UNSLOTH_OUTPUT_DIR) / "models" / f"job_{job.id}" / "merged"
        merged_dir.mkdir(parents=True, exist_ok=True)
        gguf_local_path = merged_dir / GGUF_FILENAME
        adapter_archive_path = adapter_dir / ADAPTER_ARCHIVE

        _archive_adapter_directory(adapter_dir, adapter_archive_path)
        _merge_lora_to_full_precision(job.base_model_id, adapter_dir, merged_dir)
        _convert_to_gguf(merged_dir, gguf_local_path)

        adapter_remote_path = _upload_file(
            local_path=adapter_archive_path,
            object_name=f"training/jobs/{job.id}/{ADAPTER_ARCHIVE}",
        )
        gguf_remote_path = _upload_file(
            local_path=gguf_local_path,
            object_name=f"training/jobs/{job.id}/{GGUF_FILENAME}",
        )

        model_id = job.model_id or f"finetune_{job.dataset_id}_{job.id}_{uuid4().hex[:6]}"
        job.model_id = model_id

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.metrics = result.metrics
        job.output_path = str(adapter_dir)
        job.adapter_path = adapter_remote_path
        job.merged_path = str(merged_dir)
        job.gguf_local_path = str(gguf_local_path)
        job.artifact_path = gguf_remote_path
        job.gguf_path = gguf_remote_path
        job.validation_status = "queued"
        session.commit()

        model_manager.register_model_config(
            model_id,
            {
                "path": str(gguf_local_path),
                "priority": 1,
                "ttl_seconds": 0,
            },
        )

        task_queue.schedule_model_validation(job_id=job.id)
        return result.to_dict()
    except Exception as exc:  # noqa: BLE001
        logger.error("Fine-tune job %s failed: %s", job_id, exc, exc_info=True)
        if job:
            job.status = "failed"
            job.validation_status = "failed"
            job.error = str(exc)
            session.commit()
        raise
    finally:
        session.close()


def _ensure_dataset_local(dataset: TrainingDataset, session) -> str:
    if dataset.storage_path and Path(dataset.storage_path).exists():
        return dataset.storage_path
    if not dataset.artifact_path:
        raise RuntimeError("Dataset artifact path is missing")
    target_dir = Path(settings.UNSLOTH_OUTPUT_DIR) / "datasets" / f"dataset_{dataset.id}"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "train.jsonl"
    logger.info("Downloading dataset %s from storage", dataset.id)
    data = minio_service.download_file("models", dataset.artifact_path)
    target_file.write_bytes(data)
    dataset.storage_path = str(target_file)
    session.commit()
    return str(target_file)


def _build_request_payload(job: TrainingJob, dataset_path: str) -> Dict[str, object]:
    payload: Dict[str, object] = {
        "dataset_path": dataset_path,
        "output_dir": str(Path(settings.UNSLOTH_OUTPUT_DIR) / "models" / f"job_{job.id}" / "lora"),
        "base_model_id": job.base_model_id,
    }
    hyperparams = job.hyperparameters or {}
    allowed_keys = set(FineTuneRequest.__dataclass_fields__.keys())
    for key, value in hyperparams.items():
        if key in allowed_keys and value is not None:
            payload[key] = value
    return payload


def _archive_adapter_directory(adapter_dir: Path, archive_path: Path) -> None:
    archive_path.unlink(missing_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in adapter_dir.rglob("*"):
            if file.name == ADAPTER_ARCHIVE:
                continue
            if file.is_file():
                zf.write(file, file.relative_to(adapter_dir))
    logger.info("Adapter archived at %s", archive_path)


def _merge_lora_to_full_precision(base_model_id: str, adapter_dir: Path, output_dir: Path) -> None:
    logger.info("Merging LoRA weights into base model %s", base_model_id)
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    tokenizer = AutoTokenizer.from_pretrained(base_model_id)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        torch_dtype=dtype,
        device_map="auto" if torch.cuda.is_available() else None,
    )
    peft_model = PeftModel.from_pretrained(base_model, adapter_dir)
    merged_model = peft_model.merge_and_unload()
    merged_model.to("cpu")
    output_dir.mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    logger.info("Merged model saved to %s", output_dir)


def _convert_to_gguf(model_dir: Path, gguf_path: Path) -> None:
    gguf_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Converting HF model %s to GGUF %s", model_dir, gguf_path)
    cmd = [
        sys.executable,
        "-m",
        "llama_cpp.convert",
        "--outfile",
        str(gguf_path),
        "--outtype",
        settings.UNSLOTH_GGUF_OUTTYPE,
        str(model_dir),
    ]
    subprocess.run(cmd, check=True)
    logger.info("GGUF model created at %s", gguf_path)


def _upload_file(local_path: Path, object_name: str) -> str:
    bucket = "models"
    with local_path.open("rb") as stream:
        minio_service.upload_file(
            bucket_name=bucket,
            object_name=object_name,
            data_stream=stream,
            length=local_path.stat().st_size,
            content_type="application/octet-stream",
        )
    logger.info("Uploaded %s to bucket %s as %s", local_path, bucket, object_name)
    return object_name


__all__ = ["fine_tune_unsloth"]

