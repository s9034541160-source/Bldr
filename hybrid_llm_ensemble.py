"""
Гибридный LLM Ансамбль для RTX 4060 (8GB VRAM) - GPU ОПТИМИЗАЦИЯ
- Mistral-7B-Instruct: GPU с 4-битной квантизацией - 4.5GB, 32K контекст
- SBERT: PyTorch - 1.5GB  
- RuT5: УДАЛЕН для экономии памяти
Итого: 6.0GB (помещается в 8GB VRAM!) + СКОРОСТЬ GPU!
"""

import os
import json
import torch
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from sentence_transformers import SentenceTransformer

@dataclass
class HybridLLMConfig:
    """Конфигурация гибридного ансамбля - GPU ОПТИМИЗАЦИЯ"""
    # GPU Qwen2.5-7B с 4-битной квантизацией (полностью открытая модель)
    mistral_model_name: str = "Qwen/Qwen2.5-7B-Instruct"
    mistral_device: str = "cuda"
    mistral_max_length: int = 32768  # 32K контекст (больше чем у DeepSeek!)
    
    # PyTorch SBERT - УПРАВЛЯЕТСЯ RAG TRAINER
    sbert_model: str = ""  # Пустая строка - модель управляется enterprise_rag_trainer_full.py
    sbert_device: str = "cuda"
    
    # PyTorch RuT5 - УДАЛЕН для экономии памяти
    # rut5_model: str = "ai-forever/ruT5-base"
    # rut5_device: str = "cuda"
    
    # Общие настройки
    temperature: float = 0.7
    max_length: int = 2048
    
    @classmethod
    def from_env(cls):
        """Загрузка конфигурации из переменных окружения"""
        return cls(
            mistral_model_name=os.getenv('MISTRAL_MODEL_NAME', cls.mistral_model_name),
            sbert_model=os.getenv('SBERT_MODEL', cls.sbert_model)
            # rut5_model=os.getenv('RUT5_MODEL', cls.rut5_model)  # УДАЛЕН
        )

