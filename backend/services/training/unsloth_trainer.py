"""
Utilities for fine-tuning language models via Unsloth.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from datasets import load_dataset
from unsloth import FastLanguageModel
from unsloth.trainer import SFTTrainer
from unsloth.utils import UnslothTrainingArguments

from backend.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class FineTuneRequest:
    dataset_path: str
    output_dir: Optional[str] = None
    base_model_id: Optional[str] = None
    max_seq_length: Optional[int] = None
    lora_r: Optional[int] = None
    lora_alpha: Optional[int] = None
    lora_dropout: Optional[float] = None
    batch_size: Optional[int] = None
    gradient_accumulation: Optional[int] = None
    learning_rate: Optional[float] = None
    epochs: Optional[int] = None
    evaluation_dataset_path: Optional[str] = None
    save_steps: int = 100
    logging_steps: int = 10
    warmup_steps: int = 100
    dtype: str = "bfloat16"
    load_in_4bit: bool = True


@dataclass(slots=True, kw_only=True)
class FineTuneResult:
    model_path: str
    tokenizer_path: str
    epochs_ran: int
    train_loss: Optional[float] = None
    eval_loss: Optional[float] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UnslothFineTuner:
    """Wrapper around Unsloth utilities to standardise training pipeline."""

    def __init__(self) -> None:
        self.default_model = settings.UNSLOTH_DEFAULT_MODEL

    def _resolve_config(self, request: FineTuneRequest) -> Dict[str, Any]:
        return {
            "output_dir": request.output_dir or settings.UNSLOTH_OUTPUT_DIR,
            "base_model": request.base_model_id or self.default_model,
            "max_seq_length": request.max_seq_length or settings.UNSLOTH_MAX_SEQ_LENGTH,
            "lora_r": request.lora_r or settings.UNSLOTH_LORA_R,
            "lora_alpha": request.lora_alpha or settings.UNSLOTH_LORA_ALPHA,
            "lora_dropout": request.lora_dropout or settings.UNSLOTH_LORA_DROPOUT,
            "batch_size": request.batch_size or settings.UNSLOTH_BATCH_SIZE,
            "gradient_accumulation_steps": request.gradient_accumulation or settings.UNSLOTH_GRADIENT_ACCUMULATION,
            "learning_rate": request.learning_rate or settings.UNSLOTH_LEARNING_RATE,
            "epochs": request.epochs or settings.UNSLOTH_EPOCHS,
            "dtype": request.dtype,
            "load_in_4bit": request.load_in_4bit,
            "save_steps": request.save_steps,
            "logging_steps": request.logging_steps,
            "warmup_steps": request.warmup_steps,
        }

    def train(self, request: FineTuneRequest) -> FineTuneResult:
        config = self._resolve_config(request)
        Path(config["output_dir"]).mkdir(parents=True, exist_ok=True)

        logger.info("Loading base model %s via Unsloth", config["base_model"])
        model, tokenizer = FastLanguageModel.from_pretrained(
            config["base_model"],
            max_seq_length=config["max_seq_length"],
            dtype=config["dtype"],
            load_in_4bit=config["load_in_4bit"],
        )

        FastLanguageModel.for_training(
            model,
            use_gradient_checkpointing=True,
            lora_r=config["lora_r"],
            lora_alpha=config["lora_alpha"],
            lora_dropout=config["lora_dropout"],
        )

        dataset = self._load_dataset(request.dataset_path)
        eval_dataset = (
            self._load_dataset(request.evaluation_dataset_path)
            if request.evaluation_dataset_path
            else None
        )

        training_args = UnslothTrainingArguments(
            output_dir=config["output_dir"],
            per_device_train_batch_size=config["batch_size"],
            gradient_accumulation_steps=config["gradient_accumulation_steps"],
            warmup_steps=config["warmup_steps"],
            logging_steps=config["logging_steps"],
            save_steps=config["save_steps"],
            learning_rate=config["learning_rate"],
            num_train_epochs=config["epochs"],
            optim="adamw_torch",
            report_to="none",
        )

        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            args=training_args,
            train_dataset=dataset["train"],
            eval_dataset=(eval_dataset["validation"] if eval_dataset and "validation" in eval_dataset else None),
            dataset_text_field="text",
            packing=True,
        )

        train_metrics = trainer.train()
        trainer.save_model(config["output_dir"])
        tokenizer.save_pretrained(config["output_dir"])

        metrics = train_metrics.metrics or {}
        logger.info("Unsloth training finished: %s", metrics)

        return FineTuneResult(
            model_path=str(Path(config["output_dir"]) / "adapter_model.bin"),
            tokenizer_path=config["output_dir"],
            epochs_ran=int(metrics.get("epoch", config["epochs"])),
            train_loss=metrics.get("train_loss"),
            eval_loss=metrics.get("eval_loss"),
            metrics=metrics,
        )

    def _load_dataset(self, path: Optional[str]):
        if not path:
            raise ValueError("Dataset path is required")
        source = Path(path)
        if source.is_file() and source.suffix in {".json", ".jsonl"}:
            return load_dataset(
                "json",
                data_files={"train": str(source)},
            )
        if source.is_dir():
            return load_dataset(str(source))
        return load_dataset(path)


__all__ = ["UnslothFineTuner", "FineTuneRequest", "FineTuneResult"]

