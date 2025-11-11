"""
DeepSeek-OCR integration powered by Unsloth accelerated loading.
"""

from __future__ import annotations

import io
import logging
from functools import lru_cache
from typing import Optional

import torch
from PIL import Image
from transformers import AutoProcessor
from unsloth import FastLanguageModel

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class DeepseekOCRService:
    """Обёртка над мультимодальной моделью DeepSeek для OCR и семантического анализа."""

    def __init__(self) -> None:
        self.model_id = settings.DEEPSEEK_OCR_MODEL
        self.max_new_tokens = settings.DEEPSEEK_OCR_MAX_NEW_TOKENS
        self.prompt = settings.DEEPSEEK_OCR_PROMPT
        self.device = settings.DEEPSEEK_OCR_DEVICE
        self.load_in_4bit = settings.DEEPSEEK_OCR_LOAD_IN_4BIT
        self._model: Optional[torch.nn.Module] = None
        self._tokenizer = None
        self._processor = None

    def _load(self) -> None:
        if self._model is not None:
            return
        logger.info("Loading DeepSeek-OCR model %s", self.model_id)
        self._model, self._tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.model_id,
            max_seq_length=settings.UNSLOTH_MAX_SEQ_LENGTH,
            dtype="bfloat16",
            load_in_4bit=self.load_in_4bit,
        )
        FastLanguageModel.for_inference(self._model)
        self._processor = AutoProcessor.from_pretrained(self.model_id)

    def extract_text(self, image_bytes: bytes, prompt: Optional[str] = None, max_new_tokens: Optional[int] = None) -> str:
        """
        Распознаёт текст на изображении, выполняя при необходимости дополнительную инструкцию.

        Args:
            image_bytes: Байтовое представление изображения.
            prompt: Пользовательская инструкция для модели. Если не указана, применяется стандартный OCR-промпт.
            max_new_tokens: Ограничение на количество генерируемых токенов (при None используется значение из настроек).

        Returns:
            Распознанный текст/JSON, приведённый моделью.
        """
        if not image_bytes:
            return ""
        self._load()
        assert self._processor is not None
        instruction = prompt or self.prompt
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        inputs = self._processor(
            images=image,
            text=instruction,
            return_tensors="pt",
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        tokens_limit = max_new_tokens or self.max_new_tokens
        with torch.inference_mode():
            output_ids = self._model.generate(
                **inputs,
                max_new_tokens=tokens_limit,
            )
        generated = self._tokenizer.batch_decode(output_ids, skip_special_tokens=True)
        return (generated[0] if generated else "").strip()

    def extract_structured(self, image_bytes: bytes, instruction: str, *, max_new_tokens: Optional[int] = None) -> str:
        """
        Выполняет OCR и просит модель вернуть структурированные данные (например, JSON).
        """
        return self.extract_text(image_bytes, prompt=instruction, max_new_tokens=max_new_tokens)


@lru_cache(maxsize=1)
def get_deepseek_service() -> DeepseekOCRService:
    return DeepseekOCRService()


deepseek_ocr_service = get_deepseek_service()


__all__ = ["deepseek_ocr_service", "DeepseekOCRService", "get_deepseek_service"]

