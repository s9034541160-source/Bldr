"""
Менеджер для управления локальными LLM моделями
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
import os

from llama_cpp import Llama

from backend.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class ModelCacheEntry:
    """Запись о загруженной модели в кэше"""

    instance: Llama
    model_path: str
    loaded_at: datetime
    last_accessed: datetime
    ttl_seconds: int
    memory_size_bytes: int
    priority: int = 0

    @property
    def expires_at(self) -> Optional[datetime]:
        if self.ttl_seconds <= 0:
            return None
        return self.last_accessed + timedelta(seconds=self.ttl_seconds)

    def touch(self) -> None:
        """Обновить время последнего использования"""
        self.last_accessed = datetime.utcnow()

    def to_dict(self, model_id: str) -> Dict[str, Any]:
        """Сериализация информации о модели"""
        data = {
            "model_id": model_id,
            "model_path": self.model_path,
            "loaded_at": self.loaded_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "memory_size_bytes": self.memory_size_bytes,
            "priority": self.priority,
        }
        expires = self.expires_at
        if expires:
            data["expires_at"] = expires.isoformat()
        return data


class ModelManager:
    """Менеджер для управления локальными GGUF моделями"""
    
    def __init__(self):
        self.models: Dict[str, ModelCacheEntry] = {}
        self.current_model: Optional[str] = None
        self._max_models: int = max(1, settings.LLM_MAX_LOADED_MODELS)
        self._default_ttl: int = max(0, settings.LLM_MODEL_TTL_SECONDS)

    def _update_settings_cache(self) -> None:
        """Обновление настроек TTL и лимита моделей"""
        self._max_models = max(1, settings.LLM_MAX_LOADED_MODELS)
        self._default_ttl = max(0, settings.LLM_MODEL_TTL_SECONDS)

    def _cleanup_expired_models(self) -> None:
        """Автоматическая выгрузка моделей, просроченных по TTL"""
        now = datetime.utcnow()
        expired: List[str] = []
        for model_id, entry in list(self.models.items()):
            ttl = entry.ttl_seconds
            if ttl <= 0:
                continue
            if (now - entry.last_accessed).total_seconds() >= ttl:
                expired.append(model_id)
        for model_id in expired:
            self._unload_internal(model_id, reason="ttl_expired")

    def _enforce_capacity_limit(self) -> None:
        """Выгружает наименее используемые модели при превышении лимита"""
        if len(self.models) <= self._max_models:
            return
        # сортируем: низкий приоритет → более старые обращения выгружаются первыми
        sorted_models = sorted(
            self.models.items(),
            key=lambda item: (item[1].priority, item[1].last_accessed)
        )
        while len(sorted_models) > self._max_models:
            model_id, _ = sorted_models.pop(0)
            self._unload_internal(model_id, reason="capacity_limit")
            sorted_models = sorted(
                self.models.items(),
                key=lambda item: (item[1].priority, item[1].last_accessed)
            )

    def _unload_internal(self, model_id: str, reason: str = "manual") -> bool:
        """Внутренний метод выгрузки модели"""
        entry = self.models.pop(model_id, None)
        if not entry:
            return False

        # llama.cpp не требует явного освобождения, GC освободит ресурсы.
        if self.current_model == model_id:
            self.current_model = None

        logger.info(
            "Model %s unloaded (reason=%s, last_accessed=%s)",
            model_id,
            reason,
            entry.last_accessed.isoformat()
        )
        return True
    
    def load_model(
        self,
        model_path: str,
        model_id: str = "default",
        n_ctx: int = 4096,
        n_gpu_layers: int = 0,
        verbose: bool = False,
        ttl_seconds: Optional[int] = None,
        priority: Optional[int] = None,
    ) -> bool:
        """
        Загрузка модели
        
        Args:
            model_path: Путь к GGUF файлу модели
            model_id: Идентификатор модели
            n_ctx: Размер контекста
            n_gpu_layers: Количество слоев на GPU (0 = CPU only)
            verbose: Вывод подробной информации
        """
        try:
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                return False
            
            logger.info(f"Loading model {model_id} from {model_path}")
            
            model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                verbose=verbose
            )
            
            self._update_settings_cache()

            memory_size = 0
            try:
                memory_size = os.path.getsize(model_path)
            except OSError:
                logger.debug("Unable to determine model file size for %s", model_path)

            ttl_value = self._default_ttl if ttl_seconds is None else max(0, ttl_seconds)

            entry = ModelCacheEntry(
                instance=model,
                model_path=model_path,
                loaded_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                ttl_seconds=ttl_value,
                memory_size_bytes=memory_size,
                priority=priority if priority is not None else 0,
            )

            self.models[model_id] = entry
            if not self.current_model:
                self.current_model = model_id

            self._enforce_capacity_limit()
            
            logger.info(f"Model {model_id} loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            return False
    
    def unload_model(self, model_id: str) -> bool:
        """Выгрузка модели"""
        return self._unload_internal(model_id)
    
    def get_model(self, model_id: Optional[str] = None) -> Optional[Llama]:
        """Получение модели"""
        self._cleanup_expired_models()
        model_id = model_id or self.current_model
        if not model_id:
            return None
        entry = self.models.get(model_id)
        if not entry:
            return None
        entry.touch()
        if not self.current_model:
            self.current_model = model_id
        return entry.instance
    
    def generate(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        repeat_penalty: float = 1.1,
        stop: Optional[list] = None
    ) -> Optional[str]:
        """
        Генерация текста
        
        Args:
            prompt: Промпт для генерации
            model_id: Идентификатор модели (если None, используется текущая)
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации
            top_p: Top-p sampling
            top_k: Top-k sampling
            repeat_penalty: Штраф за повторения
            stop: Список стоп-слов
        """
        model = self.get_model(model_id)
        if not model:
            logger.error("No model available")
            return None
        
        try:
            response = model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=stop or []
            )
            
            # Извлечение текста из ответа
            if response and "choices" in response and len(response["choices"]) > 0:
                return response["choices"][0]["text"]
            
            return None
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return None
    
    def get_model_info(self, model_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Получение информации о модели"""
        self._cleanup_expired_models()
        model_id = model_id or self.current_model
        if not model_id:
            return None
        entry = self.models.get(model_id)
        if not entry:
            return None

        model = entry.instance
        info = entry.to_dict(model_id)
        info.update(
            {
                "n_ctx": getattr(model, "n_ctx", None),
                "n_gpu_layers": getattr(model, "n_gpu_layers", None),
            }
        )
        return info
    
    def list_models(self) -> List[Dict[str, Any]]:
        """Список загруженных моделей"""
        self._cleanup_expired_models()
        return [
            entry.to_dict(model_id)
            for model_id, entry in self.models.items()
        ]

    def get_memory_usage(self) -> Dict[str, Any]:
        """Отчет по использованию памяти"""
        total_memory = sum(entry.memory_size_bytes for entry in self.models.values())
        return {
            "total_memory_bytes": total_memory,
            "models": [
                {
                    "model_id": model_id,
                    "memory_size_bytes": entry.memory_size_bytes,
                    "last_accessed": entry.last_accessed.isoformat(),
                    "priority": entry.priority,
                }
                for model_id, entry in self.models.items()
            ],
        }

    def set_model_priority(self, model_id: str, priority: int) -> bool:
        """Установка приоритета для модели"""
        self._cleanup_expired_models()
        entry = self.models.get(model_id)
        if not entry:
            return False
        entry.priority = priority
        entry.touch()
        logger.info("Model %s priority set to %s", model_id, priority)
        return True


# Глобальный экземпляр менеджера моделей
model_manager = ModelManager()

