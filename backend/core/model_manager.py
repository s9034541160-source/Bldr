"""
Менеджер для управления локальными LLM моделями
"""

from llama_cpp import Llama
from backend.config.settings import settings
import logging
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)


class ModelManager:
    """Менеджер для управления локальными GGUF моделями"""
    
    def __init__(self):
        self.models: Dict[str, Llama] = {}
        self.current_model: Optional[str] = None
    
    def load_model(
        self,
        model_path: str,
        model_id: str = "default",
        n_ctx: int = 4096,
        n_gpu_layers: int = 0,
        verbose: bool = False
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
            
            self.models[model_id] = model
            if not self.current_model:
                self.current_model = model_id
            
            logger.info(f"Model {model_id} loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            return False
    
    def unload_model(self, model_id: str) -> bool:
        """Выгрузка модели"""
        if model_id in self.models:
            del self.models[model_id]
            if self.current_model == model_id:
                self.current_model = None
            logger.info(f"Model {model_id} unloaded")
            return True
        return False
    
    def get_model(self, model_id: Optional[str] = None) -> Optional[Llama]:
        """Получение модели"""
        model_id = model_id or self.current_model
        if model_id and model_id in self.models:
            return self.models[model_id]
        return None
    
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
        model = self.get_model(model_id)
        if not model:
            return None
        
        return {
            "model_id": model_id or self.current_model,
            "n_ctx": getattr(model, "n_ctx", None),
            "n_gpu_layers": getattr(model, "n_gpu_layers", None),
        }
    
    def list_models(self) -> list[str]:
        """Список загруженных моделей"""
        return list(self.models.keys())


# Глобальный экземпляр менеджера моделей
model_manager = ModelManager()

