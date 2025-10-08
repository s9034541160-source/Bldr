"""
🇷🇺 Ансамбль российских LLM для максимального качества RAG пайплайна
Stage 4: RuLongformer (классификация) + Stage 8: RuT5 (извлечение) + Stage 5.5: RuGPT (анализ)
"""

import logging
import torch
import json
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    AutoModelForSeq2SeqLM,
    pipeline,
    BitsAndBytesConfig
)

logger = logging.getLogger(__name__)

@dataclass
class RussianLLMEnsembleConfig:
    """Конфигурация ансамбля российских LLM"""
    # Stage 4: RuT5 для классификации (на CPU)
    classification_model: str = "ai-forever/ruT5-base"  # ✅ ПРАВИЛЬНЫЙ RuT5
    classification_max_length: int = 2048
    
    # Stage 8: RuT5 для извлечения метаданных (на CPU)
    extraction_model: str = "ai-forever/ruT5-base"  # ✅ ПРАВИЛЬНЫЙ RuT5
    extraction_max_length: int = 2048
    
    # Stage 5.5: RuT5 для анализа (на CPU)
    analysis_model: str = "ai-forever/ruT5-base"  # ✅ ПРАВИЛЬНЫЙ RuT5
    analysis_max_length: int = 2048
    
    # Общие настройки
    device: str = "cpu"  # ✅ ВСЕ МОДЕЛИ НА CPU
    use_quantization: bool = False  # ✅ БЕЗ КВАНТИЗАЦИИ ДЛЯ CPU
    cache_dir: str = "./models_cache"
    temperature: float = 0.1