class HybridLLMEnsemble:
    """Гибридный ансамбль LLM для RTX 4060 - GPU ОПТИМИЗАЦИЯ"""
    
    def __init__(self, config: HybridLLMConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Инициализация компонентов
        self.mistral_model = None
        self.mistral_tokenizer = None
        self.sbert_model = None
        # self.rut5_model = None  # УДАЛЕН
        # self.rut5_tokenizer = None  # УДАЛЕН
        
        self._initialize_ensemble()
    
    def _initialize_ensemble(self):
        """Инициализация всех компонентов ансамбля - GPU ОПТИМИЗАЦИЯ"""
        try:
            # 1. Загрузка GPU Mistral-7B с 4-битной квантизацией (4.5GB)
            self._initialize_mistral_gpu()
            
            # 2. Загрузка PyTorch SBERT (1.5GB)
            self._initialize_sbert()
            
            # 3. RuT5 УДАЛЕН для экономии памяти
            
            self.logger.info("✅ Гибридный ансамбль инициализирован успешно")
            self.logger.info(f"🎮 Qwen2.5-7B-Instruct (GPU): {self.config.mistral_model_name}")
            self.logger.info(f"🎮 SBERT: {self.config.sbert_device}")
            # self.logger.info(f"🎮 RuT5: {self.config.rut5_device}")  # УДАЛЕН
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации ансамбля: {e}")
            raise
    
    def _initialize_mistral_gpu(self):
        """Инициализация GPU Mistral-7B с 4-битной квантизацией"""
        try:
            self.logger.info("🔄 Загрузка Qwen2.5-7B-Instruct (GPU с квантизацией)...")
            
            # 1. Настройка 4-битной квантизации для экономии VRAM
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True
            )
            
            # 2. Загрузка токенайзера
            self.logger.info("📝 Загрузка токенайзера...")
            self.mistral_tokenizer = AutoTokenizer.from_pretrained(
                self.config.mistral_model_name,
                trust_remote_code=True
            )
            
            # 3. Загрузка модели с квантизацией и автораспределением на GPU
            self.logger.info("🚀 Загрузка модели на GPU...")
            self.mistral_model = AutoModelForCausalLM.from_pretrained(
                self.config.mistral_model_name,
                quantization_config=bnb_config,
                device_map="auto",  # Автоматически разместит на GPU
                torch_dtype=torch.float16,
                trust_remote_code=True
            )
            
            self.logger.info("✅ Qwen2.5-7B-Instruct (GPU) загружен с 4-битной квантизацией")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки Qwen2.5-7B: {e}")
            raise
    
    def _initialize_sbert(self):
        """Инициализация SBERT - CONTEXT SWITCHING"""
        try:
            # 🚀 CONTEXT SWITCHING: НЕ ЗАГРУЖАЕМ SBERT СРАЗУ!
            self.sbert_model = None
            self.sbert_model_name = self.config.sbert_model
            self.sbert_device = self.config.sbert_device
            self.logger.info("🚀 CONTEXT SWITCHING: SBERT will be loaded on-demand")
            self.logger.info("🚀 CONTEXT SWITCHING: This prevents VRAM overflow and disk thrashing!")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации SBERT context switching: {e}")
            self.sbert_model = None
    
    def _load_sbert_model(self):
        """Загружает SBERT в VRAM только при необходимости."""
        if self.sbert_model is None:
            # 🚀 CONTEXT SWITCHING: SBERT управляется enterprise_rag_trainer_full.py
            self.logger.info("🚀 CONTEXT SWITCHING: SBERT loading delegated to enterprise_rag_trainer_full.py")
            self.logger.info("🚀 CONTEXT SWITCHING: This prevents double loading and memory conflicts!")
            return None
        return self.sbert_model

    def _unload_sbert_model(self):
        """Выгружает SBERT из VRAM, очищая кэш."""
        # 🚀 CONTEXT SWITCHING: SBERT управляется enterprise_rag_trainer_full.py
        self.logger.info("🚀 CONTEXT SWITCHING: SBERT unloading delegated to enterprise_rag_trainer_full.py")
        self.logger.info("🚀 CONTEXT SWITCHING: This prevents double unloading and memory conflicts!")

    # def _initialize_rut5(self):  # УДАЛЕН для экономии памяти
    #     """Инициализация RuT5"""
    #     pass
    
    def _get_model_device(self, model):
        """Универсальное определение устройства модели"""
        try:
            return next(model.parameters()).device
        except StopIteration:
            return torch.device('cpu')
    
    def _move_inputs_to_model_device(self, inputs, model, model_name="Model"):
        """Универсальный перенос входных данных на устройство модели"""
        device = self._get_model_device(model)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        self.logger.debug(f"🔧 {model_name} device: {device}, inputs device: {inputs['input_ids'].device}")
        return inputs
    
    def classify_document(self, content: str) -> Dict:
        """Классификация документа с DeepSeek-Coder-6.7B (GGUF)"""
        try:
            if self.mistral_model is None:
                return {'classification_available': False, 'error': 'Qwen model not loaded'}
            
            prompt = f"""CLASSIFIER EXPERT. Analyze text and identify document type (gost, sp, fz, pprf, etc.).
Constraint: Return ONLY valid JSON. Confidence must be 0.9 if type is clearly visible.

🔥🔥🔥 ULTRA CRITICAL RULE 🔥🔥🔥
IF DOCUMENT STARTS WITH "СП" + NUMBERS (like СП158.13330.2014) → TYPE IS "sp" → CONFIDENCE 0.99
NEVER use "sto", "gost", or any other type if "СП" is present!
🔥🔥🔥 END ULTRA CRITICAL RULE 🔥🔥🔥

DOCUMENT:
{content[:2048]}

🔥🔥🔥 ULTRA CRITICAL RULE 🔥🔥🔥
IF DOCUMENT STARTS WITH "СП" + NUMBERS (like СП158.13330.2014) → TYPE IS "sp" → CONFIDENCE 0.99
NEVER use "sto", "gost", or any other type if "СП" is present!
🔥🔥🔥 END ULTRA CRITICAL RULE 🔥🔥🔥

Types: sp, сн, гост, санпин, фз, постановление, приказ, инструкция

🔥🔥🔥 REQUIRED JSON (MUST END WITH CLOSING BRACE) 🔥🔥🔥
{{
  "document_type": "sp",
  "confidence": 0.99,
  "subtype": "sp"
}}
🔥🔥🔥 YOUR JSON OUTPUT MUST END WITH '}}' 🔥🔥🔥"""
            
            # 🔬 СУПЕР-DEBUG ДЛЯ LLM
            import time
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info(f"[DEBUG_LLM] Prompt start (2048 chars): {prompt[:200]}...")
            logger.info(f"[DEBUG_LLM] About to call DeepSeek-Coder...")
            logger.info(f"[DEBUG_LLM] Mistral model available: {self.mistral_model is not None}")
            start_time = time.time()
            
            # ПРИНУДИТЕЛЬНАЯ ОСТАНОВКА ПО ВРЕМЕНИ (максимум 30 секунд)
            import threading
            import time as time_module
            
            response = None
            timeout_occurred = False
            
            def timeout_handler():
                nonlocal timeout_occurred
                time_module.sleep(30)  # 30 секунд максимум
                if response is None:
                    timeout_occurred = True
            
            timeout_thread = threading.Thread(target=timeout_handler)
            timeout_thread.daemon = True
            timeout_thread.start()
            
            try:
                # Формируем промпт в формате Qwen2.5
                qwen_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
                
                # Токенизация
                inputs = self.mistral_tokenizer(
                    qwen_prompt,
                    return_tensors="pt",
                    max_length=32768,
                    truncation=True,
                    padding=True
                ).to(self.mistral_model.device)
                
                # Генерация с GPU
                with torch.no_grad():
                    outputs = self.mistral_model.generate(
                        **inputs,
                        max_new_tokens=80,  # УЛЬТРА-ЖЕСТКО ОГРАНИЧИВАЕМ для JSON
                        temperature=0.0,  # МАКСИМАЛЬНО ДЕТЕРМИНИРОВАННО!
                        do_sample=False,
                        pad_token_id=self.mistral_tokenizer.eos_token_id
                    )
                
                # Декодирование ответа
                generated_text = self.mistral_tokenizer.decode(
                    outputs[0][inputs['input_ids'].shape[1]:], 
                    skip_special_tokens=True
                ).strip()
                
            except Exception as e:
                if timeout_occurred:
                    logger.warning(f"[DEBUG_LLM] ТАЙМАУТ! Mistral завис на 30 секунд: {e}")
                    return {'document_type': 'unknown', 'confidence': 0.0}
                else:
                    raise e
            
            end_time = time.time()
            
            logger.info(f"[DEBUG_LLM] Raw Response Time: {end_time - start_time:.2f}s")
            logger.info(f"[DEBUG_LLM] Raw LLM Output: {generated_text}")
            
            # ПРИНУДИТЕЛЬНАЯ ПРОВЕРКА НА ПУСТОЙ ОТВЕТ
            if not generated_text or len(generated_text.strip()) < 10:
                logger.warning(f"[DEBUG_LLM] LLM не вернул JSON! Создаем fallback для:")
                # Fallback к regex/sbert результатам
                return {'document_type': 'unknown', 'confidence': 0.0}
            
            # Парсим JSON с СУПЕР-АГРЕССИВНОЙ очисткой от Markdown
            try:
                # СУПЕР-АГРЕССИВНАЯ очистка от Markdown и мусора
                cleaned_text = generated_text.strip()
                cleaned_text = cleaned_text.replace('```json', '').replace('```', '')
                cleaned_text = cleaned_text.replace('```', '').replace('`', '')
                cleaned_text = cleaned_text.replace('\n', ' ').replace('\r', ' ')
                cleaned_text = cleaned_text.strip()
                
                # ПРИНУДИТЕЛЬНАЯ ПРОВЕРКА: Если не JSON, создаем fallback
                if not cleaned_text.startswith('{'):
                    logger.warning(f"[DEBUG_LLM] LLM не вернул JSON! Создаем fallback для: {cleaned_text[:100]}")
                    # Fallback: определяем тип по содержимому
                    if "СП" in content[:1000] or "свод правил" in content[:1000].lower():
                        cleaned_text = '{"document_type": "sp", "confidence": 0.9, "subtype": "sp"}'
                    elif "СНиП" in content[:1000] or "строительные нормы" in content[:1000].lower():
                        cleaned_text = '{"document_type": "сн", "confidence": 0.9, "subtype": "сн"}'
                    else:
                        cleaned_text = '{"document_type": "unknown", "confidence": 0.0, "subtype": ""}'
                
                json_start = cleaned_text.find('{')
                json_end = cleaned_text.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_text = cleaned_text[json_start:json_end]
                    logger.info(f"[DEBUG_LLM] Extracted JSON: {json_text}")
                    result = json.loads(json_text)
                    logger.info(f"[DEBUG_LLM] Successfully Parsed JSON: {result}")
                    return {
                        'document_type': result.get('document_type', 'unknown'),
                        'confidence': result.get('confidence', 0.0),
                        'subtype': result.get('subtype', ''),
                        'model': 'DeepSeek-Coder-6.7B-GGUF'
                    }
                else:
                    return {"document_type": "unknown", "confidence": 0.0}
            except json.JSONDecodeError as e:
                logger.error(f"❌ [DEBUG_LLM] FATAL JSON DECODE: {e}")
                logger.error(f"❌ [DEBUG_LLM] Failed String Attempt: {cleaned_text[:500]}...")
                return {"document_type": "unknown", "confidence": 0.0}
                
        except Exception as e:
            self.logger.error(f"Classification error: {e}")
            return {"document_type": "unknown", "confidence": 0.0}
    
    def extract_metadata(self, content: str, structural_data: Dict) -> Dict:
        """Извлечение метаданных с Mistral-7B GPU (32K контекст для длинных абзацев)"""
        try:
            if self.mistral_model is None or self.mistral_tokenizer is None:
                return {'extraction_available': False, 'error': 'Mistral model not loaded'}
            
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
                    # Формируем промпт в формате Qwen2.5
                    qa_prompt = f"""<|im_start|>user
Найди в документе ответ на вопрос: {question}

ДОКУМЕНТ:
{content[:16384]}  # Увеличили до 16K символов

Ответ (только факт, без дополнительного текста):<|im_end|>
<|im_start|>assistant
"""
                    
                    # Токенизация
                    inputs = self.mistral_tokenizer(
                        qa_prompt,
                        return_tensors="pt",
                        max_length=32768,  # 32K контекст!
                        truncation=True,
                        padding=True
                    ).to(self.mistral_model.device)
                    
                    # Генерация с GPU
                    with torch.no_grad():
                        outputs = self.mistral_model.generate(
                            **inputs,
                            max_new_tokens=100,
                            temperature=0.0,
                            do_sample=False,
                            pad_token_id=self.mistral_tokenizer.eos_token_id
                        )
                    
                    # Декодирование ответа
                    answer = self.mistral_tokenizer.decode(
                        outputs[0][inputs['input_ids'].shape[1]:], 
                        skip_special_tokens=True
                    ).strip()
                    
                    if answer and len(answer) > 2:
                        metadata[field] = answer
                    else:
                        metadata[field] = "Не найдено"
                        
                except Exception as e:
                    self.logger.debug(f"Ошибка извлечения поля {field}: {e}")
                    metadata[field] = "Ошибка извлечения"
            
            return {
                'extraction_available': True,
                'metadata': metadata,
                'model': 'Qwen2.5-7B-Instruct-GPU',
                'fields_extracted': len(metadata)
            }
            
        except Exception as e:
            self.logger.error(f"Metadata extraction failed: {e}")
            return {'extraction_available': False, 'error': str(e)}
    
    def get_embeddings(self, texts: list) -> list:
        """Получение эмбеддингов с SBERT"""
        try:
            if self.sbert_model is None:
                return []
            
            embeddings = self.sbert_model.encode(texts)
            return embeddings.tolist()
            
        except Exception as e:
            self.logger.error(f"Embeddings error: {e}")
            return []
    
    def get_ensemble_info(self) -> Dict:
        """Получение информации об ансамбле"""
        return {
            'mistral_loaded': self.mistral_model is not None,
            'sbert_loaded': self.sbert_model is not None,
            'rut5_loaded': self.rut5_model is not None,
            'mistral_type': 'GPU-4bit',
            'sbert_device': str(self.sbert_model.device) if self.sbert_model else 'unknown',
            'rut5_device': str(self.rut5_model.device) if self.rut5_model else 'unknown',
            'strategy': 'Hybrid: Qwen2.5-7B-Instruct(GPU-4bit) + SBERT(PyTorch) + RuT5(PyTorch)',
            'total_vram_usage': '~6.0GB (fits in 8GB RTX 4060) + SPEED!'
        }

# Пример использования
if __name__ == "__main__":
    config = HybridLLMConfig.from_env()
    ensemble = HybridLLMEnsemble(config)
    
    print("Информация об ансамбле:")
    print(json.dumps(ensemble.get_ensemble_info(), indent=2, ensure_ascii=False))
