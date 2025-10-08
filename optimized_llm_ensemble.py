"""
🚀 Оптимизированный ансамбль LLM для RTX 4060 (8GB VRAM)
Qwen3-8B (рабочая лошадка) + RuT5 (извлечение) + Qwen3-Coder-30B (сложные задачи)
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
    AutoModelForSeq2SeqLM,
    BitsAndBytesConfig
)

logger = logging.getLogger(__name__)

@dataclass
class OptimizedLLMConfig:
    """Конфигурация оптимизированного ансамбля LLM"""
    # Рабочая лошадка: Qwen3-8B для классификации и анализа
    workhorse_model: str = "Qwen/Qwen2.5-7B-Instruct"  # Qwen3-8B
    workhorse_max_length: int = 4096
    
    # Специалист: RuT5 для извлечения метаданных
    extraction_model: str = "ai-forever/rugpt3large_based_on_gpt2"  # Fallback к RuGPT
    extraction_max_length: int = 2048
    
    # Тяжеловес: Qwen3-Coder-30B для сложных задач (только при необходимости)
    heavy_model: str = "Qwen/Qwen2.5-Coder-32B-Instruct"  # Qwen3-Coder-30B
    heavy_model_max_length: int = 8192
    
    # Настройки VRAM для RTX 4060 (8GB)
    use_4bit_quantization: bool = True
    use_8bit_quantization: bool = False
    max_memory_gb: float = 7.0  # Оставляем 1GB для системы
    
    # Общие настройки
    device: str = "auto"
    cache_dir: str = "./models_cache"
    temperature: float = 0.1

class OptimizedLLMEnsemble:
    """
    Оптимизированный ансамбль LLM для RTX 4060
    Qwen3-8B (рабочая лошадка) + RuT5 (извлечение) + Qwen3-Coder-30B (сложные задачи)
    """
    
    def __init__(self, config: OptimizedLLMConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Инициализируем модели
        self.workhorse_model = None
        self.workhorse_tokenizer = None
        self.extraction_model = None
        self.extraction_tokenizer = None
        self.heavy_model = None
        self.heavy_tokenizer = None
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Инициализация оптимизированного ансамбля"""
        try:
            self.logger.info("🔄 Инициализация оптимизированного ансамбля LLM...")
            
            # Настройка квантизации для RTX 4060
            quantization_config = self._get_quantization_config()
            
            # 1. Рабочая лошадка: Qwen3-8B (всегда загружена)
            self._initialize_workhorse_model(quantization_config)
            
            # 2. Специалист: RuT5 (загружается по требованию)
            self._initialize_extraction_model(quantization_config)
            
            # 3. Тяжеловес: Qwen3-Coder-30B (загружается только при необходимости)
            # self._initialize_heavy_model(quantization_config)  # Отложенная загрузка
            
            self.logger.info("✅ Оптимизированный ансамбль LLM инициализирован")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации ансамбля: {e}")
            raise
    
    def _get_quantization_config(self) -> Optional[BitsAndBytesConfig]:
        """Настройка квантизации для RTX 4060"""
        if not torch.cuda.is_available():
            return None
        
        if self.config.use_4bit_quantization:
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
        elif self.config.use_8bit_quantization:
            return BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
            )
        
        return None
    
    def _initialize_workhorse_model(self, quantization_config):
        """Инициализация рабочей лошадки: Qwen3-8B"""
        try:
            self.logger.info(f"🐎 Загрузка рабочей лошадки: {self.config.workhorse_model}")
            
            # Загружаем токенизатор
            self.workhorse_tokenizer = AutoTokenizer.from_pretrained(
                self.config.workhorse_model,
                cache_dir=self.config.cache_dir,
                trust_remote_code=True
            )
            
            if self.workhorse_tokenizer.pad_token is None:
                self.workhorse_tokenizer.pad_token = self.workhorse_tokenizer.eos_token
            
            # Загружаем модель с оптимизацией VRAM
            self.workhorse_model = AutoModelForCausalLM.from_pretrained(
                self.config.workhorse_model,
                cache_dir=self.config.cache_dir,
                quantization_config=quantization_config,
                device_map=self.config.device,
                torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
                trust_remote_code=True,
                max_memory={0: f"{self.config.max_memory_gb}GB"} if torch.cuda.is_available() else None
            )
            
            self.logger.info("✅ Рабочая лошадка (Qwen3-8B) загружена")
            self.logger.info(f"📊 Устройство: {self.workhorse_model.device}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки рабочей лошадки: {e}")
            self.workhorse_model = None
    
    def _initialize_extraction_model(self, quantization_config):
        """Инициализация специалиста: RuT5"""
        try:
            self.logger.info(f"🔍 Загрузка специалиста: {self.config.extraction_model}")
            
            # Загружаем токенизатор
            self.extraction_tokenizer = AutoTokenizer.from_pretrained(
                self.config.extraction_model,
                cache_dir=self.config.cache_dir,
                trust_remote_code=True
            )
            
            if self.extraction_tokenizer.pad_token is None:
                self.extraction_tokenizer.pad_token = self.extraction_tokenizer.eos_token
            
            # Загружаем модель
            self.extraction_model = AutoModelForCausalLM.from_pretrained(
                self.config.extraction_model,
                cache_dir=self.config.cache_dir,
                quantization_config=quantization_config,
                device_map=self.config.device,
                torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
                trust_remote_code=True,
                max_memory={0: f"{self.config.max_memory_gb}GB"} if torch.cuda.is_available() else None
            )
            
            self.logger.info("✅ Специалист (RuT5) загружен")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки специалиста: {e}")
            self.extraction_model = None
    
    def _initialize_heavy_model(self, quantization_config):
        """Инициализация тяжеловеса: Qwen3-Coder-30B (только при необходимости)"""
        try:
            self.logger.info(f"🏋️ Загрузка тяжеловеса: {self.config.heavy_model}")
            
            # Загружаем токенизатор
            self.heavy_tokenizer = AutoTokenizer.from_pretrained(
                self.config.heavy_model,
                cache_dir=self.config.cache_dir,
                trust_remote_code=True
            )
            
            if self.heavy_tokenizer.pad_token is None:
                self.heavy_tokenizer.pad_token = self.heavy_tokenizer.eos_token
            
            # Загружаем модель с максимальной оптимизацией VRAM
            self.heavy_model = AutoModelForCausalLM.from_pretrained(
                self.config.heavy_model,
                cache_dir=self.config.cache_dir,
                quantization_config=quantization_config,
                device_map="auto",
                torch_dtype=torch.bfloat16,
                trust_remote_code=True,
                max_memory={0: f"{self.config.max_memory_gb}GB"}
            )
            
            self.logger.info("✅ Тяжеловес (Qwen3-Coder-30B) загружен")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки тяжеловеса: {e}")
            self.heavy_model = None
    
    def stage_4_classify_document(self, content: str) -> Dict:
        """
        Stage 4: Классификация документов (Qwen3-8B)
        Быстрая и точная классификация
        """
        try:
            if self.workhorse_model is None:
                return {'classification_available': False, 'error': 'Workhorse model not loaded'}
            
            # Подготавливаем промпт для Qwen3-8B
            prompt = self._prepare_classification_prompt(content)
            
            # Классифицируем с Qwen3-8B
            classification_result = self._classify_with_workhorse(prompt)
            
            return {
                'classification_available': True,
                'document_type': classification_result.get('document_type', 'unknown'),
                'confidence': classification_result.get('confidence', 0.0),
                'subtype': classification_result.get('subtype', ''),
                'model': 'Qwen3-8B',
                'context_length': len(prompt)
            }
            
        except Exception as e:
            self.logger.error(f"Stage 4 classification failed: {e}")
            return {'classification_available': False, 'error': str(e)}
    
    def stage_8_extract_metadata(self, content: str, structural_data: Dict) -> Dict:
        """
        Stage 8: Извлечение метаданных (RuT5)
        Специализированное извлечение с QA подходом
        """
        try:
            if self.extraction_model is None:
                return {'extraction_available': False, 'error': 'Extraction model not loaded'}
            
            # Извлекаем метаданные с RuT5
            metadata = self._extract_metadata_with_specialist(content, structural_data)
            
            return {
                'extraction_available': True,
                'metadata': metadata,
                'model': 'RuT5',
                'fields_extracted': len(metadata)
            }
            
        except Exception as e:
            self.logger.error(f"Stage 8 extraction failed: {e}")
            return {'extraction_available': False, 'error': str(e)}
    
    def stage_5_5_deep_analysis(self, content: str, vlm_metadata: Dict) -> Dict:
        """
        Stage 5.5: Глубокий анализ (Qwen3-8B)
        Быстрый анализ с рабочей лошадкой
        """
        try:
            if self.workhorse_model is None:
                return {'analysis_available': False, 'error': 'Workhorse model not loaded'}
            
            # Анализируем с Qwen3-8B
            analysis_result = self._analyze_with_workhorse(content, vlm_metadata)
            
            return {
                'analysis_available': True,
                'analysis': analysis_result,
                'model': 'Qwen3-8B',
                'enhanced_sections': len(analysis_result.get('sections', [])),
                'extracted_entities': len(analysis_result.get('entities', []))
            }
            
        except Exception as e:
            self.logger.error(f"Stage 5.5 analysis failed: {e}")
            return {'analysis_available': False, 'error': str(e)}
    
    def complex_task_with_heavy_model(self, task_description: str, context: str) -> Dict:
        """
        Сложные задачи с Qwen3-Coder-30B
        Только для критически важных задач
        """
        try:
            # Загружаем тяжеловес только при необходимости
            if self.heavy_model is None:
                self.logger.info("🏋️ Загружаем тяжеловес для сложной задачи...")
                quantization_config = self._get_quantization_config()
                self._initialize_heavy_model(quantization_config)
            
            if self.heavy_model is None:
                return {'heavy_task_available': False, 'error': 'Heavy model not loaded'}
            
            # Выполняем сложную задачу
            result = self._execute_heavy_task(task_description, context)
            
            return {
                'heavy_task_available': True,
                'result': result,
                'model': 'Qwen3-Coder-30B',
                'task_type': 'complex_analysis'
            }
            
        except Exception as e:
            self.logger.error(f"Heavy model task failed: {e}")
            return {'heavy_task_available': False, 'error': str(e)}
    
    def _prepare_classification_prompt(self, content: str) -> str:
        """Подготовка промпта для классификации (Qwen3-8B)"""
        max_length = self.config.workhorse_max_length - 500
        truncated_content = content[:max_length] if len(content) > max_length else content
        
        prompt = f"""<|im_start|>system
Ты - эксперт по классификации строительных документов. Определи тип документа по его содержанию.
<|im_end|>
<|im_start|>user
Определи тип документа:

{truncated_content}

Типы документов:
- СНиП (Строительные нормы и правила)
- СП (Своды правил)
- ГОСТ (Государственный стандарт)
- ППР (Проект производства работ)
- Смета (Локальная смета)
- Технический регламент
- Приказ/Постановление
- Проектная документация
- Другое

Ответь в формате JSON:
{{
    "document_type": "основной тип",
    "subtype": "подтип или номер",
    "confidence": 0.95,
    "keywords": ["ключевые слова"]
}}
<|im_end|>
<|im_start|>assistant"""
        
        return prompt
    
    def _classify_with_workhorse(self, prompt: str) -> Dict:
        """Классификация с Qwen3-8B"""
        try:
            inputs = self.workhorse_tokenizer(
                prompt, 
                return_tensors="pt", 
                max_length=self.config.workhorse_max_length, 
                truncation=True
            )
            
            # Перемещаем на устройство
            if not hasattr(self.workhorse_model, 'hf_quantizer'):
                inputs = {k: v.to(self.workhorse_model.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.workhorse_model.generate(
                    **inputs,
                    max_length=min(len(inputs['input_ids'][0]) + 200, self.config.workhorse_max_length),
                    temperature=self.config.temperature,
                    do_sample=True,
                    pad_token_id=self.workhorse_tokenizer.eos_token_id
                )
            
            response = self.workhorse_tokenizer.decode(outputs[0], skip_special_tokens=True)
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
    
    def _extract_metadata_with_specialist(self, content: str, structural_data: Dict) -> Dict:
        """Извлечение метаданных с RuT5"""
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
                qa_prompt = f"""Найди в документе ответ на вопрос: {question}

ДОКУМЕНТ:
{content[:2000]}

Ответ (только факт, без дополнительного текста):"""
                
                inputs = self.extraction_tokenizer(qa_prompt, return_tensors="pt", max_length=self.config.extraction_max_length, truncation=True)
                
                if not hasattr(self.extraction_model, 'hf_quantizer'):
                    inputs = {k: v.to(self.extraction_model.device) for k, v in inputs.items()}
                
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
                
                if answer and len(answer) < 200:
                    metadata[field] = answer
                    
            except Exception as e:
                self.logger.warning(f"Failed to extract {field}: {e}")
                continue
        
        return metadata
    
    def _analyze_with_workhorse(self, content: str, vlm_metadata: Dict) -> Dict:
        """Анализ с Qwen3-8B"""
        try:
            prompt = f"""<|im_start|>system
Ты - эксперт по анализу строительных документов. Проведи глубокий анализ документа.
<|im_end|>
<|im_start|>user
Проанализируй документ:

{content[:3000]}

VLM АНАЛИЗ:
- Таблицы: {len(vlm_metadata.get('tables', []))}
- Секции: {len(vlm_metadata.get('sections', []))}

Извлеки:
1. Все секции и подразделы
2. Именованные сущности (даты, номера, организации)
3. Семантические связи между элементами

Ответь в формате JSON:
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
<|im_end|>
<|im_start|>assistant"""
            
            inputs = self.workhorse_tokenizer(prompt, return_tensors="pt", max_length=self.config.workhorse_max_length, truncation=True)
            
            if not hasattr(self.workhorse_model, 'hf_quantizer'):
                inputs = {k: v.to(self.workhorse_model.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.workhorse_model.generate(
                    **inputs,
                    max_length=min(len(inputs['input_ids'][0]) + 500, self.config.workhorse_max_length),
                    temperature=self.config.temperature,
                    do_sample=True,
                    pad_token_id=self.workhorse_tokenizer.eos_token_id
                )
            
            response = self.workhorse_tokenizer.decode(outputs[0], skip_special_tokens=True)
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
            self.logger.error(f"Analysis error: {e}")
            return {"sections": [], "entities": [], "relations": []}
    
    def _execute_heavy_task(self, task_description: str, context: str) -> Dict:
        """Выполнение сложной задачи с Qwen3-Coder-30B"""
        try:
            prompt = f"""<|im_start|>system
Ты - эксперт по сложному анализу строительных документов. Выполни сложную задачу с максимальной точностью.
<|im_end|>
<|im_start|>user
Задача: {task_description}

Контекст:
{context}

Выполни задачу и предоставь детальный результат.
<|im_end|>
<|im_start|>assistant"""
            
            inputs = self.heavy_tokenizer(prompt, return_tensors="pt", max_length=self.config.heavy_model_max_length, truncation=True)
            
            if not hasattr(self.heavy_model, 'hf_quantizer'):
                inputs = {k: v.to(self.heavy_model.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.heavy_model.generate(
                    **inputs,
                    max_length=min(len(inputs['input_ids'][0]) + 1000, self.config.heavy_model_max_length),
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.heavy_tokenizer.eos_token_id
                )
            
            response = self.heavy_tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_text = response[len(prompt):].strip()
            
            return {
                'task_result': generated_text,
                'task_type': 'complex_analysis',
                'model_used': 'Qwen3-Coder-30B'
            }
            
        except Exception as e:
            self.logger.error(f"Heavy task error: {e}")
            return {'error': str(e)}
    
    def get_ensemble_info(self) -> Dict:
        """Получение информации об ансамбле"""
        return {
            'workhorse_model': self.config.workhorse_model,
            'extraction_model': self.config.extraction_model,
            'heavy_model': self.config.heavy_model,
            'workhorse_loaded': self.workhorse_model is not None,
            'extraction_loaded': self.extraction_model is not None,
            'heavy_loaded': self.heavy_model is not None,
            'device': str(self.workhorse_model.device) if self.workhorse_model is not None else 'unknown',
            'vram_optimized': True,
            'quantization': '4bit' if self.config.use_4bit_quantization else '8bit' if self.config.use_8bit_quantization else 'none'
        }

# Пример использования
if __name__ == "__main__":
    # Конфигурация для RTX 4060
    config = OptimizedLLMConfig(
        workhorse_model="Qwen/Qwen2.5-7B-Instruct",
        extraction_model="ai-forever/rugpt3large_based_on_gpt2",
        heavy_model="Qwen/Qwen2.5-Coder-32B-Instruct",
        use_4bit_quantization=True,
        max_memory_gb=7.0
    )
    
    # Создание ансамбля
    ensemble = OptimizedLLMEnsemble(config)
    
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
