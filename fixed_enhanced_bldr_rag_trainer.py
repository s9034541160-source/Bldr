#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIXED ENHANCED BLDR RAG TRAINER V3 - ПРАВИЛЬНЫЕ ЭТАПЫ
====================================================

ИСПРАВЛЕННЫЙ ПАЙПЛАЙН СО ВСЕМИ ЭТАПАМИ ПО ИДЕАЛЬНОМУ ПЛАНУ:

Stage 0: Smart File Scanning + NTD Preprocessing  
Stage 1: Initial Validation (file_exists, file_size, can_read)
Stage 2: Duplicate Checking (MD5/SHA256, Qdrant, processed_files.json)
Stage 3: Text Extraction (PDF PyPDF2+OCR, DOCX, Excel)
Stage 4: Document Type Detection (симбиотический: regex + SBERT)
Stage 5: Structural Analysis (ПОЛНАЯ рекурсивная структура)
Stage 6: Regex to SBERT (seed works extraction)
Stage 7: SBERT Markup (ПОЛНАЯ структура + граф)
Stage 8: Metadata Extraction (ТОЛЬКО из структуры Stage 5)
Stage 9: Quality Control
Stage 10: Type-specific Processing
Stage 11: Work Sequence Extraction
Stage 12: Save Work Sequences (Neo4j)
Stage 13: Smart Chunking (1 пункт = 1 чанк)
Stage 14: Save to Qdrant

