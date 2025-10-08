"""
🚀 Оптимизированный ансамбль LLM для RTX 4060
Qwen3-8B (рабочая лошадка) + RuT5 (специалист по извлечению)
Максимальная скорость и эффективность для RAG-тренера
"""

import logging
import torch
import json
import time
import os
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
class WorkhorseLLMConfig:
    """Конфигурация рабочего ансамбля LLM"""
    # Рабочая лошадка: Qwen3-8B для всех основных задач
    workhorse_model: str = "Qwen/Qwen3-8B"
    workhorse_max_length: int = 32768
    
    # Специалист: RuT5 для извлечения метаданных
    extraction_model: str = "ai-forever/ruT5-base"  # ✅ ПРАВИЛЬНЫЙ RuT5
    extraction_max_length: int = 2048
    
    # Настройки VRAM для RTX 4060 (8GB)
    use_4bit_quantization: bool = True
    use_8bit_quantization: bool = False
    max_memory_gb: float = 7.0  # Оставляем 1GB для системы
    
    # Общие настройки
    device: str = "auto"
    cache_dir: str = "./models_cache"
    temperature: float = 0.1
    
    @classmethod
    def from_env(cls):
        """Загрузка конфигурации из переменных окружения"""
        # Устанавливаем переменные окружения для Hugging Face
        os.environ.setdefault('HF_HOME', 'I:/huggingface_cache')
        os.environ.setdefault('TRANSFORMERS_CACHE', 'I:/huggingface_cache')
        os.environ.setdefault('HF_DATASETS_CACHE', 'I:/huggingface_cache')
        
        return cls(
            workhorse_model=os.getenv('LLM_WORKHORSE_MODEL', 'Qwen/Qwen3-8B'),
            workhorse_max_length=int(os.getenv('LLM_WORKHORSE_MAX_LENGTH', '32768')),
            extraction_model=os.getenv('LLM_EXTRACTION_MODEL', 'ai-forever/ruT5-base'),
            extraction_max_length=int(os.getenv('LLM_EXTRACTION_MAX_LENGTH', '2048')),
            use_4bit_quantization=os.getenv('LLM_4BIT_QUANTIZATION', 'true').lower() == 'true',
            use_8bit_quantization=os.getenv('LLM_8BIT_QUANTIZATION', 'false').lower() == 'true',
            max_memory_gb=float(os.getenv('LLM_MAX_MEMORY_GB', '7.0')),
            device=os.getenv('LLM_DEVICE', 'auto'),
            cache_dir=os.getenv('LLM_CACHE_DIR', 'I:/models_cache'),
            temperature=float(os.getenv('LLM_TEMPERATURE', '0.1'))
        )

