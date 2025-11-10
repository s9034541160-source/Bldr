"""
Dataset builder for automated fine-tuning pipeline.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy.orm import Session

from backend.config.settings import settings
from backend.core.model_manager import model_manager
from backend.models.document import Document, DocumentVersion
from backend.models.training import TrainingDataset
from backend.services.document_parser import get_document_parser
from backend.services.minio_service import minio_service
from backend.services.ocr.deepseek_service import deepseek_ocr_service

logger = logging.getLogger(__name__)

DEFAULT_PROMPT = """You are an assistant helping to create high-quality question-answer pairs for fine-tuning an LLM.
Given the following fragment of a construction-related document, generate {num_pairs} diverse factual questions with detailed answers.
Structure your response strictly as JSON array with fields "question" and "answer".
Use Russian language if the context is Russian, otherwise follow the context language.
Return only valid JSON.

Context:
{context}
"""


@dataclass(slots=True)
class DatasetBuildResult:
    total_examples: int
    preview: List[Dict[str, Any]]
    storage_path: str
    artifact_path: str


class TrainingDatasetBuilder:
    """Builds instruction datasets from selected documents."""

    def __init__(self, db: Session):
        self.db = db
        self.dataset_root = Path(settings.UNSLOTH_OUTPUT_DIR) / "datasets"
        self.dataset_root.mkdir(parents=True, exist_ok=True)
        self.document_parser = get_document_parser()

    def build(self, dataset_id: int) -> DatasetBuildResult:
        dataset = (
            self.db.query(TrainingDataset)
            .filter(TrainingDataset.id == dataset_id)
            .with_for_update()
            .one_or_none()
        )
        if not dataset:
            raise ValueError(f"TrainingDataset {dataset_id} not found")

        dataset.status = "building"
        dataset.error = None
        self.db.commit()

        config = dataset.config or {}
        num_pairs = int(config.get("questions_per_chunk", 5))
        total_pairs_target = int(config.get("total_pairs_target", 0))
        qa_model_id = config.get("qa_model_id")
        prompt_template = config.get("prompt_template") or DEFAULT_PROMPT

        output_dir = self.dataset_root / f"dataset_{dataset.id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "train.jsonl"

        examples: List[Dict[str, Any]] = []
        source_documents = self._normalize_source_documents(dataset.source_documents)

        for item in source_documents:
            document = self.db.query(Document).filter(Document.id == item["document_id"]).one_or_none()
            if not document:
                logger.warning("Document %s not found, skipping", item["document_id"])
                continue
            logger.info("Building dataset from document %s", document.id)
            doc_examples = self._process_document(
                document=document,
                prompt_template=prompt_template,
                qa_model_id=qa_model_id,
                num_pairs=num_pairs,
                max_examples=None,
            )
            examples.extend(doc_examples)
            if total_pairs_target and len(examples) >= total_pairs_target:
                logger.info("Reached target of %s examples, stopping dataset generation", total_pairs_target)
                break

        if not examples:
            raise RuntimeError("No examples generated for dataset")

        with output_file.open("w", encoding="utf-8") as handle:
            for example in examples:
                json.dump(example, handle, ensure_ascii=False)
                handle.write("\n")

        minio_object = f"training/datasets/{dataset.id}/train.jsonl"
        minio_service.upload_file(
            bucket_name="models",
            object_name=minio_object,
            data=output_file.read_bytes(),
            content_type="application/json",
        )

        preview = examples[: min(5, len(examples))]
        dataset.status = "ready"
        dataset.total_examples = len(examples)
        dataset.storage_path = str(output_file)
        dataset.artifact_path = minio_object
        dataset.sample_preview = preview
        from datetime import datetime

        dataset.updated_at = datetime.utcnow()
        self.db.commit()

        return DatasetBuildResult(
            total_examples=len(examples),
            preview=preview,
            storage_path=str(output_file),
            artifact_path=minio_object,
        )

    def _normalize_source_documents(self, raw: Iterable[Any]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for item in raw:
            if isinstance(item, int):
                normalized.append({"document_id": item})
            elif isinstance(item, dict):
                doc_id = item.get("document_id") or item.get("id")
                if doc_id is None:
                    continue
                normalized.append({"document_id": int(doc_id)})
        return normalized

    def _process_document(
        self,
        *,
        document: Document,
        prompt_template: str,
        qa_model_id: Optional[str],
        num_pairs: int,
        max_examples: int,
    ) -> List[Dict[str, Any]]:
        version = (
            self.db.query(DocumentVersion)
            .filter(
                DocumentVersion.document_id == document.id,
                DocumentVersion.version_number == document.version,
            )
            .one_or_none()
        )
        file_path = version.file_path if version else document.file_path
        file_bytes = minio_service.download_file("documents", file_path)

        suffix = Path(document.file_name or "document").suffix or ".bin"
        with NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
            tmp.write(file_bytes)
            tmp.flush()
            chunks = self.document_parser.extract_chunks_from_file(tmp.name)

        # fallback to OCR if no text chunks or original file is an image
        if not chunks and document.mime_type and document.mime_type.startswith("image/"):
            text_content = deepseek_ocr_service.extract_text(file_bytes)
            chunks = self.document_parser.chunk_text(text_content) if text_content else []

        examples: List[Dict[str, Any]] = []
        for idx, chunk in enumerate(chunks):
            context = chunk.text.strip()
            if not context:
                continue
            prompt = prompt_template.format(context=context, num_pairs=num_pairs)
            qa_pairs = self._generate_pairs(prompt, qa_model_id, expected=num_pairs)
            for pair in qa_pairs:
                examples.append(
                    {
                        "instruction": pair["question"],
                        "input": "",
                        "output": pair["answer"],
                        "text": self._format_instruction(pair["question"], pair["answer"]),
                        "metadata": {
                            "document_id": document.id,
                            "chunk_index": idx,
                            "title": chunk.title,
                        },
                    }
                )
        return examples

    def _generate_pairs(
        self,
        prompt: str,
        model_id: Optional[str],
        expected: int,
    ) -> List[Dict[str, str]]:
        try:
            response = model_manager.generate(prompt=prompt, model_id=model_id)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to generate QA pairs: %s", exc, exc_info=True)
            return []

        try:
            data = json.loads(response)
            if isinstance(data, dict):
                data = data.get("pairs") or data.get("qa") or []
            if not isinstance(data, list):
                return []
            pairs = []
            for item in data:
                question = item.get("question") if isinstance(item, dict) else None
                answer = item.get("answer") if isinstance(item, dict) else None
                if question and answer:
                    pairs.append({"question": question.strip(), "answer": answer.strip()})
            if len(pairs) >= expected:
                return pairs
            return pairs
        except json.JSONDecodeError:
            logger.warning("Model returned non-JSON response; falling back to heuristic parsing")
            return self._parse_fallback(response, expected)

    def _parse_fallback(self, text: str, expected: int) -> List[Dict[str, str]]:
        pairs: List[Dict[str, str]] = []
        for block in text.split("\n\n"):
            if len(pairs) >= expected:
                break
            if ":" not in block:
                continue
            lines = block.splitlines()
            question = None
            answer_parts: List[str] = []
            for line in lines:
                if line.lower().startswith("вопрос") or line.lower().startswith("question"):
                    question = line.split(":", 1)[-1].strip()
                elif line.lower().startswith("ответ") or line.lower().startswith("answer"):
                    answer_parts.append(line.split(":", 1)[-1].strip())
                else:
                    answer_parts.append(line.strip())
            if question and answer_parts:
                pairs.append({"question": question, "answer": " ".join(answer_parts).strip()})
        return pairs

    @staticmethod
    def _format_instruction(question: str, answer: str) -> str:
        return f"### Instruction:\n{question.strip()}\n\n### Response:\n{answer.strip()}"


__all__ = ["TrainingDatasetBuilder", "DatasetBuildResult"]

