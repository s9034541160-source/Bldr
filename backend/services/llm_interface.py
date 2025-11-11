"""
Унифицированный интерфейс взаимодействия с LLM (локальные GGUF и облачные API).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class LLMProviderError(Exception):
    """Базовое исключение LLM-провайдера."""


class BaseLLMClient:
    """
    Базовый клиент: реализует send_instruction и возвращает текст.
    """

    def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError

    def generate_structured(self, prompt: str, schema: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Запрашивает у модели структуру данных в формате JSON.

        Args:
            prompt: текстовое задание.
            schema: ожидаемая структура (если передана, используется в инструкциях).

        Returns:
            JSON-объект.
        """
        instruction = prompt
        if schema:
            schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
            instruction += (
                "\n\nВерни строго валидный JSON, соответствующий схеме:\n"
                f"{schema_str}\n"
                "Не добавляй комментариев и пояснений."
            )
        raw = self.generate(instruction, **kwargs)
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise LLMProviderError("LLM не вернула корректный JSON.")
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMProviderError(f"Ошибка JSON-десериализации: {exc}") from exc


# ------------------------------------------------------------------------------
# Локальный GGUF через LM Studio / OpenAI совместимый API
# ------------------------------------------------------------------------------


class LocalLLMClient(BaseLLMClient):
    """Клиент для локальных моделей (LM Studio, ollama), работающих по OpenAI API."""

    def __init__(self, base_url: str, model: str) -> None:
        from openai import OpenAI

        self.client = OpenAI(base_url=base_url, api_key="EMPTY")  # ключ не используется
        self.model = model

    def generate(self, prompt: str, **kwargs) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                temperature=kwargs.get("temperature", 0.2),
                max_output_tokens=kwargs.get("max_tokens", 1024),
            )
            return response.output_text.strip()
        except Exception as exc:  # noqa: BLE001
            raise LLMProviderError(f"Local LLM generation failed: {exc}") from exc


# ------------------------------------------------------------------------------
# Облачный OpenAI-совместимый клиент
# ------------------------------------------------------------------------------


class RemoteLLMClient(BaseLLMClient):
    """Клиент для облачных поставщиков (OpenAI, Azure, Together)."""

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        from openai import OpenAI

        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def generate(self, prompt: str, **kwargs) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                temperature=kwargs.get("temperature", 0.1),
                max_output_tokens=kwargs.get("max_tokens", 2048),
            )
            return response.output_text.strip()
        except Exception as exc:  # noqa: BLE001
            raise LLMProviderError(f"Remote LLM generation failed: {exc}") from exc


# ------------------------------------------------------------------------------
# Фабрика клиентов
# ------------------------------------------------------------------------------


def get_llm_client(provider: str | None = None) -> BaseLLMClient:
    """
    Возвращает клиент согласно настройкам.
    """
    target = provider or settings.LLM_PROVIDER
    if target == "local":
        return LocalLLMClient(base_url=settings.LLM_LOCAL_API_URL, model=settings.LLM_LOCAL_MODEL)
    if target == "openai":
        return RemoteLLMClient(base_url=settings.LLM_REMOTE_API_URL, api_key=settings.LLM_REMOTE_API_KEY, model=settings.LLM_REMOTE_MODEL)
    raise ValueError(f"Unsupported LLM provider: {target}")


