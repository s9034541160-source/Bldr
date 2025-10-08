"""
🇷🇺 Локальный российский LLM процессор для RAG пайплайна
Использует бесплатные локальные модели: RuGPT, YaLM, T-Lite
"""

import logging
import torch
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    pipeline,
    BitsAndBytesConfig
)

logger = logging.getLogger(__name__)

@dataclass
class LocalLLMConfig:
    """Конфигурация локального российского LLM"""
    model_name: str = "ai-forever/rugpt3large_based_on_gpt2"  # RuGPT-3.5
    device: str = "auto"  # auto, cuda, cpu
    max_length: int = 4096  # Максимальная длина контекста
    temperature: float = 0.1
    do_sample: bool = True
    use_quantization: bool = True  # Использовать квантизацию для экономии памяти
    cache_dir: str = "./models_cache"

class LocalRussianLLMProcessor:
    """
    Локальный российский LLM процессор для глубокого анализа документов
    Поддерживает RuGPT, YaLM, T-Lite и другие российские модели
    """
    
    def __init__(self, config: LocalLLMConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Инициализация локальной модели"""
        try:
            self.logger.info(f"🔄 Загружаем локальную модель: {self.config.model_name}")
            
            # Настройка квантизации для экономии памяти
            quantization_config = None
            if self.config.use_quantization and torch.cuda.is_available():
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    llm_int8_threshold=6.0,
                    llm_int8_has_fp16_weight=False,
                )
            
            # Загружаем токенизатор
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_name,
                cache_dir=self.config.cache_dir,
                trust_remote_code=True
            )
            
            # Настраиваем pad_token если его нет
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Загружаем модель
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                cache_dir=self.config.cache_dir,
                quantization_config=quantization_config,
                device_map=self.config.device,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                trust_remote_code=True
            )
            
            # Создаем pipeline для удобства использования
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=self.config.device,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            
            self.logger.info(f"✅ Локальная модель загружена: {self.config.model_name}")
            self.logger.info(f"📊 Устройство: {self.model.device}")
            self.logger.info(f"💾 Память GPU: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB" if torch.cuda.is_available() else "CPU режим")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки модели: {e}")
            raise
    
    def analyze_document_structure(self, content: str, vlm_metadata: Dict) -> Dict:
        """
        Глубокий анализ структуры документа с помощью локального российского LLM
        
        Args:
            content: Текст документа
            vlm_metadata: Метаданные от VLM анализа
            
        Returns:
            Dict с результатами анализа
        """
        try:
            # Подготавливаем промпт для российского LLM
            prompt = self._prepare_analysis_prompt(content, vlm_metadata)
            
            # Анализируем с локальным LLM
            analysis_result = self._analyze_with_local_llm(prompt)
            
            return {
                'local_llm_available': True,
                'analysis': analysis_result,
                'model': self.config.model_name,
                'device': str(self.model.device),
                'context_length': len(prompt),
                'processing_time': analysis_result.get('processing_time', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Local LLM analysis failed: {e}")
            return {
                'local_llm_available': False,
                'error': str(e),
                'fallback_to_vlm': True
            }
    
    def _prepare_analysis_prompt(self, content: str, vlm_metadata: Dict) -> str:
        """Подготовка промпта для локального российского LLM"""
        
        # Извлекаем информацию от VLM
        vlm_tables = vlm_metadata.get('tables', [])
        vlm_sections = vlm_metadata.get('sections', [])
        
        # Ограничиваем длину контента для промпта
        max_content_length = self.config.max_length - 500  # Оставляем место для промпта
        truncated_content = content[:max_content_length] if len(content) > max_content_length else content
        
        prompt = f"""Ты - эксперт по анализу строительной документации. Проанализируй документ и извлеки структурированную информацию.

ДОКУМЕНТ:
{truncated_content}

VLM АНАЛИЗ (предварительный):
- Таблицы: {len(vlm_tables)}
- Секции: {len(vlm_sections)}

ЗАДАЧИ:
1. Определи тип документа (СНиП, ГОСТ, ППР, смета, проект)
2. Извлеки основные разделы и подразделы
3. Найди таблицы и их содержимое
4. Выдели ключевые требования и нормы
5. Определи применимость и область действия

ФОРМАТ ОТВЕТА (JSON):
{{
    "document_type": "тип документа",
    "sections": [
        {{
            "title": "название раздела",
            "content": "содержимое",
            "level": 1
        }}
    ],
    "tables": [
        {{
            "title": "название таблицы",
            "data": "данные таблицы"
        }}
    ],
    "requirements": [
        "ключевое требование 1",
        "ключевое требование 2"
    ],
    "scope": "область применения"
}}

Отвечай только JSON, без дополнительного текста."""
        
        return prompt
    
    def _analyze_with_local_llm(self, prompt: str) -> Dict:
        """Анализ с локальным LLM"""
        start_time = time.time()
        
        try:
            # Генерируем ответ с помощью pipeline
            response = self.pipeline(
                prompt,
                max_length=min(len(prompt) + 1000, self.config.max_length),
                temperature=self.config.temperature,
                do_sample=self.config.do_sample,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                return_full_text=False
            )
            
            # Извлекаем сгенерированный текст
            generated_text = response[0]['generated_text'].strip()
            
            # Пытаемся найти JSON в ответе
            json_start = generated_text.find('{')
            json_end = generated_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = generated_text[json_start:json_end]
                try:
                    analysis = json.loads(json_text)
                    processing_time = time.time() - start_time
                    analysis['processing_time'] = processing_time
                    return analysis
                except json.JSONDecodeError:
                    self.logger.warning("Не удалось распарсить JSON из ответа LLM")
                    return {"error": "JSON parsing failed", "raw_response": generated_text}
            else:
                self.logger.warning("JSON не найден в ответе LLM")
                return {"error": "No JSON found", "raw_response": generated_text}
                
        except Exception as e:
            self.logger.error(f"Ошибка генерации LLM: {e}")
            return {"error": str(e), "processing_time": time.time() - start_time}
    
    def get_model_info(self) -> Dict:
        """Получение информации о модели"""
        return {
            'model_name': self.config.model_name,
            'device': str(self.model.device) if self.model else 'not_loaded',
            'max_length': self.config.max_length,
            'quantization': self.config.use_quantization,
            'cache_dir': self.config.cache_dir
        }

# Пример использования
if __name__ == "__main__":
    # Конфигурация для RuGPT-3.5
    config = LocalLLMConfig(
        model_name="ai-forever/rugpt3large_based_on_gpt2",
        device="auto",
        max_length=2048,
        use_quantization=True
    )
    
    # Создание процессора
    processor = LocalRussianLLMProcessor(config)
    
    # Тестовый анализ
    test_content = "Это тестовый документ для анализа структуры."
    vlm_metadata = {"tables": [], "sections": []}
    
    result = processor.analyze_document_structure(test_content, vlm_metadata)
    print(f"Результат анализа: {result}")
    print(f"Информация о модели: {processor.get_model_info()}")
