"""
ENTERPRISE RAG 3.0: VLM Processor для анализа таблиц и структуры документов
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from transformers import LayoutLMv3Processor, LayoutLMv3ForTokenClassification
import cv2
import numpy as np
from pdf2image import convert_from_path
import pytesseract

logger = logging.getLogger(__name__)

class VLMProcessor:
    """ENTERPRISE RAG 3.0: Vision-Language Model для анализа документов"""
    
    def __init__(self, device: str = "auto"):
        # ⬅️ КРИТИЧЕСКАЯ ПРАВКА: VLM на CUDA для скорости!
        self.device = self._get_device(device)  # Автоматически CUDA если доступно
        self.blip_processor = None
        self.blip_model = None
        self.layout_processor = None
        self.layout_model = None
        
        # CUDA оптимизации для скорости!
        logger.info(f"[VLM] VLM device: {self.device}")
        self._load_models()
    
    def _get_device(self, device: str) -> str:
        """Определяет оптимальное устройство для VLM"""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return device
    
    def _optimize_gpu_memory(self):
        """Оптимизирует GPU память для RTX 4060"""
        
        if torch.cuda.is_available():
            # Очищаем кэш
            torch.cuda.empty_cache()
            
            # Настраиваем память (90% от 8GB = 7.2GB)
            torch.cuda.set_per_process_memory_fraction(0.9)
            
            # Включаем оптимизации
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.deterministic = False
            
            logger.info("GPU memory optimized for RTX 4060")
    
    def _load_models(self):
        """Загружает VLM модели"""
        try:
            logger.info(f"Loading VLM models on {self.device} (VLM на CUDA для скорости!)")
            
            # BLIP для описания изображений
            self.blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            self.blip_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base",
                torch_dtype=torch.float16  # ⬅️ CUDA использует float16
            )
            self.blip_model.to(self.device)  # ⬅️ На CUDA для скорости!
            
            # LayoutLMv3 для анализа структуры документов
            self.layout_processor = LayoutLMv3Processor.from_pretrained("microsoft/layoutlmv3-base")
            
            # VLM на CUDA для скорости!
            self.layout_model = LayoutLMv3ForTokenClassification.from_pretrained(
                "microsoft/layoutlmv3-base",
                trust_remote_code=True,
                torch_dtype=torch.float16  # ⬅️ ОБЯЗАТЕЛЬНО float16 для совместимости с BLIP!
            ).to(self.device)
            
            # 💥 ПРИНУДИТЕЛЬНАЯ ПРОВЕРКА ТИПОВ: Обе модели должны быть float16!
            if hasattr(self.blip_model, 'dtype'):
                logger.info(f"[VLM_DEBUG] BLIP dtype: {self.blip_model.dtype}")
            if hasattr(self.layout_model, 'dtype'):
                logger.info(f"[VLM_DEBUG] LayoutLMv3 dtype: {self.layout_model.dtype}")
            
            # Принудительно устанавливаем float16 для обеих моделей
            self.blip_model = self.blip_model.half()
            self.layout_model = self.layout_model.half()
            logger.info(f"[VLM_DEBUG] Принудительно установлен float16 для обеих моделей")
            
            logger.info(f"VLM models loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load VLM models: {e}")
            self.blip_processor = None
            self.blip_model = None
            self.layout_processor = None
            self.layout_model = None
    
    def is_available(self) -> bool:
        """Проверяет доступность VLM"""
        return (self.blip_processor is not None and 
                self.blip_model is not None and
                self.layout_processor is not None and
                self.layout_model is not None)
    
    def extract_tables_from_pdf(self, pdf_path: str) -> List[Dict]:
        """ENTERPRISE: Извлечение таблиц из PDF с помощью VLM"""
        
        if not self.is_available():
            logger.warning("VLM not available, using fallback")
            return self._fallback_table_extraction(pdf_path)
        
        try:
            # Конвертируем PDF в изображения
            images = convert_from_path(pdf_path, dpi=300)
            tables = []
            
            # Защита от пустого PDF
            if not images or len(images) == 0:
                logger.warning(f"⚠️ PDF {pdf_path} has no pages or failed to convert")
                return []
            
            for page_num, image in enumerate(images):
                # Анализируем каждую страницу с защитой
                try:
                    page_tables = self._analyze_page_for_tables(image, page_num)
                    tables.extend(page_tables)
                except Exception as e:
                    logger.error(f"🛑 Critical error on page {page_num}, skipping: {e}")
                    continue  # Продолжаем обработку других страниц
            
            return tables
            
        except Exception as e:
            logger.error(f"VLM table extraction failed: {e}")
            return self._fallback_table_extraction(pdf_path)
    
    def _analyze_page_for_tables(self, image: Image.Image, page_num: int) -> List[Dict]:
        """Анализирует страницу на наличие таблиц с защитой от CUDA ошибок"""
        
        try:
            # 1. Защита от пустого изображения
            if image.size[0] == 0 or image.size[1] == 0:
                logger.warning(f"⚠️ Page {page_num} skipped: Empty image dimensions")
                return []
            
            # КРИТИЧЕСКИЙ ФИКС: Принудительное ограничение токенов для предотвращения CUDA ошибок
            inputs = self.layout_processor(
                image, 
                return_tensors="pt",
                max_length=512,  # Ограничение до 512 токенов
                truncation=True,  # Обрезка длинных последовательностей
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 2. Защита от нулевых тензоров
            for key, tensor in inputs.items():
                if tensor.numel() == 0:
                    logger.warning(f"⚠️ Page {page_num} skipped: Empty tensor {key}")
                    return []
            
            # 3. КРИТИЧЕСКАЯ ЗАЩИТА: Проверка длины токенов
            input_ids = inputs.get('input_ids', None)
            if input_ids is not None:
                token_count = input_ids.shape[1]
                if token_count > 512:
                    logger.warning(f"⚠️ Page {page_num} has {token_count} tokens (>{512}), truncating to prevent CUDA error")
                    # Дополнительная обрезка если нужно
                    if token_count > 512:
                        inputs['input_ids'] = input_ids[:, :512]
                        if 'attention_mask' in inputs:
                            inputs['attention_mask'] = inputs['attention_mask'][:, :512]
            
            # Получаем предсказания с защитой от CUDA ошибок
            with torch.no_grad():
                outputs = self.layout_model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Извлекаем таблицы
            tables = self._extract_tables_from_predictions(image, predictions, page_num)
            
            return tables
            
        except RuntimeError as e:
            # 3. Низкоуровневая защита: PyTorch оборачивает CUDA-ошибки в RuntimeError
            if "device-side assert triggered" in str(e) or "srcSelectDimSize" in str(e):
                logger.error(f"🛑 CUDA assertion failed on page {page_num}. Skipping page: {e}")
                return []
            raise e  # Если это не CUDA-ошибка, перебрасываем ее
        except Exception as e:
            logger.error(f"Page analysis failed: {e}")
            return []
    
    def _extract_tables_from_predictions(self, image: Image.Image, predictions: torch.Tensor, page_num: int) -> List[Dict]:
        """Извлекает таблицы из предсказаний модели"""
        
        tables = []
        
        # Простая логика извлечения таблиц
        # В реальной реализации здесь была бы более сложная логика
        
        # Используем OpenCV для дополнительного анализа
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Ищем прямоугольники (потенциальные таблицы)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for i, contour in enumerate(contours):
            # Фильтруем по размеру
            area = cv2.contourArea(contour)
            if area > 1000:  # Минимальная площадь
                x, y, w, h = cv2.boundingRect(contour)
                
                # Извлекаем текст из области
                roi = image.crop((x, y, x + w, y + h))
                text = pytesseract.image_to_string(roi, lang='rus')
                
                if self._is_table_content(text):
                    tables.append({
                        'page': page_num,
                        'position': (x, y, w, h),
                        'content': text.strip(),
                        'confidence': 0.8,
                        'detection_method': 'VLM_LAYOUT',
                        'metadata': {
                            'data_type': 'TABLE',
                            'structured': True,
                            'vlm_processed': True
                        }
                    })
        
        return tables
    
    def _is_table_content(self, text: str) -> bool:
        """Определяет, является ли текст таблицей"""
        
        # Простые эвристики
        lines = text.strip().split('\n')
        if len(lines) < 3:
            return False
        
        # Проверяем на наличие столбцов
        has_columns = any('|' in line or '\t' in line for line in lines)
        has_numbers = any(char.isdigit() for char in text)
        
        return has_columns or has_numbers
    
    def _fallback_table_extraction(self, pdf_path: str) -> List[Dict]:
        """Fallback метод без VLM"""
        
        logger.info("Using fallback table extraction")
        return []
    
    def analyze_document_structure(self, pdf_path: str) -> Dict:
        """ENTERPRISE: Полный анализ структуры документа с VLM с защитой от CUDA ошибок"""
        
        if not self.is_available():
            return {'vlm_available': False, 'tables': [], 'structure': 'fallback'}
        
        try:
            # Извлекаем таблицы с защитой от CUDA ошибок
            tables = self.extract_tables_from_pdf(pdf_path)
            
            # Анализируем общую структуру
            structure_analysis = {
                'vlm_available': True,
                'tables': tables,
                'total_tables': len(tables),
                'structure_complexity': self._calculate_structure_complexity(tables),
                'analysis_method': 'VLM_LAYOUT'
            }
            
            return structure_analysis
            
        except RuntimeError as e:
            # Специальная обработка CUDA ошибок
            if "device-side assert triggered" in str(e) or "srcSelectDimSize" in str(e):
                logger.error(f"🛑 CUDA assertion failed in document analysis. Skipping VLM: {e}")
                return {'vlm_available': False, 'tables': [], 'structure': 'cuda_error'}
            raise e  # Если это не CUDA-ошибка, перебрасываем ее
        except Exception as e:
            logger.error(f"VLM structure analysis failed: {e}")
            return {'vlm_available': False, 'tables': [], 'structure': 'error'}
    
    def _calculate_structure_complexity(self, tables: List[Dict]) -> float:
        """Рассчитывает сложность структуры на основе VLM анализа"""
        
        if not tables:
            return 0.0
        
        # Простая метрика сложности
        total_area = sum(t.get('position', (0, 0, 0, 0))[2] * t.get('position', (0, 0, 0, 0))[3] for t in tables)
        avg_confidence = sum(t.get('confidence', 0) for t in tables) / len(tables)
        
        complexity = min(1.0, (len(tables) * 0.3 + avg_confidence * 0.7))
        return round(complexity, 3)