class WorkhorseLLMEnsemble:
    """
    Оптимизированный ансамбль LLM для RTX 4060
    Qwen3-8B (рабочая лошадка) + RuT5 (специалист по извлечению)
    """
    
    def __init__(self, config: WorkhorseLLMConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Инициализируем только необходимые модели
        self.workhorse_model = None
        self.workhorse_tokenizer = None
        self.extraction_model = None
        self.extraction_tokenizer = None
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Инициализация рабочего ансамбля"""
        try:
            self.logger.info("🔄 Инициализация рабочего ансамбля LLM...")
            
            # 1. Рабочая лошадка: Qwen3-8B (всегда загружена)
            self._initialize_workhorse_model()
            
            # 2. Специалист: RuT5 (загружается по требованию)
            self._initialize_extraction_model()
            
            self.logger.info("✅ Рабочий ансамбль LLM инициализирован")
            
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
    
    def _initialize_workhorse_model(self):
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
            
            # 🚨 КРИТИЧЕСКАЯ ОПТИМИЗАЦИЯ VRAM для RTX 4060 (8GB)
            # Используем простой device_map="auto" для корректной работы
            device_map_config = "auto" if torch.cuda.is_available() else "cpu"
            
            # 🚨 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Правильная конфигурация квантизации для Qwen3-8B
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                # ⬅️ КРИТИЧЕСКИЙ ФЛАГ ТЕПЕРЬ ВНУТРИ КОНФИГА
                llm_int8_enable_fp32_cpu_offload=True,
                bnb_4bit_compute_dtype=torch.bfloat16  # Рекомендуется для Qwen
            )
            
            # 🚨 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Увеличиваем лимит VRAM до 97.5%
            MAX_QWEN_VRAM = 7800  # 7800 MiB (97.5% от 8192 MiB)
            
            # Загружаем модель с увеличенным лимитом VRAM
            self.workhorse_model = AutoModelForCausalLM.from_pretrained(
                self.config.workhorse_model,
                cache_dir=self.config.cache_dir,
                quantization_config=bnb_config,  # ✅ ПРАВИЛЬНАЯ КВАНТИЗАЦИЯ
                device_map="auto",  # ⬅️ ВОЗВРАЩАЕМ device_map для max_memory
                max_memory={0: f'{MAX_QWEN_VRAM}MiB', 'cpu': '50GiB'},  # ⬅️ ЯДЕРНАЯ ПРАВКА OOM
                torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
                trust_remote_code=True,
                low_cpu_mem_usage=True,  # Минимизируем использование CPU RAM
                offload_folder="./offload_cache"  # Папка для временного хранения
            )
            
            self.logger.info("✅ Рабочая лошадка (Qwen3-8B) загружена")
            self.logger.info(f"📊 Устройство: {self.workhorse_model.device}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки рабочей лошадки: {e}")
            self.workhorse_model = None
    
    def _initialize_extraction_model(self):
        """🔍 Загрузка специалиста: RuT5 (НЕ RuGPT!)"""
        try:
            self.logger.info(f"🔍 Загрузка специалиста: {self.config.extraction_model}")
            
            # Загружаем токенизатор RuT5 с принудительным slow tokenizer
            self.extraction_tokenizer = AutoTokenizer.from_pretrained(
                self.config.extraction_model,
                cache_dir=self.config.cache_dir,
                use_fast=False,  # ⬅️ КРИТИЧЕСКАЯ ПРАВКА ДЛЯ WINDOWS/RuT5
                trust_remote_code=True
            )
            
            if self.extraction_tokenizer.pad_token is None:
                self.extraction_tokenizer.pad_token = self.extraction_tokenizer.eos_token
            
            # ✅ ПРИНУДИТЕЛЬНО RuT5 на CPU с float32 (float16 не работает на CPU!)
            self.extraction_model = AutoModelForSeq2SeqLM.from_pretrained(
                self.config.extraction_model,
                cache_dir=self.config.cache_dir,
                trust_remote_code=True,
                torch_dtype=torch.float32  # ✅ float32 для CPU
            ).to("cpu")  # ✅ ПРИНУДИТЕЛЬНО НА CPU
            
            # ✅ ПРИНУДИТЕЛЬНАЯ ПРОВЕРКА: Убеждаемся, что RuT5 на CPU
            self.extraction_model = self.extraction_model.to("cpu")
            self.logger.info("✅ Специалист (RuT5) загружен")
            self.logger.info(f"🔧 RuT5 device: {next(self.extraction_model.parameters()).device}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки RuT5. Работа без специалиста: {e}")
            self.extraction_model = None
            self.extraction_tokenizer = None
    
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
    
    def stage_10_complex_logic(self, task_description: str, context: str) -> Dict:
        """
        Stage 10: Сложная логика (Qwen3-8B)
        Генерация Cypher запросов и сложная логика
        """
        try:
            if self.workhorse_model is None:
                return {'complex_logic_available': False, 'error': 'Workhorse model not loaded'}
            
            # Выполняем сложную задачу с Qwen3-8B
            result = self._execute_complex_logic_with_workhorse(task_description, context)
            
            return {
                'complex_logic_available': True,
                'result': result,
                'model': 'Qwen3-8B',
                'task_type': 'complex_logic'
            }
            
        except Exception as e:
            self.logger.error(f"Stage 10 complex logic failed: {e}")
            return {'complex_logic_available': False, 'error': str(e)}
    
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
    
    def _get_model_device(self, model):
        """Универсальное определение устройства модели"""
        try:
            return next(model.parameters()).device
        except StopIteration:
            # Если модель без параметров (редко), предполагаем CPU
            return torch.device('cpu')
    
    def _move_inputs_to_model_device(self, inputs, model, model_name="Model"):
        """Универсальный перенос входных данных на устройство модели"""
        device = self._get_model_device(model)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        self.logger.debug(f"🔧 {model_name} device: {device}, inputs device: {inputs['input_ids'].device}")
        return inputs

    def _classify_with_workhorse(self, prompt: str) -> Dict:
        """Классификация с Qwen3-8B"""
        try:
            inputs = self.workhorse_tokenizer(
                prompt, 
                return_tensors="pt", 
                max_length=self.config.workhorse_max_length, 
                truncation=True
            )
            
            # ✅ УНИВЕРСАЛЬНОЕ РЕШЕНИЕ: Автоматическое определение устройства
            inputs = self._move_inputs_to_model_device(inputs, self.workhorse_model, "Qwen3-8B")
            
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
                
                # ✅ УНИВЕРСАЛЬНОЕ РЕШЕНИЕ: Автоматическое определение устройства RuT5
                inputs = self._move_inputs_to_model_device(inputs, self.extraction_model, "RuT5")
                
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
    
    def _execute_complex_logic_with_workhorse(self, task_description: str, context: str) -> Dict:
        """Выполнение сложной логики с Qwen3-8B"""
        try:
            prompt = f"""<|im_start|>system
Ты - эксперт по сложной логике для строительных документов. Выполни сложную задачу с максимальной точностью.
<|im_end|>
<|im_start|>user
Задача: {task_description}

Контекст:
{context}

Выполни задачу и предоставь детальный результат.
<|im_end|>
<|im_start|>assistant"""
            
            inputs = self.workhorse_tokenizer(prompt, return_tensors="pt", max_length=self.config.workhorse_max_length, truncation=True)
            
            if not hasattr(self.workhorse_model, 'hf_quantizer'):
                inputs = {k: v.to(self.workhorse_model.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.workhorse_model.generate(
                    **inputs,
                    max_length=min(len(inputs['input_ids'][0]) + 1000, self.config.workhorse_max_length),
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.workhorse_tokenizer.eos_token_id
                )
            
            response = self.workhorse_tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_text = response[len(prompt):].strip()
            
            return {
                'task_result': generated_text,
                'task_type': 'complex_logic',
                'model_used': 'Qwen3-8B'
            }
            
        except Exception as e:
            self.logger.error(f"Complex logic error: {e}")
            return {'error': str(e)}
    
    def get_ensemble_info(self) -> Dict:
        """Получение информации об ансамбле"""
        return {
            'workhorse_model': self.config.workhorse_model,
            'extraction_model': self.config.extraction_model,
            'workhorse_loaded': self.workhorse_model is not None,
            'extraction_loaded': self.extraction_model is not None,
            'device': str(self.workhorse_model.device) if self.workhorse_model is not None else 'unknown',
            'extraction_device': str(self.extraction_model.device) if self.extraction_model is not None else 'unknown',
            'vram_optimized': True,
            'quantization': '4bit' if self.config.use_4bit_quantization else '8bit' if self.config.use_8bit_quantization else 'none',
            'strategy': 'Qwen3-8B (workhorse) + RuT5 (specialist)'
        }

# Пример использования
if __name__ == "__main__":
    # Конфигурация для RTX 4060
    config = WorkhorseLLMConfig(
        workhorse_model="Qwen/Qwen3-8B",
        extraction_model="ai-forever/ruT5-base",
        use_4bit_quantization=True,
        max_memory_gb=7.0
    )
    
    # Создание ансамбля
    ensemble = WorkhorseLLMEnsemble(config)
    
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
    
    # Stage 10: Сложная логика
    complex_logic = ensemble.stage_10_complex_logic(
        "Создай Cypher запрос для поиска всех документов, связанных с нагрузками",
        test_content
    )
    print(f"Сложная логика: {complex_logic}")
    
    print(f"Информация об ансамбле: {ensemble.get_ensemble_info()}")