class RussianLLMEnsemble:
    """
    Ансамбль российских LLM для разных задач RAG пайплайна
    Stage 4: Классификация документов (RuLongformer)
    Stage 8: Извлечение метаданных (RuT5) 
    Stage 5.5: Глубокий анализ (RuGPT)
    """
    
    def __init__(self, config: RussianLLMEnsembleConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Инициализируем модели
        self.classification_model = None
        self.classification_tokenizer = None
        self.extraction_model = None
        self.extraction_tokenizer = None
        self.analysis_model = None
        self.analysis_tokenizer = None
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Инициализация всех моделей ансамбля"""
        try:
            self.logger.info("🔄 Инициализация ансамбля российских LLM...")
            
            # Настройка квантизации
            # Отключаем квантизацию для стабильности
            quantization_config = None
            # if self.config.use_quantization and torch.cuda.is_available():
            #     quantization_config = BitsAndBytesConfig(
            #         load_in_8bit=True,
            #         llm_int8_threshold=6.0,
            #         llm_int8_has_fp16_weight=False,
            #     )
            
            # Stage 4: Модель для классификации документов
            self._initialize_classification_model(quantization_config)
            
            # Stage 8: Модель для извлечения метаданных
            self._initialize_extraction_model(quantization_config)
            
            # Stage 5.5: Модель для анализа
            self._initialize_analysis_model(quantization_config)
            
            self.logger.info("✅ Ансамбль российских LLM инициализирован")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации ансамбля: {e}")
            raise
    
    def _initialize_classification_model(self, quantization_config):
        """Инициализация модели для классификации (Stage 4)"""
        try:
            self.logger.info(f"📋 Загрузка модели классификации: {self.config.classification_model}")
            
            # Загружаем токенизатор RuT5 с принудительным slow tokenizer
            self.classification_tokenizer = AutoTokenizer.from_pretrained(
                self.config.classification_model,
                cache_dir=self.config.cache_dir,
                use_fast=False,  # ⬅️ КРИТИЧЕСКАЯ ПРАВКА ДЛЯ WINDOWS/RuT5
                trust_remote_code=True
            )
            
            if self.classification_tokenizer.pad_token is None:
                self.classification_tokenizer.pad_token = self.classification_tokenizer.eos_token
            
            # RuT5 отправляем на CPU, чтобы Qwen'у хватило VRAM!
            self.classification_model = AutoModelForSeq2SeqLM.from_pretrained(
                self.config.classification_model,
                cache_dir=self.config.cache_dir,
                trust_remote_code=True,
                torch_dtype=torch.float32  # ✅ float32 для CPU
            ).to("cpu")  # ✅ ПРИНУДИТЕЛЬНО НА CPU
            
            # Проверяем, что модель загружена
            if self.classification_model is not None:
                self.logger.info("✅ Модель классификации загружена успешно")
                self.logger.info(f"📊 Устройство модели: {self.classification_model.device}")
            else:
                self.logger.error("❌ Модель классификации не загружена")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки модели классификации: {e}")
            self.classification_model = None
    
    def _initialize_extraction_model(self, quantization_config):
        """Инициализация модели для извлечения (Stage 8) - RuT5 на CPU"""
        try:
            self.logger.info(f"🔍 Загрузка модели извлечения: {self.config.extraction_model}")
            
            # Загружаем токенизатор RuT5 с принудительным slow tokenizer
            self.extraction_tokenizer = AutoTokenizer.from_pretrained(
                self.config.extraction_model,
                cache_dir=self.config.cache_dir,
                use_fast=False,  # ⬅️ КРИТИЧЕСКАЯ ПРАВКА ДЛЯ WINDOWS/RuT5
                trust_remote_code=True
            )
            
            if self.extraction_tokenizer.pad_token is None:
                self.extraction_tokenizer.pad_token = self.extraction_tokenizer.eos_token
            
            # RuT5 отправляем на CPU, чтобы Qwen'у хватило VRAM!
            self.extraction_model = AutoModelForSeq2SeqLM.from_pretrained(
                self.config.extraction_model,
                cache_dir=self.config.cache_dir,
                trust_remote_code=True,
                torch_dtype=torch.float32  # ✅ float32 для CPU
            ).to("cpu")  # ✅ ПРИНУДИТЕЛЬНО НА CPU
            
            self.logger.info("✅ Модель извлечения (RuT5) загружена на CPU")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки модели извлечения: {e}")
            self.extraction_model = None
    
    def _initialize_analysis_model(self, quantization_config):
        """Инициализация модели для анализа (Stage 5.5) - RuT5 на CPU"""
        try:
            self.logger.info(f"🧠 Загрузка модели анализа: {self.config.analysis_model}")
            
            # Загружаем токенизатор RuT5 с принудительным slow tokenizer
            self.analysis_tokenizer = AutoTokenizer.from_pretrained(
                self.config.analysis_model,
                cache_dir=self.config.cache_dir,
                use_fast=False,  # ⬅️ КРИТИЧЕСКАЯ ПРАВКА ДЛЯ WINDOWS/RuT5
                trust_remote_code=True
            )
            
            if self.analysis_tokenizer.pad_token is None:
                self.analysis_tokenizer.pad_token = self.analysis_tokenizer.eos_token
            
            # RuT5 отправляем на CPU, чтобы Qwen'у хватило VRAM!
            self.analysis_model = AutoModelForSeq2SeqLM.from_pretrained(
                self.config.analysis_model,
                cache_dir=self.config.cache_dir,
                trust_remote_code=True,
                torch_dtype=torch.float32  # ✅ float32 для CPU
            ).to("cpu")  # ✅ ПРИНУДИТЕЛЬНО НА CPU
            
            self.logger.info("✅ Модель анализа (RuT5) загружена на CPU")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки модели анализа: {e}")
            self.analysis_model = None
    
    def stage_4_classify_document(self, content: str) -> Dict:
        """
        Stage 4: Классификация типа документа с RuLongformer
        Анализирует полный контекст первой страницы (4096+ токенов)
        """
        try:
            if self.classification_model is None:
                return {'classification_available': False, 'error': 'Model not loaded'}
            
            # Подготавливаем промпт для классификации
            prompt = self._prepare_classification_prompt(content)
            
            # Классифицируем документ
            classification_result = self._classify_with_llm(prompt, self.classification_model, self.classification_tokenizer)
            
            return {
                'classification_available': True,
                'document_type': classification_result.get('document_type', 'unknown'),
                'confidence': classification_result.get('confidence', 0.0),
                'subtype': classification_result.get('subtype', ''),
                'model': self.config.classification_model,
                'context_length': len(prompt)
            }
            
        except Exception as e:
            self.logger.error(f"Stage 4 classification failed: {e}")
            return {'classification_available': False, 'error': str(e)}
    
    def stage_8_extract_metadata(self, content: str, structural_data: Dict) -> Dict:
        """
        Stage 8: Извлечение метаданных с RuT5
        Использует QA/IE подход для точного извлечения
        """
        try:
            if self.extraction_model is None:
                return {'extraction_available': False, 'error': 'Model not loaded'}
            
            # Извлекаем метаданные с помощью QA
            metadata = self._extract_metadata_with_qa(content, structural_data)
            
            return {
                'extraction_available': True,
                'metadata': metadata,
                'model': self.config.extraction_model,
                'fields_extracted': len(metadata)
            }
            
        except Exception as e:
            self.logger.error(f"Stage 8 extraction failed: {e}")
            return {'extraction_available': False, 'error': str(e)}
    
    def stage_5_5_deep_analysis(self, content: str, vlm_metadata: Dict) -> Dict:
        """
        Stage 5.5: Глубокий анализ с RuGPT
        Объединяет VLM + LLM для максимального понимания
        """
        try:
            if self.analysis_model is None:
                return {'analysis_available': False, 'error': 'Model not loaded'}
            
            # Глубокий анализ документа
            analysis_result = self._deep_analysis_with_llm(content, vlm_metadata)
            
            return {
                'analysis_available': True,
                'analysis': analysis_result,
                'model': self.config.analysis_model,
                'enhanced_sections': len(analysis_result.get('sections', [])),
                'extracted_entities': len(analysis_result.get('entities', []))
            }
            
        except Exception as e:
            self.logger.error(f"Stage 5.5 analysis failed: {e}")
            return {'analysis_available': False, 'error': str(e)}
    
    def _prepare_classification_prompt(self, content: str) -> str:
        """Подготовка промпта для классификации документа"""
        # Ограничиваем длину для классификации
        max_length = self.config.classification_max_length - 500
        truncated_content = content[:max_length] if len(content) > max_length else content
        
        prompt = f"""Определи тип строительного документа по его содержанию.

ДОКУМЕНТ:
{truncated_content}

ТИПЫ ДОКУМЕНТОВ:
- СНиП (Строительные нормы и правила)
- СП (Своды правил) 
- ГОСТ (Государственный стандарт)
- ППР (Проект производства работ)
- Смета (Локальная смета)
- Технический регламент
- Приказ/Постановление
- Проектная документация
- Другое

ФОРМАТ ОТВЕТА (JSON):
{{
    "document_type": "основной тип",
    "subtype": "подтип или номер",
    "confidence": 0.95,
    "keywords": ["ключевые слова"]
}}

Отвечай только JSON."""
        
        return prompt
    
    def _classify_with_llm(self, prompt: str, model, tokenizer) -> Dict:
        """Классификация с помощью LLM"""
        try:
            # Генерируем ответ
            inputs = tokenizer(prompt, return_tensors="pt", max_length=self.config.classification_max_length, truncation=True)
            
            # ✅ ПРИНУДИТЕЛЬНО ПЕРЕНОСИМ ВСЕ НА CPU (RuT5 должен быть на CPU!)
            inputs = {k: v.to("cpu") for k, v in inputs.items()}
            model = model.to("cpu")  # Принудительно переносим модель на CPU
            
            # ✅ Логируем устройство для отладки
            self.logger.info(f"🔧 RuT5 device: {next(model.parameters()).device}, inputs device: {inputs['input_ids'].device}")
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_length=min(len(inputs['input_ids'][0]) + 200, self.config.classification_max_length),
                    temperature=self.config.temperature,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            # Декодируем ответ
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_text = response[len(prompt):].strip()
            
            # Парсим JSON
            json_start = generated_text.find('{')
            json_end = generated_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = generated_text[json_start:json_end]
                return json.loads(json_text)
            else:
                return {"document_type": "unknown", "confidence": 0.0}
                
        except Exception as e:
            self.logger.error(f"Classification error: {e}")
            return {"document_type": "unknown", "confidence": 0.0}
    
    def _extract_metadata_with_qa(self, content: str, structural_data: Dict) -> Dict:
        """Извлечение метаданных с помощью QA подхода"""
        metadata = {}
        
        # Список полей для извлечения
        qa_questions = [
            ("Дата утверждения документа", "date_approval"),
            ("Номер документа", "document_number"),
            ("Название организации", "organization"),
            ("Дата введения в действие", "date_effective"),
            ("Область применения", "scope"),
            ("Ключевые слова", "keywords")
        ]
        
        for question, field in qa_questions:
            try:
                # Создаем QA промпт
                qa_prompt = f"""Найди в документе ответ на вопрос: {question}

ДОКУМЕНТ:
{content[:2000]}

Ответ (только факт, без дополнительного текста):"""
                
                # Генерируем ответ
                inputs = self.extraction_tokenizer(qa_prompt, return_tensors="pt", max_length=self.config.extraction_max_length, truncation=True)
                # Перемещаем на устройство (только если не квантизированная модель)
                if not hasattr(self.extraction_model, 'hf_quantizer'):
                    inputs = {k: v.to(self.extraction_model.device) for k, v in inputs.items()}
                else:
                    inputs = {k: v for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = self.extraction_model.generate(
                        **inputs,
                        max_length=min(len(inputs['input_ids'][0]) + 100, self.config.extraction_max_length),
                        temperature=0.1,
                        do_sample=True,
                        pad_token_id=self.extraction_tokenizer.eos_token_id
                    )
                
                response = self.extraction_tokenizer.decode(outputs[0], skip_special_tokens=True)
                answer = response[len(qa_prompt):].strip()
                
                if answer and len(answer) < 200:  # Разумная длина ответа
                    metadata[field] = answer
                    
            except Exception as e:
                self.logger.warning(f"Failed to extract {field}: {e}")
                continue
        
        return metadata
    
    def _deep_analysis_with_llm(self, content: str, vlm_metadata: Dict) -> Dict:
        """Глубокий анализ с помощью LLM"""
        try:
            # Подготавливаем промпт для анализа
            prompt = self._prepare_analysis_prompt(content, vlm_metadata)
            
            # Анализируем с LLM
            inputs = self.analysis_tokenizer(prompt, return_tensors="pt", max_length=self.config.analysis_max_length, truncation=True)
            # Перемещаем на устройство (только если не квантизированная модель)
            if not hasattr(self.analysis_model, 'hf_quantizer'):
                inputs = {k: v.to(self.analysis_model.device) for k, v in inputs.items()}
            else:
                inputs = {k: v for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.analysis_model.generate(
                    **inputs,
                    max_length=min(len(inputs['input_ids'][0]) + 500, self.config.analysis_max_length),
                    temperature=self.config.temperature,
                    do_sample=True,
                    pad_token_id=self.analysis_tokenizer.eos_token_id
                )
            
            response = self.analysis_tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_text = response[len(prompt):].strip()
            
            # Парсим JSON
            json_start = generated_text.find('{')
            json_end = generated_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = generated_text[json_start:json_end]
                return json.loads(json_text)
            else:
                return {"sections": [], "entities": [], "relations": []}
                
        except Exception as e:
            self.logger.error(f"Deep analysis error: {e}")
            return {"sections": [], "entities": [], "relations": []}
    
    def _prepare_analysis_prompt(self, content: str, vlm_metadata: Dict) -> str:
        """Подготовка промпта для глубокого анализа"""
        prompt = f"""Проведи глубокий анализ строительного документа.

ДОКУМЕНТ:
{content[:3000]}

VLM АНАЛИЗ:
- Таблицы: {len(vlm_metadata.get('tables', []))}
- Секции: {len(vlm_metadata.get('sections', []))}

ЗАДАЧИ:
1. Извлеки все секции и подразделы
2. Найди именованные сущности (даты, номера, организации)
3. Определи семантические связи между элементами

ФОРМАТ ОТВЕТА (JSON):
{{
    "sections": [
        {{"title": "название", "content": "содержимое", "level": 1}}
    ],
    "entities": [
        {{"text": "сущность", "type": "тип", "confidence": 0.9}}
    ],
    "relations": [
        {{"source": "источник", "target": "цель", "type": "связь"}}
    ]
}}

Отвечай только JSON."""
        
        return prompt
    
    def get_ensemble_info(self) -> Dict:
        """Получение информации об ансамбле"""
        return {
            'classification_model': self.config.classification_model,
            'extraction_model': self.config.extraction_model,
            'analysis_model': self.config.analysis_model,
            'classification_loaded': self.classification_model is not None,
            'extraction_loaded': self.extraction_model is not None,
            'analysis_loaded': self.analysis_model is not None,
            'device': str(self.classification_model.device) if self.classification_model is not None else 'unknown'
        }

# Пример использования
if __name__ == "__main__":
    # Конфигурация ансамбля
    config = RussianLLMEnsembleConfig(
        classification_model="ai-forever/rugpt3large_based_on_gpt2",
        extraction_model="ai-forever/rugpt3large_based_on_gpt2", 
        analysis_model="ai-forever/rugpt3large_based_on_gpt2",
        device="auto",
        use_quantization=True
    )
    
    # Создание ансамбля
    ensemble = RussianLLMEnsemble(config)
    
    # Тестовый анализ
    test_content = "СНиП 2.01.07-85* Нагрузки и воздействия. Утвержден 29.12.2020."
    
    # Stage 4: Классификация
    classification = ensemble.stage_4_classify_document(test_content)
    print(f"Классификация: {classification}")
    
    # Stage 8: Извлечение метаданных
    metadata = ensemble.stage_8_extract_metadata(test_content, {})
    print(f"Метаданные: {metadata}")
    
    # Stage 5.5: Глубокий анализ
    analysis = ensemble.stage_5_5_deep_analysis(test_content, {})
    print(f"Анализ: {analysis}")
    
    print(f"Информация об ансамбле: {ensemble.get_ensemble_info()}")
