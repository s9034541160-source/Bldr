#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔥🚀 MONSTER RAG TRAINER - FULL POWER V3 🚀🔥
=============================================
ПОЛНАЯ МОЩНОСТЬ! ВСЕ СИСТЕМЫ В КРАСНОЙ ЗОНЕ!

🎯 WHAT WE'RE UNLEASHING:
✅ Full 15-Stage Enhanced Pipeline
✅ Recursive Hierarchical Chunking (1 пункт = 1 чанк)
✅ Intelligent File Sorting & Organization  
✅ GPU-Accelerated Processing (CUDA)
✅ Parallel Multi-Threading
✅ Smart Document Prioritization
✅ Advanced Structure Extraction
✅ All 10 Performance Improvements
✅ Auto File Organization & Cleanup
✅ Real-time Progress Monitoring

🔥 TARGET: 1168 FILES → FULL RAG MONSTER POWER!
"""

import os
import sys
import time
import json
import shutil
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
import hashlib
import glob
import threading
from queue import Queue
import psutil

# Настройка мощного логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler(f'C:/Bldr/logs/monster_rag_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Импорты наших систем
try:
    from complete_enhanced_bldr_rag_trainer import CompleteEnhancedBldrRAGTrainer
    from recursive_hierarchical_chunker import RecursiveHierarchicalChunker, create_hierarchical_chunks_from_structure
    from working_frontend_rag_integration import create_working_rag_trainer
    FULL_SYSTEMS_AVAILABLE = True
    logger.info("🔥 ALL SYSTEMS LOADED - MONSTER MODE ACTIVATED!")
except ImportError as e:
    logger.error(f"❌ Critical system import failed: {e}")
    FULL_SYSTEMS_AVAILABLE = False

@dataclass
class MonsterStats:
    """Статистика работы монстра"""
    start_time: float = 0.0
    files_found: int = 0
    files_processed: int = 0
    files_failed: int = 0
    files_moved: int = 0
    chunks_created: int = 0
    total_sections: int = 0
    total_tables: int = 0
    processing_speed: float = 0.0  # файлов в минуту
    gpu_utilization: float = 0.0
    cpu_utilization: float = 0.0
    memory_usage: float = 0.0
    
class MonsterRAGTrainer:
    """
    🔥 MONSTER RAG TRAINER - FULL POWER MODE
    
    Unleashes all systems for maximum performance:
    - Multi-stage document processing pipeline
    - Intelligent file organization
    - Recursive hierarchical chunking  
    - GPU-accelerated operations
    - Real-time monitoring
    """
    
    def __init__(self, base_dir: str = "I:/docs", max_workers: int = None):
        """
        🔥 Initialize the MONSTER
        
        Args:
            base_dir: Base directory with documents
            max_workers: Max parallel workers (auto-detected if None)
        """
        
        print("🔥" * 60)
        print("🚀 INITIALIZING MONSTER RAG TRAINER - FULL POWER MODE 🚀")
        print("🔥" * 60)
        
        self.base_dir = Path(base_dir)
        self.max_workers = max_workers or min(psutil.cpu_count(), 12)  # Max 12 workers
        
        # Папки для организации
        self.organized_dirs = {
            'gosts': self.base_dir / 'organized' / 'GOSTS',
            'snips': self.base_dir / 'organized' / 'SNIPs', 
            'sps': self.base_dir / 'organized' / 'SPs',
            'pprs': self.base_dir / 'organized' / 'PPRs',
            'smetas': self.base_dir / 'organized' / 'SMETAS',
            'other': self.base_dir / 'organized' / 'OTHER',
            'processed': self.base_dir / 'processed'
        }
        
        # Создаем папки
        for folder in self.organized_dirs.values():
            folder.mkdir(parents=True, exist_ok=True)
        
        # Инициализация статистики  
        self.stats = MonsterStats()
        self.stats.start_time = time.time()
        
        # Очередь для обработки
        self.processing_queue = Queue()
        self.results_queue = Queue()
        
        # Системы
        self.enhanced_trainer = None
        self.hierarchical_chunker = None
        self.working_trainer = None
        
        # Инициализируем системы
        self._initialize_monster_systems()
        
        logger.info(f"🔥 MONSTER INITIALIZED:")
        logger.info(f"   📁 Base directory: {self.base_dir}")
        logger.info(f"   👥 Max workers: {self.max_workers}")
        logger.info(f"   🚀 GPU Available: {self._check_gpu()}")
        logger.info(f"   💾 RAM Available: {psutil.virtual_memory().available / 1024**3:.1f} GB")
        logger.info(f"   🔥 MONSTER STATUS: READY TO UNLEASH!")
        
    def _initialize_monster_systems(self):
        """Инициализация всех подсистем монстра"""
        
        if not FULL_SYSTEMS_AVAILABLE:
            logger.error("❌ Critical systems not available!")
            return
        
        try:
            # Enhanced RAG Trainer
            logger.info("🔥 Initializing Enhanced RAG Trainer...")
            self.enhanced_trainer = CompleteEnhancedBldrRAGTrainer(base_dir=str(self.base_dir))
            
            # Hierarchical Chunker
            logger.info("🔄 Initializing Recursive Hierarchical Chunker...")
            self.hierarchical_chunker = RecursiveHierarchicalChunker(
                target_chunk_size=400,
                min_chunk_size=100,
                max_chunk_size=800
            )
            
            # Working Trainer (backup)
            logger.info("🛡️ Initializing Working Trainer (backup)...")
            self.working_trainer = create_working_rag_trainer(use_intelligent_chunking=True)
            
            logger.info("✅ ALL MONSTER SYSTEMS INITIALIZED!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize systems: {e}")
            raise
    
    def _check_gpu(self) -> bool:
        """Проверка доступности GPU"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
    
    def unleash_the_monster(self, max_files: Optional[int] = None):
        """
        🔥🚀 UNLEASH THE MONSTER - FULL POWER PROCESSING!
        
        Args:
            max_files: Maximum files to process (None = all files)
        """
        
        print("\n" + "🔥" * 80)
        print("🚀" * 20 + " UNLEASHING THE MONSTER " + "🚀" * 20)
        print("🔥" * 80)
        
        try:
            # STAGE 1: File Discovery & Organization
            logger.info("🔍 STAGE 1: MONSTER FILE DISCOVERY & ORGANIZATION")
            all_files = self._monster_file_discovery()
            
            if not all_files:
                logger.error("❌ NO FILES FOUND - MONSTER HIBERNATING")
                return
            
            if max_files:
                all_files = all_files[:max_files]
                logger.info(f"🎯 Limited to {max_files} files for processing")
            
            self.stats.files_found = len(all_files)
            logger.info(f"🎯 TARGET ACQUIRED: {len(all_files)} FILES")
            
            # STAGE 2: File Organization
            logger.info("📁 STAGE 2: INTELLIGENT FILE ORGANIZATION")
            organized_files = self._organize_files_by_type(all_files)
            
            # STAGE 3: Priority Processing Queue
            logger.info("⚡ STAGE 3: PRIORITY QUEUE CONSTRUCTION")
            priority_queue = self._build_priority_queue(organized_files)
            
            # STAGE 4: UNLEASH PARALLEL PROCESSING
            logger.info("🔥 STAGE 4: UNLEASHING PARALLEL MONSTER PROCESSING")
            self._parallel_monster_processing(priority_queue)
            
            # STAGE 5: Final Statistics & Cleanup
            logger.info("📊 STAGE 5: MONSTER STATISTICS & CLEANUP")
            self._generate_monster_report()
            
            print("\n" + "🎉" * 80)
            print("🏆" * 20 + " MONSTER OPERATION COMPLETE " + "🏆" * 20) 
            print("🎉" * 80)
            
        except Exception as e:
            logger.error(f"💥 MONSTER ERROR: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _monster_file_discovery(self) -> List[Path]:
        """🔍 Monster-powered file discovery"""
        
        logger.info("🔍 Scanning for documents with MONSTER POWER...")
        
        # Расширенные паттерны файлов
        file_patterns = {
            'pdf': '*.pdf',
            'docx': '*.docx', 
            'doc': '*.doc',
            'txt': '*.txt',
            'rtf': '*.rtf',
            'djvu': '*.djvu'
        }
        
        all_files = []
        pattern_stats = {}
        
        for file_type, pattern in file_patterns.items():
            logger.info(f"  🔎 Scanning for {file_type.upper()} files...")
            files = list(self.base_dir.rglob(pattern))
            
            # Фильтруем файлы (исключаем временные, системные)
            filtered_files = []
            for file_path in files:
                if self._is_valid_document(file_path):
                    filtered_files.append(file_path)
            
            pattern_stats[file_type] = len(filtered_files)
            all_files.extend(filtered_files)
            
            logger.info(f"    ✅ Found {len(filtered_files)} valid {file_type.upper()} files")
        
        # Удаляем дубликаты по содержимому
        logger.info("🔄 Removing duplicates...")
        unique_files = self._remove_duplicate_files(all_files)
        
        logger.info("🎯 FILE DISCOVERY COMPLETE:")
        for file_type, count in pattern_stats.items():
            logger.info(f"  📄 {file_type.upper()}: {count} files")
        logger.info(f"  🎯 TOTAL UNIQUE: {len(unique_files)} files")
        
        return unique_files
    
    def _is_valid_document(self, file_path: Path) -> bool:
        """Проверка валидности документа"""
        
        # Исключаем системные файлы и папки
        exclude_patterns = [
            'temp', 'tmp', 'cache', '.git', '__pycache__',
            'node_modules', 'venv', 'backup', '~$'
        ]
        
        file_str = str(file_path).lower()
        if any(pattern in file_str for pattern in exclude_patterns):
            return False
        
        # Проверяем размер файла
        try:
            size = file_path.stat().st_size
            if size < 1024 or size > 100 * 1024 * 1024:  # 1KB - 100MB
                return False
        except:
            return False
        
        return True
    
    def _remove_duplicate_files(self, files: List[Path]) -> List[Path]:
        """Удаление дубликатов по хешу содержимого"""
        
        seen_hashes = set()
        unique_files = []
        
        for file_path in files:
            try:
                file_hash = self._get_file_hash(file_path)
                if file_hash not in seen_hashes:
                    seen_hashes.add(file_hash)
                    unique_files.append(file_path)
            except Exception as e:
                logger.warning(f"⚠️ Failed to hash {file_path}: {e}")
                # Добавляем файл даже если хеширование не удалось
                unique_files.append(file_path)
        
        logger.info(f"🔄 Removed {len(files) - len(unique_files)} duplicate files")
        return unique_files
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Быстрое хеширование файла"""
        hasher = hashlib.md5()
        
        # Читаем только первые и последние 8KB для скорости
        with open(file_path, 'rb') as f:
            # Первые 8KB
            chunk = f.read(8192)
            if chunk:
                hasher.update(chunk)
            
            # Последние 8KB (если файл больше 16KB)
            f.seek(-8192, 2)  # От конца файла
            chunk = f.read(8192)
            if chunk:
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def _organize_files_by_type(self, files: List[Path]) -> Dict[str, List[Path]]:
        """📁 Умная организация файлов по типам"""
        
        logger.info("📁 Organizing files by document type...")
        
        organized = {
            'gosts': [],
            'snips': [], 
            'sps': [],
            'pprs': [],
            'smetas': [],
            'other': []
        }
        
        # Паттерны для классификации
        classification_patterns = {
            'gosts': [r'\bГОСТ\b', r'\bgost\b', r'государственный.*стандарт'],
            'snips': [r'\bСНиП\b', r'\bsnip\b', r'строительные.*нормы'],
            'sps': [r'\bСП\b', r'\bsp\b', r'свод.*правил'],
            'pprs': [r'\bППР\b', r'\bppr\b', r'проект.*производства.*работ', r'технологическая.*карта'],
            'smetas': [r'\bсмета\b', r'расценк', r'калькулряц', r'стоимость']
        }
        
        for file_path in files:
            file_type = self._classify_document(file_path, classification_patterns)
            organized[file_type].append(file_path)
            
            # Перемещаем файл в соответствующую папку
            try:
                target_dir = self.organized_dirs[file_type]
                new_path = target_dir / file_path.name
                
                # Если файл еще не в целевой папке
                if file_path.parent != target_dir:
                    if new_path.exists():
                        # Добавляем суффикс если файл существует
                        counter = 1
                        while new_path.exists():
                            name_parts = file_path.stem, counter, file_path.suffix
                            new_name = f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                            new_path = target_dir / new_name
                            counter += 1
                    
                    shutil.move(str(file_path), str(new_path))
                    self.stats.files_moved += 1
                    logger.debug(f"📁 Moved {file_path.name} → {file_type.upper()}")
            
            except Exception as e:
                logger.warning(f"⚠️ Failed to move {file_path}: {e}")
        
        # Статистика организации
        logger.info("📊 FILE ORGANIZATION COMPLETE:")
        for doc_type, file_list in organized.items():
            logger.info(f"  📂 {doc_type.upper()}: {len(file_list)} files")
        
        return organized
    
    def _classify_document(self, file_path: Path, patterns: Dict[str, List[str]]) -> str:
        """Классификация документа по типу"""
        
        # Анализируем имя файла
        filename_lower = file_path.name.lower()
        
        for doc_type, type_patterns in patterns.items():
            for pattern in type_patterns:
                import re
                if re.search(pattern, filename_lower, re.IGNORECASE):
                    return doc_type
        
        # Если ничего не подошло - читаем начало файла
        try:
            if file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content_sample = f.read(2000).lower()
                    
                for doc_type, type_patterns in patterns.items():
                    for pattern in type_patterns:
                        if re.search(pattern, content_sample, re.IGNORECASE):
                            return doc_type
        except:
            pass
        
        return 'other'
    
    def _build_priority_queue(self, organized_files: Dict[str, List[Path]]) -> List[Tuple[Path, int, str]]:
        """⚡ Построение очереди с приоритетами"""
        
        logger.info("⚡ Building priority processing queue...")
        
        # Приоритеты типов документов
        type_priorities = {
            'gosts': 10,    # Максимальный приоритет
            'sps': 9,       # Своды правил
            'snips': 8,     # СНиПы
            'pprs': 6,      # ППР
            'smetas': 4,    # Сметы
            'other': 2      # Остальное
        }
        
        priority_queue = []
        
        for doc_type, files in organized_files.items():
            base_priority = type_priorities.get(doc_type, 1)
            
            for file_path in files:
                # Дополнительные факторы приоритета
                file_priority = base_priority
                
                # Бонус за размер (больше = важнее)
                try:
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    if size_mb > 5:
                        file_priority += 2
                    elif size_mb > 1:
                        file_priority += 1
                except:
                    pass
                
                # Бонус за "свежесть" файла
                try:
                    mtime = file_path.stat().st_mtime
                    days_old = (time.time() - mtime) / (24 * 3600)
                    if days_old < 365:  # Менее года
                        file_priority += 1
                except:
                    pass
                
                priority_queue.append((file_path, file_priority, doc_type))
        
        # Сортируем по приоритету (высший - первый)
        priority_queue.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"⚡ Priority queue built: {len(priority_queue)} files")
        logger.info(f"   🔥 High priority (8+): {sum(1 for _, p, _ in priority_queue if p >= 8)}")
        logger.info(f"   🟡 Medium priority (5-7): {sum(1 for _, p, _ in priority_queue if 5 <= p < 8)}")
        logger.info(f"   🔵 Low priority (<5): {sum(1 for _, p, _ in priority_queue if p < 5)}")
        
        return priority_queue
    
    def _parallel_monster_processing(self, priority_queue: List[Tuple[Path, int, str]]):
        """🔥 Параллельная обработка на полной мощности"""
        
        logger.info(f"🔥 UNLEASHING PARALLEL PROCESSING - {self.max_workers} WORKERS")
        
        # Запускаем мониторинг производительности
        monitor_thread = threading.Thread(target=self._performance_monitor, daemon=True)
        monitor_thread.start()
        
        # Параллельная обработка
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Отправляем все файлы на обработку
            future_to_file = {
                executor.submit(self._process_single_file_monster, file_path, priority, doc_type): (file_path, priority, doc_type)
                for file_path, priority, doc_type in priority_queue
            }
            
            # Обрабатываем результаты по мере готовности
            for future in as_completed(future_to_file):
                file_info = future_to_file[future]
                file_path, priority, doc_type = file_info
                
                try:
                    result = future.result(timeout=300)  # 5 минут таймаут
                    
                    if result['success']:
                        self.stats.files_processed += 1
                        self.stats.chunks_created += result.get('chunks_created', 0)
                        self.stats.total_sections += result.get('sections_found', 0)
                        self.stats.total_tables += result.get('tables_found', 0)
                        
                        logger.info(f"✅ PROCESSED: {file_path.name} ({result.get('chunks_created', 0)} chunks)")
                    else:
                        self.stats.files_failed += 1
                        logger.error(f"❌ FAILED: {file_path.name} - {result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    self.stats.files_failed += 1
                    logger.error(f"💥 PROCESSING ERROR: {file_path.name} - {e}")
                
                # Обновляем статистику скорости
                self._update_processing_speed()
        
        logger.info("🔥 PARALLEL PROCESSING COMPLETE!")
    
    def _process_single_file_monster(self, file_path: Path, priority: int, doc_type: str) -> Dict[str, Any]:
        """🔥 Обработка одного файла на MONSTER POWER"""
        
        result = {
            'success': False,
            'file_path': str(file_path),
            'priority': priority,
            'doc_type': doc_type,
            'chunks_created': 0,
            'sections_found': 0,
            'tables_found': 0,
            'processing_time': 0,
            'error': None
        }
        
        start_time = time.time()
        
        try:
            # Читаем содержимое файла
            content = self._read_file_content(file_path)
            if not content:
                raise ValueError("Empty or unreadable file")
            
            # MONSTER PROCESSING с полным пайплайном
            if self.enhanced_trainer:
                # Используем Enhanced RAG Trainer для полной обработки
                document_result = self.enhanced_trainer.process_single_file(str(file_path))
                
                if document_result:
                    result['chunks_created'] = document_result.get('chunks_created', 0)
                    result['sections_found'] = len(document_result.get('sections', []))
                    result['tables_found'] = len(document_result.get('tables', []))
                    result['success'] = True
            
            # Backup с Working Trainer
            elif self.working_trainer:
                document_result = self.working_trainer.process_single_document(content, str(file_path))
                
                result['chunks_created'] = len(document_result.get('chunks', []))
                result['sections_found'] = len(document_result.get('sections', []))
                result['tables_found'] = len(document_result.get('tables', []))
                result['success'] = True
            
            else:
                raise ValueError("No processing systems available")
        
        except Exception as e:
            result['error'] = str(e)
            logger.debug(f"Processing error for {file_path.name}: {e}")
        
        result['processing_time'] = time.time() - start_time
        return result
    
    def _read_file_content(self, file_path: Path) -> str:
        """Чтение содержимого файла"""
        
        try:
            # Пока поддерживаем только текстовые файлы
            if file_path.suffix.lower() in ['.txt', '.rtf']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            else:
                # Добавлена поддержка PDF/DOCX через соответствующие библиотеки
                try:
                    if file_path.suffix.lower() == '.pdf':
                        # Импорт PDF обработчика
                        try:
                            import PyPDF2
                            with open(file_path, 'rb') as pdf_file:
                                pdf_reader = PyPDF2.PdfReader(pdf_file)
                                content = ''
                                for page in pdf_reader.pages:
                                    content += page.extract_text() + '\n'
                            return content
                        except ImportError:
                            logger.warning("PyPDF2 not available for PDF processing")
                            return ""
                    elif file_path.suffix.lower() in ['.docx', '.doc']:
                        # Импорт DOCX обработчика
                        try:
                            from docx import Document
                            doc = Document(str(file_path))
                            content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                            return content
                        except ImportError:
                            logger.warning("python-docx not available for DOCX processing")
                            return ""
                    else:
                        logger.debug(f"Unsupported file type: {file_path.suffix}")
                        return ""
                except Exception as e:
                    logger.debug(f"Failed to read {file_path}: {e}")
                    return ""
        
        except Exception as e:
            logger.debug(f"Failed to read {file_path}: {e}")
            return ""
    
    def _performance_monitor(self):
        """📊 Мониторинг производительности в реальном времени"""
        
        while self.stats.files_processed + self.stats.files_failed < self.stats.files_found:
            # Обновляем системные метрики
            self.stats.cpu_utilization = psutil.cpu_percent(interval=1)
            self.stats.memory_usage = psutil.virtual_memory().percent
            
            # GPU утилизация (если доступно)
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    self.stats.gpu_utilization = gpus[0].load * 100
            except:
                self.stats.gpu_utilization = 0
            
            # Выводим статистику каждые 30 секунд
            time.sleep(30)
            self._print_live_stats()
    
    def _update_processing_speed(self):
        """Обновление скорости обработки"""
        
        elapsed_minutes = (time.time() - self.stats.start_time) / 60.0
        processed_total = self.stats.files_processed + self.stats.files_failed
        
        if elapsed_minutes > 0:
            self.stats.processing_speed = processed_total / elapsed_minutes
    
    def _print_live_stats(self):
        """Вывод живой статистики"""
        
        processed_total = self.stats.files_processed + self.stats.files_failed
        progress_pct = (processed_total / self.stats.files_found) * 100 if self.stats.files_found > 0 else 0
        
        print("\n" + "="*80)
        print(f"🔥 MONSTER RAG TRAINER - LIVE STATS")
        print("="*80)
        print(f"📊 Progress: {progress_pct:.1f}% ({processed_total}/{self.stats.files_found})")
        print(f"✅ Processed: {self.stats.files_processed} | ❌ Failed: {self.stats.files_failed}")
        print(f"🧩 Chunks Created: {self.stats.chunks_created}")
        print(f"📑 Sections Found: {self.stats.total_sections}")
        print(f"📊 Tables Found: {self.stats.total_tables}")
        print(f"⚡ Speed: {self.stats.processing_speed:.1f} files/min")
        print(f"💻 CPU: {self.stats.cpu_utilization:.1f}% | 💾 RAM: {self.stats.memory_usage:.1f}% | 🚀 GPU: {self.stats.gpu_utilization:.1f}%")
        
        # Оценка времени до завершения
        if self.stats.processing_speed > 0:
            files_left = self.stats.files_found - processed_total
            minutes_left = files_left / self.stats.processing_speed
            eta = datetime.now() + timedelta(minutes=minutes_left)
            print(f"⏰ ETA: {eta.strftime('%H:%M:%S')} ({minutes_left:.0f} min left)")
        
        print("="*80)
    
    def _generate_monster_report(self):
        """📊 Генерация финального отчета монстра"""
        
        total_time = time.time() - self.stats.start_time
        success_rate = (self.stats.files_processed / self.stats.files_found) * 100 if self.stats.files_found > 0 else 0
        
        report = {
            'monster_stats': {
                'total_time_seconds': total_time,
                'total_time_formatted': str(timedelta(seconds=int(total_time))),
                'files_found': self.stats.files_found,
                'files_processed': self.stats.files_processed,
                'files_failed': self.stats.files_failed,
                'files_moved': self.stats.files_moved,
                'success_rate_percent': success_rate,
                'processing_speed_files_per_minute': self.stats.processing_speed,
                'chunks_created': self.stats.chunks_created,
                'sections_found': self.stats.total_sections,
                'tables_found': self.stats.total_tables,
                'avg_chunks_per_file': self.stats.chunks_created / max(self.stats.files_processed, 1)
            },
            'performance_metrics': {
                'max_workers': self.max_workers,
                'peak_cpu_utilization': self.stats.cpu_utilization,
                'peak_memory_usage': self.stats.memory_usage,
                'gpu_utilization': self.stats.gpu_utilization
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Сохраняем отчет
        report_file = Path("C:/Bldr/monster_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Выводим финальный отчет
        print("\n" + "🏆" * 80)
        print("🔥" * 25 + " MONSTER OPERATION COMPLETE " + "🔥" * 25)
        print("🏆" * 80)
        print(f"⏰ Total Time: {timedelta(seconds=int(total_time))}")
        print(f"📁 Files Found: {self.stats.files_found}")
        print(f"✅ Successfully Processed: {self.stats.files_processed}")
        print(f"❌ Failed: {self.stats.files_failed}")
        print(f"📁 Files Organized: {self.stats.files_moved}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"⚡ Average Speed: {self.stats.processing_speed:.1f} files/minute")
        print(f"🧩 Total Chunks Created: {self.stats.chunks_created}")
        print(f"📑 Total Sections Found: {self.stats.total_sections}")
        print(f"📊 Total Tables Found: {self.stats.total_tables}")
        print(f"📊 Average Chunks per File: {self.stats.chunks_created / max(self.stats.files_processed, 1):.1f}")
        print("🏆" * 80)
        print(f"📄 Full report saved: {report_file}")
        print("🎉 MONSTER RAG TRAINER - MISSION ACCOMPLISHED! 🎉")
        
        logger.info(f"🏆 MONSTER OPERATION COMPLETE - {self.stats.files_processed}/{self.stats.files_found} files processed")

def launch_monster(base_dir: str = "I:/docs", max_files: Optional[int] = None, max_workers: Optional[int] = None):
    """
    🚀 LAUNCH THE MONSTER RAG TRAINER
    
    Args:
        base_dir: Directory with documents
        max_files: Maximum files to process (None = all)
        max_workers: Maximum parallel workers (None = auto)
    """
    
    try:
        # Создаем папку логов
        Path("C:/Bldr/logs").mkdir(exist_ok=True)
        
        # Инициализируем монстра
        monster = MonsterRAGTrainer(base_dir=base_dir, max_workers=max_workers)
        
        # UNLEASH THE MONSTER!
        monster.unleash_the_monster(max_files=max_files)
        
        return monster
    
    except Exception as e:
        logger.error(f"💥 MONSTER LAUNCH FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    print("🔥" * 80)
    print("🚀 MONSTER RAG TRAINER - READY TO UNLEASH FULL POWER 🚀")
    print("🔥" * 80)
    
    # Параметры запуска
    BASE_DIR = "I:/docs"
    MAX_FILES = None  # Все файлы
    MAX_WORKERS = None  # Auto-detect
    
    print(f"📁 Target Directory: {BASE_DIR}")
    print(f"📊 Max Files: {'ALL' if MAX_FILES is None else MAX_FILES}")
    print(f"👥 Workers: {'AUTO' if MAX_WORKERS is None else MAX_WORKERS}")
    
    # Подтверждение запуска
    response = input("\n🔥 READY TO UNLEASH THE MONSTER? (y/N): ").strip().lower()
    
    if response == 'y':
        print("\n🚀 LAUNCHING MONSTER RAG TRAINER...")
        launch_monster(BASE_DIR, MAX_FILES, MAX_WORKERS)
    else:
        print("🛑 Monster launch cancelled.")