ЗАМЕНЫ:
- Rubern → SBERT (качественные русские эмбеддинги)
- Эмодзи → обычный текст (исправлена кодировка)
- Подробные логи на каждом этапе
"""

import os
import sys
import json
import hashlib
import time
import glob
import logging
import traceback
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional, Union
import re

# Импорты для обработки файлов
try:
    import PyPDF2
    import pytesseract
    from PIL import Image
    import docx
    import pandas as pd
    HAS_FILE_PROCESSING = True
except ImportError as e:
    print(f"WARNING: File processing libraries not available: {e}")
    HAS_FILE_PROCESSING = False

# Импорты для ML/AI
try:
    from sentence_transformers import SentenceTransformer
    import torch
    import faiss
    HAS_ML_LIBS = True
except ImportError as e:
    print(f"WARNING: ML libraries not available: {e}")
    HAS_ML_LIBS = False

# Импорты для баз данных
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    import neo4j
    HAS_DB_LIBS = True
except ImportError as e:
    print(f"WARNING: Database libraries not available: {e}")
    HAS_DB_LIBS = False

# Настройка логирования БЕЗ ЭМОДЗИ (исправлена кодировка)
def setup_logging():
    """Настройка логирования без эмодзи для Windows"""
    
    # Создаем папку для логов
    log_dir = Path("C:/Bldr/logs")
    log_dir.mkdir(exist_ok=True)
    
    # Формат без эмодзи
    log_format = '%(asctime)s - [STAGE %(levelname)s] - %(message)s'
    
    # Настраиваем логгеры
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(
                log_dir / f'fixed_rag_trainer_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
                encoding='utf-8'
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=== FIXED ENHANCED BLDR RAG TRAINER V3 STARTED ===")
    return logger

logger = setup_logging()

@dataclass
class DocumentMetadata:
    """Метаданные документа"""
    materials: List[str] = field(default_factory=list)
    finances: List[str] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    doc_numbers: List[str] = field(default_factory=list)
    quality_score: float = 0.0

@dataclass
class WorkSequence:
    """Рабочая последовательность"""
    name: str
    deps: List[str] = field(default_factory=list)
    duration: float = 0.0
    priority: int = 0
    quality_score: float = 0.0
    doc_type: str = ""
    section: str = ""

@dataclass 
class DocumentChunk:
    """Чанк документа"""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    section_id: str = ""
    chunk_type: str = "paragraph"  # paragraph, table, list, header
    embedding: Optional[List[float]] = None

class FixedEnhancedBldrRAGTrainer:
    """
    ИСПРАВЛЕННЫЙ Enhanced RAG Trainer с правильными этапами
    
    Все этапы соответствуют идеальному пайплайну:
    - Stage 0: Smart File Scanning + NTD Preprocessing
    - Stage 1-8: Основные этапы обработки 
    - Stage 9-14: Финальные этапы и сохранение
    """
    
    def __init__(self, base_dir: str = None):
        """Инициализация тренера"""
        
        logger.info("=== INITIALIZING FIXED ENHANCED RAG TRAINER ===")
        
        # Базовые пути
        self.base_dir = Path(base_dir) if base_dir else Path(os.getenv("BASE_DIR", "I:/docs"))
        self.reports_dir = self.base_dir / "reports"
        self.cache_dir = self.base_dir / "cache"
        self.processed_files_json = self.base_dir / "processed_files.json"
        
        # Создаем папки
        for dir_path in [self.reports_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Статистика
        self.stats = {
            'files_found': 0,
            'files_processed': 0,
            'files_failed': 0,
            'total_chunks': 0,
            'total_works': 0,
            'start_time': time.time()
        }
        
        # Инициализация компонентов
        self._init_sbert_model()
        self._init_databases()
        self._load_processed_files()
        
        logger.info(f"Base directory: {self.base_dir}")
        logger.info(f"SBERT model loaded: {hasattr(self, 'sbert_model')}")
        logger.info(f"Databases connected: Qdrant={hasattr(self, 'qdrant')}, Neo4j={hasattr(self, 'neo4j')}")
        logger.info("=== INITIALIZATION COMPLETE ===")
    
    def _init_sbert_model(self):
        """Инициализация SBERT модели"""
        
        if not HAS_ML_LIBS:
            logger.warning("ML libraries not available - using mock SBERT")
            self.sbert_model = None
            return
        
        try:
            logger.info("Loading SBERT model: ai-forever/sbert_large_nlu_ru")
            
            # Проверяем GPU
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Using device: {device}")
            if device == 'cuda':
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"GPU detected: {gpu_name}")
            
            # Загружаем модель
            self.sbert_model = SentenceTransformer('ai-forever/sbert_large_nlu_ru', device=device)
            logger.info("SBERT model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load SBERT model: {e}")
            self.sbert_model = None
    
    def _init_databases(self):
        """Инициализация баз данных"""
        
        # Qdrant
        try:
            self.qdrant = QdrantClient(path=str(self.base_dir / "qdrant_db"))
            
            # Создаем коллекцию если не существует
            collections = self.qdrant.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if "bldr_docs" not in collection_names:
                self.qdrant.create_collection(
                    collection_name="bldr_docs",
                    vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE)
                )
                logger.info("Created Qdrant collection: bldr_docs")
            else:
                logger.info("Qdrant collection exists: bldr_docs")
                
        except Exception as e:
            logger.error(f"Failed to init Qdrant: {e}")
            self.qdrant = None
        
        # Neo4j (опционально)
        try:
            if HAS_DB_LIBS:
                self.neo4j = neo4j.GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
                logger.info("Neo4j connected successfully")
            else:
                self.neo4j = None
        except Exception as e:
            logger.warning(f"Neo4j not available: {e}")
            self.neo4j = None
    
    def _load_processed_files(self):
        """Загрузка списка обработанных файлов"""
        
        try:
            if self.processed_files_json.exists():
                with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                    self.processed_files = json.load(f)
                logger.info(f"Loaded {len(self.processed_files)} processed files")
            else:
                self.processed_files = {}
                logger.info("No processed files found - starting fresh")
        except Exception as e:
            logger.error(f"Failed to load processed files: {e}")
            self.processed_files = {}
    
    def train(self, max_files: Optional[int] = None):
        """
        Главный метод обучения с правильными этапами
        
        Args:
            max_files: Максимальное количество файлов для обработки
        """
        
        logger.info("=== STARTING FIXED RAG TRAINING ===")
        logger.info(f"Max files: {max_files if max_files else 'ALL'}")
        
        start_time = time.time()
        
        try:
            # ===== STAGE 0: Smart File Scanning + NTD Preprocessing =====
            all_files = self._stage_0_smart_file_scanning_and_preprocessing(max_files)
            
            if not all_files:
                logger.warning("No files found for processing")
                return
            
            self.stats['files_found'] = len(all_files)
            logger.info(f"Total files to process: {len(all_files)}")
            
            # Обработка каждого файла через полный пайплайн
            for i, file_path in enumerate(all_files, 1):
                logger.info(f"\n=== PROCESSING FILE {i}/{len(all_files)}: {Path(file_path).name} ===")
                
                try:
                    success = self._process_single_file(file_path)
                    if success:
                        self.stats['files_processed'] += 1
                        logger.info(f"File processed successfully: {Path(file_path).name}")
                    else:
                        self.stats['files_failed'] += 1
                        logger.warning(f"File processing failed: {Path(file_path).name}")
                        
                except Exception as e:
                    self.stats['files_failed'] += 1
                    logger.error(f"Error processing file {file_path}: {e}")
                    logger.error(traceback.format_exc())
            
            # Генерация финального отчета
            self._generate_final_report(time.time() - start_time)
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _process_single_file(self, file_path: str) -> bool:
        """Обработка одного файла через весь пайплайн"""
        
        try:
            # ===== STAGE 1: Initial Validation =====
            validation_result = self._stage1_initial_validation(file_path)
            if not validation_result['file_exists'] or not validation_result['can_read']:
                logger.warning(f"[Stage 1/14] File validation failed: {file_path}")
                return False
            
            # ===== STAGE 2: Duplicate Checking =====
            duplicate_result = self._stage2_duplicate_checking(file_path)
            if duplicate_result['is_duplicate']:
                logger.info(f"[Stage 2/14] File is duplicate, skipping: {file_path}")
                return False
            
            # ===== STAGE 3: Text Extraction =====
            content = self._stage3_text_extraction(file_path)
            if not content or len(content) < 50:
                logger.warning(f"[Stage 3/14] Text extraction failed or content too short: {file_path}")
                return False
            
            # ===== STAGE 4: Document Type Detection (симбиотический: regex + SBERT) =====
            doc_type_info = self._stage4_document_type_detection(content, file_path)
            
            # ===== STAGE 5: Structural Analysis (ПОЛНАЯ рекурсивная структура) =====
            structural_data = self._stage5_structural_analysis(content, doc_type_info)
            
            # ===== STAGE 6: Regex to SBERT (seed works extraction) =====
            seed_works = self._stage6_regex_to_sbert(content, doc_type_info, structural_data)
            
            # ===== STAGE 7: SBERT Markup (ПОЛНАЯ структура + граф) =====
            sbert_data = self._stage7_sbert_markup(content, seed_works, doc_type_info, structural_data)
            
            # ===== STAGE 8: Metadata Extraction (ТОЛЬКО из структуры Stage 5) =====
            metadata = self._stage8_metadata_extraction(content, structural_data, doc_type_info)
            
            # ===== STAGE 9: Quality Control =====
            quality_report = self._stage9_quality_control(
                content, doc_type_info, structural_data, sbert_data, metadata
            )
            
            # ===== STAGE 10: Type-specific Processing =====
            type_specific_data = self._stage10_type_specific_processing(
                content, doc_type_info, structural_data, sbert_data
            )
            
            # ===== STAGE 11: Work Sequence Extraction =====
            work_sequences = self._stage11_work_sequence_extraction(
                sbert_data, doc_type_info, metadata
            )
            
            # ===== STAGE 12: Save Work Sequences (Neo4j) =====
            saved_sequences = self._stage12_save_work_sequences(work_sequences, file_path)
            
            # ===== STAGE 13: Smart Chunking (1 пункт = 1 чанк) =====
            chunks = self._stage13_smart_chunking(content, structural_data, metadata, doc_type_info)
            
            # ===== STAGE 14: Save to Qdrant =====
            saved_chunks = self._stage14_save_to_qdrant(chunks, file_path, duplicate_result['file_hash'])
            
            # Обновляем статистику
            self.stats['total_chunks'] += len(chunks)
            self.stats['total_works'] += len(work_sequences)
            
            # Сохраняем в processed_files
            self._update_processed_files(file_path, duplicate_result['file_hash'], {
                'chunks_count': len(chunks),
                'works_count': len(work_sequences),
                'doc_type': doc_type_info['doc_type'],
                'quality_score': quality_report['quality_score'],
                'processed_at': datetime.now().isoformat()
            })
            
            logger.info(f"[COMPLETE] File processed: {len(chunks)} chunks, {len(work_sequences)} works, quality: {quality_report['quality_score']:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error in single file processing: {e}")
            logger.error(traceback.format_exc())
            return False
    
    # =================================================================
    # STAGE IMPLEMENTATIONS
    # =================================================================
    
    def _stage_0_smart_file_scanning_and_preprocessing(self, max_files: Optional[int] = None) -> List[str]:
        """
        STAGE 0: Smart File Scanning + NTD Preprocessing
        
        Сканирует файлы и выполняет предварительную обработку НТД
        """
        
        logger.info("[Stage 0/14] SMART FILE SCANNING + NTD PREPROCESSING")
        start_time = time.time()
        
        # Паттерны файлов для поиска
        file_patterns = ['*.pdf', '*.docx', '*.doc', '*.txt', '*.rtf']
        all_files = []
        
        # Ищем файлы
        for pattern in file_patterns:
            pattern_files = glob.glob(str(self.base_dir / '**' / pattern), recursive=True)
            all_files.extend(pattern_files)
            logger.info(f"Found {len(pattern_files)} {pattern} files")
        
        # Фильтрация файлов
        valid_files = []
        for file_path in all_files:
            if self._is_valid_file(file_path):
                valid_files.append(file_path)
        
        logger.info(f"Valid files after filtering: {len(valid_files)}")
        
        # Ограничиваем количество если задано
        if max_files and len(valid_files) > max_files:
            valid_files = valid_files[:max_files]
            logger.info(f"Limited to {max_files} files")
        
        # NTD Preprocessing (сортировка по приоритету)
        prioritized_files = self._ntd_preprocessing(valid_files)
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 0/14] COMPLETE - Found {len(prioritized_files)} files in {elapsed:.2f}s")
        
        return prioritized_files
    
    def _is_valid_file(self, file_path: str) -> bool:
        """Проверка валидности файла"""
        
        try:
            path = Path(file_path)
            
            # Проверяем существование
            if not path.exists():
                return False
            
            # Проверяем размер (от 1KB до 100MB)
            size = path.stat().st_size
            if size < 1024 or size > 100 * 1024 * 1024:
                return False
            
            # Исключаем системные файлы
            exclude_patterns = ['temp', 'tmp', 'cache', '__pycache__', '.git', 'backup']
            file_str = str(path).lower()
            if any(pattern in file_str for pattern in exclude_patterns):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _ntd_preprocessing(self, files: List[str]) -> List[str]:
        """NTD Preprocessing - сортировка по приоритету"""
        
        # Приоритеты типов документов
        type_priorities = {
            'gost': 10,    # ГОСТ - максимальный приоритет
            'sp': 9,       # СП - своды правил
            'snip': 8,     # СНиП
            'ppr': 6,      # ППР
            'smeta': 4,    # Сметы
            'other': 2     # Остальное
        }
        
        # Определяем тип и приоритет для каждого файла
        prioritized = []
        for file_path in files:
            priority = self._get_file_priority(file_path, type_priorities)
            prioritized.append((file_path, priority))
        
        # Сортируем по приоритету (высший первый)
        prioritized.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"NTD Preprocessing: Prioritized {len(prioritized)} files")
        
        return [file_path for file_path, _ in prioritized]
    
    def _get_file_priority(self, file_path: str, priorities: Dict[str, int]) -> int:
        """Определение приоритета файла по имени"""
        
        filename = Path(file_path).name.lower()
        
        # Ищем ключевые слова
        if any(word in filename for word in ['гост', 'gost']):
            return priorities['gost']
        elif any(word in filename for word in ['сп', 'sp']) and 'свод' in filename:
            return priorities['sp']
        elif any(word in filename for word in ['снип', 'snip']):
            return priorities['snip']
        elif any(word in filename for word in ['ппр', 'ppr', 'технологическая карта']):
            return priorities['ppr']
        elif any(word in filename for word in ['смета', 'расценк', 'стоимость']):
            return priorities['smeta']
        else:
            return priorities['other']
    
    def _stage1_initial_validation(self, file_path: str) -> Dict[str, Any]:
        """
        STAGE 1: Initial Validation
        
        Проверка существования файла, его размера и доступности
        """
        
        logger.info(f"[Stage 1/14] INITIAL VALIDATION: {Path(file_path).name}")
        start_time = time.time()
        
        result = {
            'file_exists': False,
            'file_size': 0,
            'can_read': False
        }
        
        try:
            path = Path(file_path)
            
            # Проверяем существование
            result['file_exists'] = path.exists()
            
            if result['file_exists']:
                # Получаем размер
                result['file_size'] = path.stat().st_size
                
                # Проверяем возможность чтения
                try:
                    with open(path, 'rb') as f:
                        f.read(100)  # Пробуем прочитать первые 100 байт
                    result['can_read'] = True
                except:
                    result['can_read'] = False
        
        except Exception as e:
            logger.warning(f"Validation error: {e}")
        
        elapsed = time.time() - start_time
        
        if result['file_exists'] and result['can_read']:
            logger.info(f"[Stage 1/14] COMPLETE - File valid, size: {result['file_size']} bytes ({elapsed:.2f}s)")
        else:
            logger.warning(f"[Stage 1/14] FAILED - File invalid ({elapsed:.2f}s)")
        
        return result
    
    def _stage2_duplicate_checking(self, file_path: str) -> Dict[str, Any]:
        """
        STAGE 2: Duplicate Checking
        
        Вычисление хеша файла и проверка дубликатов
        """
        
        logger.info(f"[Stage 2/14] DUPLICATE CHECKING: {Path(file_path).name}")
        start_time = time.time()
        
        # Вычисляем хеш файла
        file_hash = self._calculate_file_hash(file_path)
        
        # Проверяем в processed_files.json
        is_duplicate = file_hash in self.processed_files
        
        # Проверяем в Qdrant (если доступен)
        if not is_duplicate and self.qdrant:
            try:
                # Ищем по хешу в метаданных
                search_result = self.qdrant.scroll(
                    collection_name="bldr_docs",
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="file_hash",
                                match=models.MatchValue(value=file_hash)
                            )
                        ]
                    ),
                    limit=1
                )
                is_duplicate = len(search_result[0]) > 0
                
            except Exception as e:
                logger.warning(f"Qdrant duplicate check failed: {e}")
        
        result = {
            'is_duplicate': is_duplicate,
            'file_hash': file_hash
        }
        
        elapsed = time.time() - start_time
        
        if is_duplicate:
            logger.info(f"[Stage 2/14] DUPLICATE FOUND - Hash: {file_hash[:16]}... ({elapsed:.2f}s)")
        else:
            logger.info(f"[Stage 2/14] UNIQUE FILE - Hash: {file_hash[:16]}... ({elapsed:.2f}s)")
        
        return result
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Вычисление MD5 хеша файла"""
        
        hasher = hashlib.md5()
        
        try:
            with open(file_path, 'rb') as f:
                # Читаем файл кусками для больших файлов
                while chunk := f.read(8192):
                    hasher.update(chunk)
                    
            return hasher.hexdigest()
            
        except Exception as e:
            logger.error(f"Hash calculation failed: {e}")
            # Возвращаем хеш имени файла + размера как fallback
            fallback_string = f"{file_path}_{os.path.getsize(file_path)}"
            return hashlib.md5(fallback_string.encode()).hexdigest()
    
    def _stage3_text_extraction(self, file_path: str) -> str:
        """
        STAGE 3: Text Extraction
        
        Извлечение текста из различных форматов файлов
        """
        
        logger.info(f"[Stage 3/14] TEXT EXTRACTION: {Path(file_path).name}")
        start_time = time.time()
        
        content = ""
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.pdf':
                content = self._extract_from_pdf(file_path)
            elif file_ext in ['.docx', '.doc']:
                content = self._extract_from_docx(file_path)
            elif file_ext in ['.txt', '.rtf']:
                content = self._extract_from_txt(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                content = self._extract_from_excel(file_path)
            else:
                logger.warning(f"Unsupported file format: {file_ext}")
                
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
        
        # Очистка текста
        if content:
            content = self._clean_text(content)
        
        elapsed = time.time() - start_time
        char_count = len(content)
        
        if char_count > 50:
            logger.info(f"[Stage 3/14] COMPLETE - Extracted {char_count} characters ({elapsed:.2f}s)")
        else:
            logger.warning(f"[Stage 3/14] FAILED - Only {char_count} characters extracted ({elapsed:.2f}s)")
        
        return content
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Извлечение текста из PDF"""
        
        if not HAS_FILE_PROCESSING:
            return "PDF processing not available"
        
        content = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    content += page.extract_text() + "\n"
                    
        except Exception as e:
            logger.warning(f"PyPDF2 failed, trying OCR fallback: {e}")
            # OCR fallback с Tesseract
            content = self._ocr_fallback_pdf(file_path)
            
        return content
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Извлечение текста из DOCX"""
        
        if not HAS_FILE_PROCESSING:
            return "DOCX processing not available"
        
        try:
            doc = docx.Document(file_path)
            content = ""
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
            return content
            
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            return ""
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Извлечение текста из TXT/RTF"""
        
        encodings = ['utf-8', 'cp1251', 'cp866', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        logger.warning(f"Could not decode text file with any encoding: {file_path}")
        return ""
    
    def _extract_from_excel(self, file_path: str) -> str:
        """Извлечение текста из Excel"""
        
        if not HAS_FILE_PROCESSING:
            return "Excel processing not available"
        
        try:
            df = pd.read_excel(file_path, sheet_name=None)  # Читаем все листы
            content = ""
            
            for sheet_name, sheet_df in df.items():
                content += f"=== Sheet: {sheet_name} ===\n"
                content += sheet_df.to_string() + "\n\n"
                
            return content
            
        except Exception as e:
            logger.error(f"Excel extraction failed: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Очистка и нормализация текста"""
        
        if not text:
            return ""
        
        # Удаляем лишние пробелы и переносы
        text = re.sub(r'\s+', ' ', text)
        
        # Удаляем специальные символы (кроме русских букв, цифр и знаков препинания)
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'№]', ' ', text, flags=re.UNICODE)
        
        # Удаляем множественные пробелы
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def _ocr_fallback_pdf(self, file_path: str) -> str:
        """Полноценный OCR fallback для PDF файлов"""
        
        try:
            # Пробуем через fitz (PyMuPDF) сначала
            try:
                import fitz  # PyMuPDF
                
                logger.info(f"Trying PyMuPDF extraction for: {Path(file_path).name}")
                doc = fitz.open(file_path)
                content = ""
                
                for page_num in range(min(len(doc), 20)):  # Максимум 20 страниц
                    page = doc[page_num]
                    content += page.get_text() + "\n"
                
                doc.close()
                
                if len(content.strip()) > 100:  # Если получили текст
                    logger.info(f"PyMuPDF extracted {len(content)} characters")
                    return content
                    
            except ImportError:
                logger.debug("PyMuPDF not available, trying Tesseract OCR")
            except Exception as e:
                logger.debug(f"PyMuPDF failed: {e}, trying Tesseract OCR")
            
            # Если PyMuPDF не сработал - пробуем OCR
            if HAS_FILE_PROCESSING:
                logger.info(f"Trying Tesseract OCR for: {Path(file_path).name}")
                return self._tesseract_ocr_pdf(file_path)
            else:
                logger.warning("OCR libraries not available")
                return ""
                
        except Exception as e:
            logger.error(f"All OCR methods failed for {file_path}: {e}")
            return ""
    
    def _tesseract_ocr_pdf(self, file_path: str) -> str:
        """Использование Tesseract OCR для PDF"""
        
        try:
            # Конвертируем PDF в изображения и применяем OCR
            from pdf2image import convert_from_path
            import pytesseract
            
            # Конвертируем первые 5 страниц (OCR медленный)
            images = convert_from_path(
                file_path, 
                dpi=200,
                first_page=1, 
                last_page=5,
                fmt='jpeg',
                thread_count=2
            )
            
            content = ""
            for i, image in enumerate(images):
                logger.debug(f"OCR processing page {i+1}/{len(images)}")
                
                # Применяем OCR к странице
                page_text = pytesseract.image_to_string(
                    image, 
                    lang='rus+eng',  # Поддержка русского и английского
                    config='--psm 1 --oem 3'
                )
                
                content += f"\n=== Страница {i+1} ===\n{page_text}\n"
            
            logger.info(f"OCR extracted {len(content)} characters from {len(images)} pages")
            return content
            
        except ImportError as e:
            logger.warning(f"OCR dependencies not available: {e}")
            # Простой fallback - попытаемся создать хотя бы что-то
            return f"Документ: {Path(file_path).name}\nНе удалось извлечь текст (OCR недоступен)."
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return ""
    
    def _stage4_document_type_detection(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        STAGE 4: Document Type Detection (симбиотический: regex + SBERT)
        
        Определение типа документа комбинированным методом
        """
        
        logger.info(f"[Stage 4/14] DOCUMENT TYPE DETECTION: {Path(file_path).name}")
        start_time = time.time()
        
        # Шаг 1: Regex анализ (быстрый)
        regex_result = self._regex_type_detection(content, file_path)
        
        # Шаг 2: SBERT анализ (качественный) 
        sbert_result = self._sbert_type_detection(content)
        
        # Шаг 3: Симбиоз результатов
        final_result = self._combine_type_detection(regex_result, sbert_result)
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 4/14] COMPLETE - Type: {final_result['doc_type']}, "
                   f"Subtype: {final_result['doc_subtype']}, "
                   f"Confidence: {final_result['confidence']:.2f} ({elapsed:.2f}s)")
        
        return final_result
    
    def _regex_type_detection(self, content: str, file_path: str) -> Dict[str, Any]:
        """Regex-based тип определение"""
        
        filename = Path(file_path).name.lower()
        content_lower = content.lower()[:2000]  # Первые 2000 символов
        
        # Паттерны для разных типов
        type_patterns = {
            'norms': {
                'patterns': [r'\bгост\b', r'\bсп\s+\d+', r'\bснип\b', r'государственный.*стандарт'],
                'subtypes': {
                    'gost': [r'\bгост\s+\d+'],
                    'sp': [r'\bсп\s+\d+', r'свод.*правил'],
                    'snip': [r'\bснип\s+\d+']
                }
            },
            'ppr': {
                'patterns': [r'\bппр\b', r'проект.*производства.*работ', r'технологическая.*карта'],
                'subtypes': {
                    'tech_card': [r'технологическая.*карта', r'тк\s+\d+'],
                    'work_project': [r'ппр', r'проект.*производства']
                }
            },
            'smeta': {
                'patterns': [r'\bсмета\b', r'расценк', r'калькуляц', r'стоимость.*работ'],
                'subtypes': {
                    'estimate': [r'\bсмета\b', r'калькуляц'],
                    'rates': [r'расценк', r'тарифы']
                }
            }
        }
        
        # Подсчет совпадений
        best_type = 'other'
        best_subtype = 'general'
        best_score = 0.0
        
        for doc_type, type_info in type_patterns.items():
            score = 0.0
            
            # Проверяем основные паттерны
            for pattern in type_info['patterns']:
                matches_content = len(re.findall(pattern, content_lower))
                matches_filename = len(re.findall(pattern, filename))
                score += matches_content * 0.7 + matches_filename * 0.9  # Имя файла важнее
            
            if score > best_score:
                best_score = score
                best_type = doc_type
                
                # Определяем подтип
                for subtype, subtype_patterns in type_info['subtypes'].items():
                    for pattern in subtype_patterns:
                        if re.search(pattern, content_lower) or re.search(pattern, filename):
                            best_subtype = subtype
                            break
        
        # Нормализуем счет (0-1)
        confidence = min(best_score / 10.0, 1.0) if best_score > 0 else 0.1
        
        return {
            'doc_type': best_type,
            'doc_subtype': best_subtype,
            'confidence': confidence,
            'method': 'regex'
        }
    
    def _sbert_type_detection(self, content: str) -> Dict[str, Any]:
        """SBERT-based тип определение"""
        
        if not self.sbert_model or not HAS_ML_LIBS:
            return {
                'doc_type': 'other',
                'doc_subtype': 'general',
                'confidence': 0.0,
                'method': 'sbert_unavailable'
            }
        
        try:
            # Примеры текстов для разных типов (templates)
            type_templates = {
                'norms': "ГОСТ стандарт технические требования нормативные документы свод правил СНиП строительные нормы",
                'ppr': "проект производства работ технологическая карта последовательность выполнения этапы строительства",
                'smeta': "смета расценки стоимость калькуляция цена материалы объем работ"
            }
            
            # Получаем embedding для контента (первые 500 слов)
            content_words = content.split()[:500]
            content_sample = ' '.join(content_words)
            content_embedding = self.sbert_model.encode([content_sample])
            
            # Получаем embeddings для шаблонов
            template_embeddings = self.sbert_model.encode(list(type_templates.values()))
            
            # Вычисляем сходство
            from numpy import dot
            from numpy.linalg import norm
            
            similarities = []
            for i, template_emb in enumerate(template_embeddings):
                sim = dot(content_embedding[0], template_emb) / (norm(content_embedding[0]) * norm(template_emb))
                similarities.append(sim)
            
            # Находим лучшее совпадение
            best_idx = max(range(len(similarities)), key=lambda i: similarities[i])
            best_type = list(type_templates.keys())[best_idx]
            confidence = max(similarities)
            
            # Подтипы (упрощенно)
            subtypes_map = {
                'norms': 'general',
                'ppr': 'tech_card',
                'smeta': 'estimate'
            }
            
            return {
                'doc_type': best_type if confidence > 0.3 else 'other',
                'doc_subtype': subtypes_map.get(best_type, 'general'),
                'confidence': float(confidence),
                'method': 'sbert'
            }
            
        except Exception as e:
            logger.warning(f"SBERT type detection failed: {e}")
            return {
                'doc_type': 'other',
                'doc_subtype': 'general',
                'confidence': 0.0,
                'method': 'sbert_error'
            }
    
    def _combine_type_detection(self, regex_result: Dict, sbert_result: Dict) -> Dict[str, Any]:
        """Комбинирование результатов regex и SBERT"""
        
        # Веса для методов
        regex_weight = 0.6
        sbert_weight = 0.4
        
        # Если типы совпадают - усиливаем confidence
        if regex_result['doc_type'] == sbert_result['doc_type']:
            combined_confidence = min(
                regex_result['confidence'] * regex_weight + sbert_result['confidence'] * sbert_weight + 0.2,
                1.0
            )
            doc_type = regex_result['doc_type']
            doc_subtype = regex_result['doc_subtype']  # Regex лучше определяет подтипы
        else:
            # Берем результат с более высокой confidence
            if regex_result['confidence'] > sbert_result['confidence']:
                doc_type = regex_result['doc_type']
                doc_subtype = regex_result['doc_subtype']
                combined_confidence = regex_result['confidence']
            else:
                doc_type = sbert_result['doc_type']
                doc_subtype = sbert_result['doc_subtype']
                combined_confidence = sbert_result['confidence']
        
        return {
            'doc_type': doc_type,
            'doc_subtype': doc_subtype,
            'confidence': combined_confidence,
            'methods_used': f"regex({regex_result['confidence']:.2f}) + sbert({sbert_result['confidence']:.2f})"
        }
    
    def _stage5_structural_analysis(self, content: str, doc_type_info: Dict) -> Dict[str, Any]:
        """
        STAGE 5: Structural Analysis (ПОЛНАЯ рекурсивная структура)
        
        Создает детальную структуру документа для использования в следующих этапах
        """
        
        logger.info(f"[Stage 5/14] STRUCTURAL ANALYSIS - Type: {doc_type_info['doc_type']}")
        start_time = time.time()
        
        # Импортируем наш рекурсивный чанкер
        try:
            from recursive_hierarchical_chunker import RecursiveHierarchicalChunker
            
            chunker = RecursiveHierarchicalChunker(
                target_chunk_size=400,
                min_chunk_size=100,
                max_chunk_size=800
            )
            
            # Создаем полную иерархическую структуру
            hierarchical_chunks = chunker.create_hierarchical_chunks(content)
            structural_data = {
                'sections': [],
                'paragraphs_count': 0,
                'tables': [],
                'structural_completeness': 1.0,
                'analysis_method': 'recursive_hierarchical'
            }
            
            # Преобразуем иерархические чанки в структуру
            for i, chunk in enumerate(hierarchical_chunks):
                if hasattr(chunk, 'content') and chunk.content:
                    structural_data['sections'].append({
                        'title': getattr(chunk, 'title', f'Раздел {i+1}'),
                        'content': chunk.content,
                        'level': getattr(chunk, 'level', 1),
                        'start_line': 0,
                        'end_line': len(chunk.content.split('\n'))
                    })
            
            structural_data['paragraphs_count'] = sum(len(section['content'].split('\n')) for section in structural_data['sections'])
            
        except ImportError:
            logger.warning("RecursiveHierarchicalChunker not available, using basic analysis")
            structural_data = self._basic_structural_analysis(content, doc_type_info)
        
        # Дополнительная обработка в зависимости от типа документа
        if doc_type_info['doc_type'] == 'norms':
            structural_data = self._enhance_norms_structure(structural_data, content)
        elif doc_type_info['doc_type'] == 'ppr':
            structural_data = self._enhance_ppr_structure(structural_data, content)
        elif doc_type_info['doc_type'] == 'smeta':
            structural_data = self._enhance_smeta_structure(structural_data, content)
        
        elapsed = time.time() - start_time
        
        # Статистика
        sections_count = len(structural_data.get('sections', []))
        paragraphs_count = structural_data.get('paragraphs_count', 0)
        tables_count = len(structural_data.get('tables', []))
        
        logger.info(f"[Stage 5/14] COMPLETE - Sections: {sections_count}, "
                   f"Paragraphs: {paragraphs_count}, Tables: {tables_count} ({elapsed:.2f}s)")
        
        return structural_data
    
    def _basic_structural_analysis(self, content: str, doc_type_info: Dict) -> Dict[str, Any]:
        """Базовый структурный анализ если рекурсивный чанкер недоступен"""
        
        lines = content.split('\n')
        
        # Находим заголовки (простые эвристики)
        sections = []
        current_section = {'title': 'Начало документа', 'content': '', 'level': 0, 'start_line': 0}
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Определяем заголовки по паттернам
            if (re.match(r'^\d+\.?\s+[А-ЯЁ]', line) or  # "1. ЗАГОЛОВОК"
                re.match(r'^[А-ЯЁ\s]{10,}$', line) or     # "ЗАГОЛОВОК БОЛЬШИМИ БУКВАМИ"  
                re.match(r'^\d+\.\d+\.?\s+', line)):       # "1.1. Подзаголовок"
                
                # Сохраняем предыдущую секцию
                if current_section['content']:
                    current_section['end_line'] = i
                    sections.append(current_section.copy())
                
                # Начинаем новую секцию
                level = line.count('.') if '.' in line else 1
                current_section = {
                    'title': line[:100],  # Ограничиваем длину заголовка
                    'content': '',
                    'level': level,
                    'start_line': i
                }
            else:
                current_section['content'] += line + '\n'
        
        # Добавляем последнюю секцию
        if current_section['content']:
            current_section['end_line'] = len(lines)
            sections.append(current_section)
        
        # Находим таблицы (простое определение)
        tables = []
        table_patterns = [r'Таблица\s+\d+', r'Table\s+\d+', r'\|.*\|.*\|']
        
        for pattern in table_patterns:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            for match in matches:
                tables.append({
                    'title': match.group(),
                    'position': match.start(),
                    'content': content[match.start():match.start()+200]  # Первые 200 символов
                })
        
        return {
            'sections': sections,
            'paragraphs_count': len([line for line in lines if line.strip()]),
            'tables': tables,
            'structural_completeness': min(len(sections) / 5.0, 1.0),  # Ожидаем хотя бы 5 секций
            'analysis_method': 'basic'
        }
    
    def _enhance_norms_structure(self, structural_data: Dict, content: str) -> Dict:
        """Улучшение структуры для нормативных документов"""
        
        # Ищем специфичные элементы ГОСТов/СП
        norm_elements = []
        
        # Пункты и подпункты
        punkt_pattern = r'(\d+\.(?:\d+\.)*)\s+([А-ЯЁа-яё].*?)(?=\n\d+\.|\n[А-ЯЁ]{5,}|\Z)'
        punkts = re.findall(punkt_pattern, content, re.DOTALL)
        
        for nummer, text in punkts:
            norm_elements.append({
                'type': 'punkt',
                'number': nummer,
                'text': text.strip()[:200],
                'level': nummer.count('.')
            })
        
        structural_data['norm_elements'] = norm_elements
        structural_data['punkts_count'] = len(punkts)
        
        return structural_data
    
    def _enhance_ppr_structure(self, structural_data: Dict, content: str) -> Dict:
        """Улучшение структуры для ППР"""
        
        # Ищем этапы работ
        stages_pattern = r'(Этап\s+\d+|Стадия\s+\d+)[:\.]?\s+([А-ЯЁа-яё].*?)(?=Этап\s+\d+|Стадия\s+\d+|\Z)'
        stages = re.findall(stages_pattern, content, re.DOTALL | re.IGNORECASE)
        
        ppr_stages = []
        for stage_num, stage_text in stages:
            ppr_stages.append({
                'type': 'work_stage',
                'number': stage_num,
                'description': stage_text.strip()[:300]
            })
        
        structural_data['ppr_stages'] = ppr_stages
        structural_data['stages_count'] = len(ppr_stages)
        
        return structural_data
    
    def _enhance_smeta_structure(self, structural_data: Dict, content: str) -> Dict:
        """Улучшение структуры для смет"""
        
        # Ищем позиции сметы
        smeta_pattern = r'(\d+(?:\.\d+)*)\s+([А-ЯЁа-яё].*?)\s+(\d+[,.]?\d*)\s+(\d+[,.]?\d*)\s+(\d+[,.]?\d*)'
        positions = re.findall(smeta_pattern, content)
        
        smeta_items = []
        for pos_num, description, quantity, rate, sum_val in positions:
            smeta_items.append({
                'type': 'smeta_item',
                'position': pos_num,
                'description': description.strip()[:200],
                'quantity': quantity,
                'rate': rate,
                'sum': sum_val
            })
        
        structural_data['smeta_items'] = smeta_items
        structural_data['items_count'] = len(smeta_items)
        
        return structural_data
    
    def _stage6_regex_to_sbert(self, content: str, doc_type_info: Dict, structural_data: Dict) -> List[str]:
        """
        STAGE 6: Regex to SBERT (seed works extraction)
        
        Извлечение кандидатов-работ для передачи в SBERT
        """
        
        logger.info(f"[Stage 6/14] SEED WORKS EXTRACTION - Type: {doc_type_info['doc_type']}")
        start_time = time.time()
        
        seed_works = []
        
        # Извлекаем seeds в зависимости от типа документа
        if doc_type_info['doc_type'] == 'norms':
            seed_works = self._extract_norms_seeds(content, structural_data)
        elif doc_type_info['doc_type'] == 'ppr':
            seed_works = self._extract_ppr_seeds(content, structural_data)
        elif doc_type_info['doc_type'] == 'smeta':
            seed_works = self._extract_smeta_seeds(content, structural_data)
        else:
            seed_works = self._extract_generic_seeds(content, structural_data)
        
        # Фильтруем и нормализуем
        seed_works = self._filter_seed_works(seed_works)
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 6/14] COMPLETE - Extracted {len(seed_works)} seed works ({elapsed:.2f}s)")
        
        return seed_works
    
    def _extract_norms_seeds(self, content: str, structural_data: Dict) -> List[str]:
        """Извлечение seeds из нормативных документов"""
        
        seeds = []
        
        # Из пунктов
        if 'norm_elements' in structural_data:
            for element in structural_data['norm_elements']:
                if element['type'] == 'punkt' and len(element['text']) > 20:
                    seeds.append(f"п.{element['number']} {element['text']}")
        
        # Дополнительные паттерны для ГОСТов
        gost_patterns = [
            r'требования?\s+к\s+[А-ЯЁа-яё\s]+',
            r'методы?\s+[А-ЯЁа-яё\s]+',
            r'контроль\s+[А-ЯЁа-яё\s]+',
            r'испытания?\s+[А-ЯЁа-яё\s]+'
        ]
        
        for pattern in gost_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            seeds.extend([match[:100] for match in matches if len(match) > 10])
        
        return seeds
    
    def _extract_ppr_seeds(self, content: str, structural_data: Dict) -> List[str]:
        """Извлечение seeds из ППР"""
        
        seeds = []
        
        # Из этапов работ
        if 'ppr_stages' in structural_data:
            for stage in structural_data['ppr_stages']:
                seeds.append(f"{stage['number']}: {stage['description']}")
        
        # Операции и работы
        work_patterns = [
            r'выполнение\s+[А-ЯЁа-яё\s]+',
            r'установка\s+[А-ЯЁа-яё\s]+',
            r'монтаж\s+[А-ЯЁа-яё\s]+',
            r'демонтаж\s+[А-ЯЁа-яё\s]+',
            r'укладка\s+[А-ЯЁа-яё\s]+',
            r'бетонирование\s+[А-ЯЁа-яё\s]+',
            r'сварка\s+[А-ЯЁа-яё\s]+'
        ]
        
        for pattern in work_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            seeds.extend([match[:80] for match in matches if len(match) > 8])
        
        return seeds
    
    def _extract_smeta_seeds(self, content: str, structural_data: Dict) -> List[str]:
        """Извлечение seeds из смет"""
        
        seeds = []
        
        # Из позиций сметы
        if 'smeta_items' in structural_data:
            for item in structural_data['smeta_items']:
                seeds.append(f"Поз.{item['position']}: {item['description']}")
        
        # Виды работ
        work_types = [
            r'земляные\s+работы',
            r'бетонные\s+работы', 
            r'железобетонные\s+работы',
            r'каменные\s+работы',
            r'монтажные\s+работы',
            r'отделочные\s+работы'
        ]
        
        for pattern in work_types:
            matches = re.findall(pattern, content, re.IGNORECASE)
            seeds.extend([match for match in matches])
        
        return seeds
    
    def _extract_generic_seeds(self, content: str, structural_data: Dict) -> List[str]:
        """Общее извлечение seeds для неопределенных типов"""
        
        seeds = []
        
        # Из секций документа
        for section in structural_data.get('sections', []):
            if len(section['content']) > 30:
                # Берем первые предложения из каждой секции
                sentences = re.split(r'[.!?]\s+', section['content'])
                for sentence in sentences[:2]:  # Максимум 2 предложения
                    if len(sentence.strip()) > 15:
                        seeds.append(sentence.strip()[:100])
        
        return seeds
    
    def _filter_seed_works(self, seeds: List[str]) -> List[str]:
        """Фильтрация и нормализация seed works"""
        
        filtered = []
        seen = set()
        
        for seed in seeds:
            # Очистка
            seed = seed.strip()
            seed = re.sub(r'\s+', ' ', seed)  # Множественные пробелы
            
            # Фильтры
            if len(seed) < 10 or len(seed) > 200:  # Длина
                continue
            if seed.lower() in seen:  # Дубликаты
                continue
            if re.match(r'^\d+$', seed):  # Только цифры
                continue
            if len(seed.split()) < 3:  # Минимум 3 слова
                continue
            
            seen.add(seed.lower())
            filtered.append(seed)
        
        # Ограничиваем количество (20-40 как в пайплайне)
        return filtered[:40]
    
    def _stage7_sbert_markup(self, content: str, seed_works: List[str], 
                            doc_type_info: Dict, structural_data: Dict) -> Dict[str, Any]:
        """
        STAGE 7: SBERT Markup (ПОЛНАЯ структура + граф)
        
        Использует SBERT для создания полной структуры и графа работ
        """
        
        logger.info(f"[Stage 7/14] SBERT MARKUP - Processing {len(seed_works)} seeds")
        start_time = time.time()
        
        if not self.sbert_model or not HAS_ML_LIBS:
            logger.warning("SBERT not available, using fallback")
            return self._sbert_markup_fallback(seed_works, structural_data)
        
        try:
            # Создаем эмбеддинги для seed works
            if seed_works:
                seed_embeddings = self.sbert_model.encode(seed_works)
            else:
                seed_embeddings = []
            
            # Анализируем связи между работами
            work_dependencies = self._analyze_work_dependencies(seed_works, seed_embeddings)
            
            # Создаем граф работ
            work_graph = self._build_work_graph(seed_works, work_dependencies)
            
            # Валидируем работы через SBERT
            validated_works = self._validate_works_with_sbert(seed_works, seed_embeddings, content)
            
            # Дополняем структуру из Stage 5
            enhanced_structure = self._enhance_structure_with_sbert(structural_data, validated_works)
            
            sbert_result = {
                'works': validated_works,
                'dependencies': work_dependencies,
                'work_graph': work_graph,
                'enhanced_structure': enhanced_structure,
                'embeddings_count': len(seed_embeddings) if seed_embeddings is not None else 0,
                'analysis_method': 'sbert'
            }
            
        except Exception as e:
            logger.error(f"SBERT markup failed: {e}")
            sbert_result = self._sbert_markup_fallback(seed_works, structural_data)
        
        elapsed = time.time() - start_time
        works_count = len(sbert_result.get('works', []))
        deps_count = len(sbert_result.get('dependencies', []))
        
        logger.info(f"[Stage 7/14] COMPLETE - Works: {works_count}, "
                   f"Dependencies: {deps_count} ({elapsed:.2f}s)")
        
        return sbert_result
    
    def _sbert_markup_fallback(self, seed_works: List[str], structural_data: Dict) -> Dict[str, Any]:
        """Fallback когда SBERT недоступен"""
        
        # Простая обработка без машинного обучения
        validated_works = []
        for i, work in enumerate(seed_works):
            validated_works.append({
                'id': f"work_{i}",
                'name': work,
                'confidence': 0.5,
                'type': 'generic',
                'section': 'unknown'
            })
        
        # Простые зависимости (последовательные)
        dependencies = []
        for i in range(len(validated_works) - 1):
            dependencies.append({
                'from': f"work_{i}",
                'to': f"work_{i+1}",
                'type': 'sequence',
                'confidence': 0.3
            })
        
        return {
            'works': validated_works,
            'dependencies': dependencies,
            'work_graph': {'nodes': validated_works, 'edges': dependencies},
            'enhanced_structure': structural_data,
            'analysis_method': 'fallback'
        }
    
    def _analyze_work_dependencies(self, works: List[str], embeddings) -> List[Dict]:
        """Анализ зависимостей между работами через SBERT"""
        
        if not works or embeddings is None or len(embeddings) == 0:
            return []
        
        dependencies = []
        
        try:
            from numpy import dot
            from numpy.linalg import norm
            
            # Ключевые слова для определения типов зависимостей
            sequence_keywords = ['после', 'затем', 'далее', 'следующий', 'этап']
            prerequisite_keywords = ['требует', 'необходимо', 'перед', 'до']
            
            for i, work1 in enumerate(works):
                for j, work2 in enumerate(works):
                    if i >= j:  # Избегаем дубликатов и самосравнения
                        continue
                    
                    # Семантическое сходство
                    similarity = dot(embeddings[i], embeddings[j]) / (
                        norm(embeddings[i]) * norm(embeddings[j])
                    )
                    
                    # Если сходство высокое, анализируем тип связи
                    if similarity > 0.7:
                        dep_type = 'related'
                        confidence = float(similarity)
                        
                        # Определяем тип зависимости по ключевым словам
                        work1_lower = work1.lower()
                        work2_lower = work2.lower()
                        
                        if any(kw in work1_lower for kw in sequence_keywords):
                            dep_type = 'sequence'
                        elif any(kw in work1_lower for kw in prerequisite_keywords):
                            dep_type = 'prerequisite'
                        
                        dependencies.append({
                            'from': f"work_{i}",
                            'to': f"work_{j}",
                            'type': dep_type,
                            'confidence': confidence,
                            'similarity': float(similarity)
                        })
            
        except Exception as e:
            logger.warning(f"Dependency analysis failed: {e}")
        
        return dependencies
    
    def _build_work_graph(self, works: List[str], dependencies: List[Dict]) -> Dict:
        """Построение графа работ"""
        
        nodes = []
        for i, work in enumerate(works):
            nodes.append({
                'id': f"work_{i}",
                'label': work[:50] + ('...' if len(work) > 50 else ''),
                'full_text': work,
                'type': 'work'
            })
        
        edges = []
        for dep in dependencies:
            edges.append({
                'from': dep['from'],
                'to': dep['to'],
                'label': dep['type'],
                'weight': dep['confidence']
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'nodes_count': len(nodes),
                'edges_count': len(edges),
                'avg_connectivity': len(edges) / max(len(nodes), 1)
            }
        }
    
    def _validate_works_with_sbert(self, works: List[str], embeddings, content: str) -> List[Dict]:
        """Валидация работ с помощью SBERT"""
        
        validated = []
        
        # Создаем эмбеддинг для всего контента (sample)
        content_sample = ' '.join(content.split()[:300])  # Первые 300 слов
        
        try:
            if self.sbert_model:
                content_embedding = self.sbert_model.encode([content_sample])[0]
            else:
                content_embedding = None
        except:
            content_embedding = None
        
        for i, work in enumerate(works):
            work_info = {
                'id': f"work_{i}",
                'name': work,
                'confidence': 0.5,
                'type': 'generic',
                'section': 'unknown',
                'relevance': 0.5
            }
            
            # Если есть эмбеддинги, вычисляем релевантность
            if embeddings is not None and content_embedding is not None and i < len(embeddings):
                try:
                    from numpy import dot
                    from numpy.linalg import norm
                    
                    relevance = dot(embeddings[i], content_embedding) / (
                        norm(embeddings[i]) * norm(content_embedding)
                    )
                    work_info['relevance'] = float(relevance)
                    work_info['confidence'] = min(float(relevance) + 0.3, 1.0)
                    
                except:
                    pass
            
            # Определяем тип работы
            work_lower = work.lower()
            if any(word in work_lower for word in ['монтаж', 'установка', 'сборка']):
                work_info['type'] = 'assembly'
            elif any(word in work_lower for word in ['бетонирование', 'заливка']):
                work_info['type'] = 'concrete'
            elif any(word in work_lower for word in ['контроль', 'проверка', 'испытание']):
                work_info['type'] = 'control'
            elif any(word in work_lower for word in ['подготовка', 'разметка']):
                work_info['type'] = 'preparation'
            
            validated.append(work_info)
        
        return validated
    
    def _enhance_structure_with_sbert(self, structural_data: Dict, works: List[Dict]) -> Dict:
        """Дополнение структуры информацией из SBERT анализа"""
        
        enhanced = structural_data.copy()
        
        # Добавляем информацию о работах в секции
        if 'sections' in enhanced:
            for section in enhanced['sections']:
                section['related_works'] = []
                
                # Ищем работы, относящиеся к этой секции
                section_text = section.get('content', '').lower()
                
                for work in works:
                    work_name = work['name'].lower()
                    
                    # Простая эвристика - если работа упоминается в секции
                    if any(word in section_text for word in work_name.split()[:3]):
                        section['related_works'].append(work['id'])
        
        # Добавляем общую статистику
        enhanced['sbert_analysis'] = {
            'total_works': len(works),
            'avg_confidence': sum(w['confidence'] for w in works) / max(len(works), 1),
            'work_types': list(set(w['type'] for w in works))
        }
        
        return enhanced
    
    def _stage8_metadata_extraction(self, content: str, structural_data: Dict, 
                                    doc_type_info: Dict) -> DocumentMetadata:
        """
        STAGE 8: Metadata Extraction (ТОЛЬКО из структуры Stage 5)
        
        Извлекает метаданные используя ТОЛЬКО структуру из Stage 5
        """
        
        logger.info(f"[Stage 8/14] METADATA EXTRACTION - Type: {doc_type_info['doc_type']}")
        start_time = time.time()
        
        metadata = DocumentMetadata()
        
        # Извлекаем метаданные из структуры (НЕ из сырого текста)
        if 'sections' in structural_data:
            metadata = self._extract_from_sections(structural_data['sections'], metadata)
        
        if 'tables' in structural_data:
            metadata = self._extract_from_tables(structural_data['tables'], metadata)
        
        # Специфичная обработка по типу документа
        if doc_type_info['doc_type'] == 'norms' and 'norm_elements' in structural_data:
            metadata = self._extract_norms_metadata(structural_data['norm_elements'], metadata)
        elif doc_type_info['doc_type'] == 'smeta' and 'smeta_items' in structural_data:
            metadata = self._extract_smeta_metadata(structural_data['smeta_items'], metadata)
        elif doc_type_info['doc_type'] == 'ppr' and 'ppr_stages' in structural_data:
            metadata = self._extract_ppr_metadata(structural_data['ppr_stages'], metadata)
        
        # Оценка качества извлечения
        metadata.quality_score = self._calculate_metadata_quality(metadata)
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 8/14] COMPLETE - Materials: {len(metadata.materials)}, "
                   f"Finances: {len(metadata.finances)}, Dates: {len(metadata.dates)}, "
                   f"Quality: {metadata.quality_score:.2f} ({elapsed:.2f}s)")
        
        return metadata
    
    def _extract_from_sections(self, sections: List[Dict], metadata: DocumentMetadata) -> DocumentMetadata:
        """Извлечение метаданных из секций структуры"""
        
        for section in sections:
            content = section.get('content', '')
            
            # Материалы из секций
            material_patterns = [
                r'бетон\s+[БМ]?\s*\d+',
                r'арматура\s+[А-Я]\s*\d+',
                r'сталь\s+\d+',
                r'кирпич\s+[А-Я]?\d*',
                r'цемент\s+[М]\s*\d+'
            ]
            
            for pattern in material_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                metadata.materials.extend([match.strip() for match in matches])
            
            # Даты из заголовков секций (приоритет заголовкам)
            title = section.get('title', '')
            date_patterns = [
                r'\d{1,2}[.\/-]\d{1,2}[.\/-]\d{2,4}',
                r'\d{4}[.\/-]\d{1,2}[.\/-]\d{1,2}'
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, title + ' ' + content)
                metadata.dates.extend([match for match in matches])
            
            # Номера документов (приоритет заголовкам)
            doc_patterns = [
                r'ГОСТ\s+\d+[.\-]\d+[.\-]\d+',
                r'СП\s+\d+[.\-]\d+[.\-]\d+',
                r'СНиП\s+\d+[.\-]\d+[.\-]\d+'
            ]
            
            for pattern in doc_patterns:
                matches = re.findall(pattern, title + ' ' + content, re.IGNORECASE)
                metadata.doc_numbers.extend([match for match in matches])
        
        return metadata
    
    def _extract_from_tables(self, tables: List[Dict], metadata: DocumentMetadata) -> DocumentMetadata:
        """Извлечение метаданных из таблиц структуры"""
        
        for table in tables:
            table_content = table.get('content', '')
            
            # Финансы ТОЛЬКО из таблиц (как указано в пайплайне)
            finance_patterns = [
                r'\d+[,.]?\d*\s*руб',
                r'стоимость[:\s]+\d+[,.]?\d*',
                r'цена[:\s]+\d+[,.]?\d*',
                r'\d+[,.]?\d*\s*тыс[.\s]*руб'
            ]
            
            for pattern in finance_patterns:
                matches = re.findall(pattern, table_content, re.IGNORECASE)
                metadata.finances.extend([match.strip() for match in matches])
            
            # Дополнительные материалы из таблиц
            table_materials = re.findall(r'[А-ЯЁа-яё]+\s+[БМА]\s*\d+', table_content)
            metadata.materials.extend([mat.strip() for mat in table_materials])
        
        return metadata
    
    def _extract_norms_metadata(self, norm_elements: List[Dict], metadata: DocumentMetadata) -> DocumentMetadata:
        """Специфичное извлечение для нормативных документов"""
        
        for element in norm_elements:
            if element['type'] == 'punkt':
                text = element['text']
                
                # Технические требования
                if 'требования' in text.lower():
                    tech_requirements = re.findall(r'[А-ЯЁа-яё\s]+требования?[А-ЯЁа-яё\s]*', text, re.IGNORECASE)
                    metadata.materials.extend([req[:50] for req in tech_requirements])
                
                # Ссылки на другие документы
                doc_refs = re.findall(r'согласно\s+[А-ЯЁ]+\s+\d+[.\-\d]*', text, re.IGNORECASE)
                metadata.doc_numbers.extend(doc_refs)
        
        return metadata
    
    def _extract_smeta_metadata(self, smeta_items: List[Dict], metadata: DocumentMetadata) -> DocumentMetadata:
        """Специфичное извлечение для смет"""
        
        total_sum = 0.0
        
        for item in smeta_items:
            # Суммы из позиций сметы
            try:
                item_sum = float(item.get('sum', '0').replace(',', '.'))
                total_sum += item_sum
            except:
                pass
            
            # Описания работ как материалы
            description = item.get('description', '')
            if len(description) > 10:
                metadata.materials.append(description[:100])
        
        # Общая стоимость
        if total_sum > 0:
            metadata.finances.append(f"Общая стоимость: {total_sum:.2f}")
        
        return metadata
    
    def _extract_ppr_metadata(self, ppr_stages: List[Dict], metadata: DocumentMetadata) -> DocumentMetadata:
        """Специфичное извлечение для ППР"""
        
        for stage in ppr_stages:
            description = stage.get('description', '')
            
            # Операции как материалы
            if len(description) > 15:
                metadata.materials.append(f"Операция: {description[:80]}")
            
            # Временные характеристики
            time_refs = re.findall(r'\d+\s*(?:дн|час|мин)', description, re.IGNORECASE)
            metadata.dates.extend(time_refs)
        
        return metadata
    
    def _calculate_metadata_quality(self, metadata: DocumentMetadata) -> float:
        """Расчет качества извлеченных метаданных"""
        
        score = 0.0
        
        # Бонусы за найденные элементы
        if metadata.materials:
            score += min(len(metadata.materials) / 10.0, 0.4)  # Максимум 0.4 за материалы
        
        if metadata.finances:
            score += min(len(metadata.finances) / 5.0, 0.3)   # Максимум 0.3 за финансы
        
        if metadata.dates:
            score += min(len(metadata.dates) / 3.0, 0.2)      # Максимум 0.2 за даты
        
        if metadata.doc_numbers:
            score += min(len(metadata.doc_numbers) / 3.0, 0.1) # Максимум 0.1 за номера
        
        return min(score, 1.0)
    
    def _stage9_quality_control(self, content: str, doc_type_info: Dict, 
                               structural_data: Dict, sbert_data: Dict, 
                               metadata: DocumentMetadata) -> Dict[str, Any]:
        """
        STAGE 9: Quality Control
        
        Контроль качества обработанных данных
        """
        
        logger.info(f"[Stage 9/14] QUALITY CONTROL")
        start_time = time.time()
        
        issues = []
        recommendations = []
        quality_score = 100.0
        
        # Проверка согласованности
        if doc_type_info['confidence'] < 0.7:
            issues.append(f"Low document type confidence: {doc_type_info['confidence']:.2f}")
            quality_score -= 15
        
        # Проверка структуры
        sections_count = len(structural_data.get('sections', []))
        if sections_count < 2:
            issues.append(f"Too few sections found: {sections_count}")
            quality_score -= 20
            recommendations.append("Consider manual section markup")
        
        # Проверка работ
        works_count = len(sbert_data.get('works', []))
        if works_count < 3:
            issues.append(f"Too few works extracted: {works_count}")
            quality_score -= 10
            recommendations.append("Review seed extraction patterns")
        
        # Проверка метаданных
        if metadata.quality_score < 0.3:
            issues.append(f"Low metadata quality: {metadata.quality_score:.2f}")
            quality_score -= 15
        
        # Проверка зависимостей
        deps_count = len(sbert_data.get('dependencies', []))
        if deps_count == 0 and works_count > 1:
            issues.append("No work dependencies found")
            quality_score -= 5
            recommendations.append("Check dependency extraction logic")
        
        quality_score = max(quality_score, 0.0)
        
        result = {
            'quality_score': quality_score,
            'issues': issues,
            'recommendations': recommendations,
            'stats': {
                'doc_type_confidence': doc_type_info['confidence'],
                'sections_count': sections_count,
                'works_count': works_count,
                'dependencies_count': deps_count,
                'metadata_quality': metadata.quality_score
            }
        }
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 9/14] COMPLETE - Quality Score: {quality_score:.1f}, "
                   f"Issues: {len(issues)} ({elapsed:.2f}s)")
        
        return result
    
    def _stage10_type_specific_processing(self, content: str, doc_type_info: Dict,
                                         structural_data: Dict, sbert_data: Dict) -> Dict[str, Any]:
        """
        STAGE 10: Type-specific Processing
        
        Обработка с учетом типа документа
        """
        
        logger.info(f"[Stage 10/14] TYPE-SPECIFIC PROCESSING - Type: {doc_type_info['doc_type']}")
        start_time = time.time()
        
        doc_type = doc_type_info['doc_type']
        result = {}
        
        if doc_type == 'norms':
            result = self._process_norms_specific(content, structural_data, sbert_data)
        elif doc_type == 'ppr':
            result = self._process_ppr_specific(content, structural_data, sbert_data)
        elif doc_type == 'smeta':
            result = self._process_smeta_specific(content, structural_data, sbert_data)
        else:
            result = self._process_generic_specific(content, structural_data, sbert_data)
        
        elapsed = time.time() - start_time
        processed_items = len(result.get('processed_items', []))
        
        logger.info(f"[Stage 10/14] COMPLETE - Processed {processed_items} type-specific items ({elapsed:.2f}s)")
        
        return result
    
    def _process_norms_specific(self, content: str, structural_data: Dict, sbert_data: Dict) -> Dict:
        """Специфичная обработка нормативных документов"""
        
        processed_items = []
        
        # Анализ требований
        if 'norm_elements' in structural_data:
            for element in structural_data['norm_elements']:
                if 'требования' in element['text'].lower():
                    processed_items.append({
                        'type': 'requirement',
                        'punkt': element['number'],
                        'text': element['text'][:200],
                        'level': element['level']
                    })
        
        # Связь с работами
        work_requirements = []
        for work in sbert_data.get('works', []):
            if any(word in work['name'].lower() for word in ['требует', 'должен', 'необходимо']):
                work_requirements.append({
                    'work_id': work['id'],
                    'requirement_type': 'mandatory',
                    'confidence': work['confidence']
                })
        
        return {
            'processed_items': processed_items,
            'work_requirements': work_requirements,
            'analysis_type': 'norms'
        }
    
    def _process_ppr_specific(self, content: str, structural_data: Dict, sbert_data: Dict) -> Dict:
        """Специфичная обработка ППР"""
        
        processed_items = []
        
        # Анализ технологических карт
        if 'ppr_stages' in structural_data:
            for stage in structural_data['ppr_stages']:
                processed_items.append({
                    'type': 'tech_card',
                    'stage': stage['number'],
                    'description': stage['description'][:200],
                    'complexity': len(stage['description'].split())  # Простая оценка сложности
                })
        
        # Временная последовательность работ
        work_sequence = []
        works = sbert_data.get('works', [])
        for i, work in enumerate(works):
            work_sequence.append({
                'order': i + 1,
                'work_id': work['id'],
                'estimated_duration': self._estimate_work_duration(work['name'])
            })
        
        return {
            'processed_items': processed_items,
            'work_sequence': work_sequence,
            'analysis_type': 'ppr'
        }
    
    def _process_smeta_specific(self, content: str, structural_data: Dict, sbert_data: Dict) -> Dict:
        """Специфичная обработка смет"""
        
        processed_items = []
        total_cost = 0.0
        
        # Анализ сметных позиций
        if 'smeta_items' in structural_data:
            for item in structural_data['smeta_items']:
                try:
                    cost = float(item.get('sum', '0').replace(',', '.'))
                    total_cost += cost
                except:
                    cost = 0.0
                
                processed_items.append({
                    'type': 'smeta_position',
                    'position': item['position'],
                    'description': item['description'][:150],
                    'cost': cost,
                    'quantity': item.get('quantity', '0')
                })
        
        # Связь работ со стоимостью
        work_costs = []
        for work in sbert_data.get('works', []):
            estimated_cost = self._estimate_work_cost(work['name'], total_cost, len(sbert_data.get('works', [])))
            work_costs.append({
                'work_id': work['id'],
                'estimated_cost': estimated_cost
            })
        
        return {
            'processed_items': processed_items,
            'total_cost': total_cost,
            'work_costs': work_costs,
            'analysis_type': 'smeta'
        }
    
    def _process_generic_specific(self, content: str, structural_data: Dict, sbert_data: Dict) -> Dict:
        """Общая обработка для неопределенных типов"""
        
        processed_items = []
        
        # Простой анализ секций
        for section in structural_data.get('sections', []):
            if len(section['content']) > 50:
                processed_items.append({
                    'type': 'section',
                    'title': section['title'][:100],
                    'length': len(section['content']),
                    'level': section.get('level', 1)
                })
        
        return {
            'processed_items': processed_items,
            'analysis_type': 'generic'
        }
    
    def _estimate_work_duration(self, work_name: str) -> float:
        """Простая оценка длительности работы"""
        
        work_lower = work_name.lower()
        
        if any(word in work_lower for word in ['подготовка', 'разметка']):
            return 1.0  # дни
        elif any(word in work_lower for word in ['монтаж', 'установка']):
            return 3.0
        elif any(word in work_lower for word in ['бетонирование']):
            return 2.0
        elif any(word in work_lower for word in ['контроль', 'проверка']):
            return 0.5
        else:
            return 1.5  # по умолчанию
    
    def _estimate_work_cost(self, work_name: str, total_cost: float, works_count: int) -> float:
        """Простая оценка стоимости работы"""
        
        if works_count == 0:
            return 0.0
        
        base_cost = total_cost / works_count
        work_lower = work_name.lower()
        
        # Коэффициенты сложности
        if any(word in work_lower for word in ['монтаж', 'установка']):
            return base_cost * 1.5
        elif any(word in work_lower for word in ['бетонирование']):
            return base_cost * 1.3
        elif any(word in work_lower for word in ['контроль']):
            return base_cost * 0.5
        else:
            return base_cost
    
    def _stage11_work_sequence_extraction(self, sbert_data: Dict, doc_type_info: Dict, 
                                         metadata: DocumentMetadata) -> List[WorkSequence]:
        """
        STAGE 11: Work Sequence Extraction
        
        Извлечение и усиление рабочих последовательностей
        """
        
        logger.info(f"[Stage 11/14] WORK SEQUENCE EXTRACTION")
        start_time = time.time()
        
        work_sequences = []
        works = sbert_data.get('works', [])
        dependencies = sbert_data.get('dependencies', [])
        
        # Создаем WorkSequence для каждой работы
        for work in works:
            # Найдем зависимости для этой работы
            work_deps = []
            for dep in dependencies:
                if dep['to'] == work['id']:
                    work_deps.append(dep['from'])
            
            # Определяем приоритет на основе типа и зависимостей
            priority = self._calculate_work_priority(work, work_deps, doc_type_info)
            
            # Оценка длительности
            duration = self._estimate_work_duration(work['name'])
            
            # Определение секции
            section = work.get('section', 'general')
            
            sequence = WorkSequence(
                name=work['name'],
                deps=work_deps,
                duration=duration,
                priority=priority,
                quality_score=work['confidence'],
                doc_type=doc_type_info['doc_type'],
                section=section
            )
            
            work_sequences.append(sequence)
        
        # Сортируем по приоритету
        work_sequences.sort(key=lambda x: x.priority, reverse=True)
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 11/14] COMPLETE - Created {len(work_sequences)} work sequences ({elapsed:.2f}s)")
        
        return work_sequences
    
    def _calculate_work_priority(self, work: Dict, dependencies: List[str], doc_type_info: Dict) -> int:
        """Расчет приоритета работы"""
        
        base_priority = 5
        
        # Бонус за тип работы
        work_name = work['name'].lower()
        if any(word in work_name for word in ['подготовка', 'планирование']):
            base_priority += 3  # Подготовительные работы приоритетнее
        elif any(word in work_name for word in ['контроль', 'проверка']):
            base_priority -= 2  # Контроль после основных работ
        
        # Бонус за уверенность
        base_priority += int(work['confidence'] * 3)
        
        # Штраф за количество зависимостей (много зависимостей = ниже приоритет)
        base_priority -= len(dependencies)
        
        # Бонус за тип документа
        if doc_type_info['doc_type'] == 'norms':
            base_priority += 2  # Нормативные документы важнее
        
        return max(base_priority, 1)
    
    def _stage12_save_work_sequences(self, work_sequences: List[WorkSequence], file_path: str) -> int:
        """
        STAGE 12: Save Work Sequences (Neo4j)
        
        Сохранение рабочих последовательностей в базу данных
        """
        
        logger.info(f"[Stage 12/14] SAVE WORK SEQUENCES")
        start_time = time.time()
        
        saved_count = 0
        
        # Сохранение в JSON (резервное)
        sequences_file = self.cache_dir / f"sequences_{Path(file_path).stem}.json"
        try:
            sequences_data = []
            for seq in work_sequences:
                sequences_data.append({
                    'name': seq.name,
                    'deps': seq.deps,
                    'duration': seq.duration,
                    'priority': seq.priority,
                    'quality_score': seq.quality_score,
                    'doc_type': seq.doc_type,
                    'section': seq.section
                })
            
            with open(sequences_file, 'w', encoding='utf-8') as f:
                json.dump(sequences_data, f, ensure_ascii=False, indent=2)
            
            saved_count = len(sequences_data)
            logger.info(f"Saved {saved_count} sequences to JSON: {sequences_file}")
            
        except Exception as e:
            logger.error(f"Failed to save sequences to JSON: {e}")
        
        # Сохранение в Neo4j (если доступен)
        if self.neo4j:
            try:
                neo4j_saved = self._save_sequences_to_neo4j(work_sequences, file_path)
                logger.info(f"Saved {neo4j_saved} sequences to Neo4j")
            except Exception as e:
                logger.warning(f"Failed to save to Neo4j: {e}")
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 12/14] COMPLETE - Saved {saved_count} sequences ({elapsed:.2f}s)")
        
        return saved_count
    
    def _save_sequences_to_neo4j(self, sequences: List[WorkSequence], file_path: str) -> int:
        """Сохранение последовательностей в Neo4j"""
        
        if not self.neo4j:
            return 0
        
        saved_count = 0
        
        try:
            with self.neo4j.session() as session:
                # Создаем узел документа
                doc_result = session.run("""
                    MERGE (d:Document {path: $path})
                    SET d.processed_at = datetime()
                    RETURN d
                """, path=file_path)
                
                # Создаем узлы работ
                for seq in sequences:
                    work_result = session.run("""
                        CREATE (w:Work {
                            name: $name,
                            duration: $duration,
                            priority: $priority,
                            quality_score: $quality_score,
                            doc_type: $doc_type,
                            section: $section
                        })
                        WITH w
                        MATCH (d:Document {path: $doc_path})
                        CREATE (d)-[:CONTAINS]->(w)
                        RETURN w
                    """, 
                    name=seq.name,
                    duration=seq.duration,
                    priority=seq.priority,
                    quality_score=seq.quality_score,
                    doc_type=seq.doc_type,
                    section=seq.section,
                    doc_path=file_path
                    )
                    
                    saved_count += 1
                
                # Создаем связи зависимостей
                for seq in sequences:
                    for dep_id in seq.deps:
                        try:
                            session.run("""
                                MATCH (w1:Work {name: $dep_name})
                                MATCH (w2:Work {name: $work_name})
                                CREATE (w1)-[:PRECEDES]->(w2)
                            """, dep_name=dep_id, work_name=seq.name)
                        except:
                            pass  # Зависимость может не существовать
            
        except Exception as e:
            logger.error(f"Neo4j save error: {e}")
            saved_count = 0
        
        return saved_count
    
    def _stage13_smart_chunking(self, content: str, structural_data: Dict, 
                               metadata: DocumentMetadata, doc_type_info: Dict) -> List[DocumentChunk]:
        """
        STAGE 13: Smart Chunking (1 пункт = 1 чанк)
        
        Разбиение документа на фрагменты с учетом структуры
        """
        
        logger.info(f"[Stage 13/14] SMART CHUNKING - 1 section = 1 chunk")
        start_time = time.time()
        
        chunks = []
        
        # Создаем чанки из секций (основной принцип: 1 пункт = 1 чанк)
        for i, section in enumerate(structural_data.get('sections', [])):
            if not section.get('content') or len(section['content'].strip()) < 20:
                continue
            
            chunk_metadata = {
                'section_id': f"section_{i}",
                'section_title': section.get('title', f'Секция {i+1}'),
                'section_level': section.get('level', 1),
                'doc_type': doc_type_info['doc_type'],
                'doc_subtype': doc_type_info['doc_subtype'],
                'confidence': doc_type_info['confidence'],
                'start_line': section.get('start_line', 0),
                'end_line': section.get('end_line', 0)
            }
            
            # Добавляем метаданные документа
            if metadata.materials:
                chunk_metadata['materials'] = metadata.materials[:5]  # Первые 5 материалов
            if metadata.dates:
                chunk_metadata['dates'] = metadata.dates[:3]  # Первые 3 даты
            
            chunk = DocumentChunk(
                content=section['content'].strip(),
                metadata=chunk_metadata,
                section_id=f"section_{i}",
                chunk_type="section"
            )
            
            chunks.append(chunk)
        
        # Создаем отдельные чанки из таблиц
        for i, table in enumerate(structural_data.get('tables', [])):
            if not table.get('content') or len(table['content'].strip()) < 10:
                continue
            
            table_metadata = {
                'table_id': f"table_{i}",
                'table_title': table.get('title', f'Таблица {i+1}'),
                'doc_type': doc_type_info['doc_type'],
                'chunk_type': 'table'
            }
            
            # Финансовые данные из таблиц
            if metadata.finances:
                table_metadata['finances'] = metadata.finances
            
            chunk = DocumentChunk(
                content=table['content'].strip(),
                metadata=table_metadata,
                section_id=f"table_{i}",
                chunk_type="table"
            )
            
            chunks.append(chunk)
        
        # Если секций мало, делим контент на логические части
        if len(chunks) < 3:
            additional_chunks = self._create_fallback_chunks(content, doc_type_info, metadata)
            chunks.extend(additional_chunks)
        
        # Генерируем эмбеддинги для чанков
        chunks_with_embeddings = self._generate_chunk_embeddings(chunks)
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 13/14] COMPLETE - Created {len(chunks_with_embeddings)} chunks ({elapsed:.2f}s)")
        
        return chunks_with_embeddings
    
    def _create_fallback_chunks(self, content: str, doc_type_info: Dict, 
                               metadata: DocumentMetadata) -> List[DocumentChunk]:
        """Создание чанков при недостаточной структуре"""
        
        chunks = []
        
        # Делим по абзацам
        paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]
        
        # Группируем абзацы в чанки по ~400 слов
        current_chunk_content = ""
        current_chunk_words = 0
        chunk_counter = 0
        
        for paragraph in paragraphs:
            paragraph_words = len(paragraph.split())
            
            if current_chunk_words + paragraph_words > 400 and current_chunk_content:
                # Создаем чанк
                chunk_metadata = {
                    'fallback_chunk_id': f"fallback_{chunk_counter}",
                    'doc_type': doc_type_info['doc_type'],
                    'word_count': current_chunk_words
                }
                
                chunk = DocumentChunk(
                    content=current_chunk_content.strip(),
                    metadata=chunk_metadata,
                    section_id=f"fallback_{chunk_counter}",
                    chunk_type="paragraph"
                )
                
                chunks.append(chunk)
                
                # Начинаем новый чанк
                current_chunk_content = paragraph + "\n\n"
                current_chunk_words = paragraph_words
                chunk_counter += 1
            else:
                current_chunk_content += paragraph + "\n\n"
                current_chunk_words += paragraph_words
        
        # Добавляем последний чанк
        if current_chunk_content.strip():
            chunk_metadata = {
                'fallback_chunk_id': f"fallback_{chunk_counter}",
                'doc_type': doc_type_info['doc_type'],
                'word_count': current_chunk_words
            }
            
            chunk = DocumentChunk(
                content=current_chunk_content.strip(),
                metadata=chunk_metadata,
                section_id=f"fallback_{chunk_counter}",
                chunk_type="paragraph"
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _generate_chunk_embeddings(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Генерация эмбеддингов для чанков"""
        
        if not self.sbert_model or not HAS_ML_LIBS:
            logger.warning("SBERT not available - chunks without embeddings")
            return chunks
        
        try:
            # Собираем тексты для обработки
            chunk_texts = [chunk.content for chunk in chunks]
            
            # Генерируем эмбеддинги батчами
            batch_size = 10
            for i in range(0, len(chunk_texts), batch_size):
                batch_texts = chunk_texts[i:i+batch_size]
                batch_embeddings = self.sbert_model.encode(batch_texts)
                
                # Присваиваем эмбеддинги чанкам
                for j, embedding in enumerate(batch_embeddings):
                    if i+j < len(chunks):
                        chunks[i+j].embedding = embedding.tolist()
            
            logger.info(f"Generated embeddings for {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
        
        return chunks
    
    def _stage14_save_to_qdrant(self, chunks: List[DocumentChunk], file_path: str, file_hash: str) -> int:
        """
        STAGE 14: Save to Qdrant
        
        Сохранение фрагментов в Qdrant
        """
        
        logger.info(f"[Stage 14/14] SAVE TO QDRANT")
        start_time = time.time()
        
        if not self.qdrant:
            logger.warning("Qdrant not available - saving to JSON fallback")
            return self._save_chunks_to_json(chunks, file_path, file_hash)
        
        saved_count = 0
        
        try:
            # Подготавливаем данные для Qdrant
            points = []
            
            for i, chunk in enumerate(chunks):
                if not chunk.embedding:
                    continue  # Пропускаем чанки без эмбеддингов
                
                # Метаданные для Qdrant
                payload = {
                    'file_path': file_path,
                    'file_hash': file_hash,
                    'chunk_id': f"{file_hash}_{i}",
                    'section_id': chunk.section_id,
                    'chunk_type': chunk.chunk_type,
                    'content': chunk.content,
                    'content_length': len(chunk.content),
                    'word_count': len(chunk.content.split()),
                    'processed_at': datetime.now().isoformat()
                }
                
                # Добавляем метаданные чанка
                payload.update(chunk.metadata)
                
                # Создаем точку для Qdrant
                point = models.PointStruct(
                    id=hash(f"{file_hash}_{i}") % (2**63),  # Создаем уникальный ID
                    vector=chunk.embedding,
                    payload=payload
                )
                
                points.append(point)
            
            # Сохраняем батчами
            batch_size = 50
            for i in range(0, len(points), batch_size):
                batch_points = points[i:i+batch_size]
                
                self.qdrant.upsert(
                    collection_name="bldr_docs",
                    points=batch_points
                )
                
                saved_count += len(batch_points)
                logger.info(f"Saved batch {i//batch_size + 1}: {len(batch_points)} chunks")
            
        except Exception as e:
            logger.error(f"Qdrant save failed: {e}")
            # Fallback to JSON
            saved_count = self._save_chunks_to_json(chunks, file_path, file_hash)
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 14/14] COMPLETE - Saved {saved_count} chunks ({elapsed:.2f}s)")
        
        return saved_count
    
    def _save_chunks_to_json(self, chunks: List[DocumentChunk], file_path: str, file_hash: str) -> int:
        """Fallback сохранение в JSON"""
        
        try:
            chunks_file = self.cache_dir / f"chunks_{Path(file_path).stem}.json"
            chunks_data = []
            
            for i, chunk in enumerate(chunks):
                chunk_data = {
                    'id': f"{file_hash}_{i}",
                    'content': chunk.content,
                    'metadata': chunk.metadata,
                    'section_id': chunk.section_id,
                    'chunk_type': chunk.chunk_type,
                    'has_embedding': chunk.embedding is not None,
                    'embedding_length': len(chunk.embedding) if chunk.embedding else 0
                }
                chunks_data.append(chunk_data)
            
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(chunks_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Fallback: Saved {len(chunks_data)} chunks to JSON")
            return len(chunks_data)
            
        except Exception as e:
            logger.error(f"JSON fallback save failed: {e}")
            return 0
    
    def _update_processed_files(self, file_path: str, file_hash: str, info: Dict):
        """Обновление списка обработанных файлов"""
        
        try:
            self.processed_files[file_hash] = {
                'file_path': file_path,
                'file_hash': file_hash,
                **info
            }
            
            with open(self.processed_files_json, 'w', encoding='utf-8') as f:
                json.dump(self.processed_files, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to update processed files: {e}")
    
    def _generate_final_report(self, total_time: float):
        """Генерация финального отчета"""
        
        logger.info("=== GENERATING FINAL REPORT ===")
        
        report = {
            'training_summary': {
                'start_time': datetime.fromtimestamp(self.stats['start_time']).isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_time_seconds': total_time,
                'total_time_formatted': f"{total_time:.2f} seconds",
                'files_found': self.stats['files_found'],
                'files_processed': self.stats['files_processed'],
                'files_failed': self.stats['files_failed'],
                'success_rate': (self.stats['files_processed'] / max(self.stats['files_found'], 1)) * 100,
                'total_chunks': self.stats['total_chunks'],
                'total_works': self.stats['total_works'],
                'avg_chunks_per_file': self.stats['total_chunks'] / max(self.stats['files_processed'], 1),
                'avg_works_per_file': self.stats['total_works'] / max(self.stats['files_processed'], 1)
            },
            'system_info': {
                'sbert_available': self.sbert_model is not None,
                'qdrant_available': self.qdrant is not None,
                'neo4j_available': self.neo4j is not None,
                'base_directory': str(self.base_dir),
                'processed_files_count': len(self.processed_files)
            },
            'performance_metrics': {
                'avg_processing_time_per_file': total_time / max(self.stats['files_found'], 1),
                'files_per_minute': (self.stats['files_processed'] / (total_time / 60)) if total_time > 60 else 0
            }
        }
        
        # Сохраняем отчет
        report_file = self.reports_dir / f"training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Final report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
        
        # Выводим итоговую статистику
        logger.info("=== TRAINING COMPLETED ===")
        logger.info(f"Files processed: {self.stats['files_processed']}/{self.stats['files_found']}")
        logger.info(f"Success rate: {report['training_summary']['success_rate']:.1f}%")
        logger.info(f"Total chunks: {self.stats['total_chunks']}")
        logger.info(f"Total works: {self.stats['total_works']}")
        logger.info(f"Processing time: {total_time:.2f} seconds")
        logger.info(f"Avg time per file: {report['performance_metrics']['avg_processing_time_per_file']:.2f}s")
        
        return report

# =================================================================
# UTILITY FUNCTIONS
# =================================================================

def start_fixed_training(base_dir: str = None, max_files: Optional[int] = None):
    """
    Запуск исправленного RAG тренера
    
    Args:
        base_dir: Базовая директория с документами
        max_files: Максимальное количество файлов для обработки
    """
    
    print("=== STARTING FIXED ENHANCED RAG TRAINER ===")
    print("All stages corrected according to ideal pipeline!")
    print("Rubern replaced with SBERT, emoji issues fixed")
    
    try:
        trainer = FixedEnhancedBldrRAGTrainer(base_dir=base_dir)
        trainer.train(max_files=max_files)
        
        print("=== TRAINING COMPLETED SUCCESSFULLY ===")
        
    except Exception as e:
        print(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    # Демонстрационный запуск
    print("FIXED ENHANCED BLDR RAG TRAINER V3 - READY TO ROCK!")
    print("All 15 stages corrected according to ideal pipeline")
    print("SBERT instead of Rubern, no emoji encoding issues")
    print()
    
    # Параметры
    BASE_DIR = os.getenv("BASE_DIR", "I:/docs")
    MAX_FILES = None  # Все файлы
    
    print(f"Base directory: {BASE_DIR}")
    print(f"Max files: {'ALL' if MAX_FILES is None else MAX_FILES}")
    print()
    
    response = input("Start training? (y/N): ").strip().lower()
    
    if response == 'y':
        start_fixed_training(BASE_DIR, MAX_FILES)
    else:
        print("Training cancelled.")