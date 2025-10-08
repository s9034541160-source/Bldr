#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 BACKGROUND RAG TRAINING SCRIPT
=================================
Скрипт для запуска полного RAG-обучения в фоновом режиме
на всех 1168 файлах с улучшенным интеллектуальным чанкингом

ВОЗМОЖНОСТИ:
✅ Обучение в фоне с прогресс-индикатором
✅ Использование улучшенной системы чанкинга  
✅ Логирование прогресса и ошибок
✅ Автоматическое возобновление при сбоях
✅ Детальная статистика и отчеты
"""

import os
import sys
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
from queue import Queue
import signal

# Import process tracking system
from core.process_tracker import get_process_tracker, ProcessType, ProcessStatus
from core.retry_system import get_retry_system

# Get process tracker and retry system instances
process_tracker = get_process_tracker()
retry_system = get_retry_system()

# Настройка логирования для фонового режима
log_dir = Path("C:/Bldr/logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f"rag_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Импорт нашего улучшенного RAG тренера
try:
    from working_frontend_rag_integration import create_working_rag_trainer, WorkingEnhancedRAGTrainer
    ENHANCED_RAG_AVAILABLE = True
    logger.info("✅ Enhanced RAG trainer imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import enhanced RAG trainer: {e}")
    ENHANCED_RAG_AVAILABLE = False
    sys.exit(1)

class BackgroundRAGTrainer:
    """
    🚀 Фоновый RAG тренер с мониторингом и восстановлением
    """
    
    def __init__(self, base_dir: str = "I:/docs", max_workers: int = 4):
        self.base_dir = Path(base_dir)
        self.max_workers = max_workers
        self.progress_file = Path("C:/Bldr/training_progress.json")
        self.stats_file = Path("C:/Bldr/training_stats.json")
        
        # Статистика обучения
        self.stats = {
            'start_time': None,
            'end_time': None,
            'files_found': 0,
            'files_processed': 0,
            'files_failed': 0,
            'chunks_created': 0,
            'processing_errors': [],
            'current_file': '',
            'progress_percent': 0.0,
            'estimated_time_left': 'unknown',
            'average_time_per_file': 0.0
        }
        
        # Очередь для обработки
        self.file_queue = Queue()
        self.processed_files = set()
        self.failed_files = set()
        
        # Флаги управления
        self.running = False
        self.paused = False
        
        # Создаем улучшенный тренер
        logger.info("🚀 Initializing enhanced RAG trainer...")
        self.rag_trainer = create_working_rag_trainer(use_intelligent_chunking=True)
        
        # Process tracking
        self.process_id = f"rag_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Обработка сигналов для корректного завершения
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"✅ Background RAG Trainer initialized")
        logger.info(f"📁 Base directory: {self.base_dir}")
        logger.info(f"👥 Max workers: {self.max_workers}")
    
    def discover_files(self) -> List[Path]:
        """Поиск всех документов для обработки"""
        
        logger.info("🔍 Discovering files for training...")
        
        extensions = ['*.pdf', '*.docx', '*.doc', '*.txt', '*.rtf']
        all_files = []
        
        for ext in extensions:
            try:
                files = list(self.base_dir.rglob(ext))
                all_files.extend(files)
                logger.info(f"  📄 Found {len(files)} {ext} files")
            except Exception as e:
                logger.warning(f"⚠️ Error searching for {ext}: {e}")
        
        # Фильтруем дубликаты и недоступные файлы
        unique_files = []
        seen_names = set()
        
        for file_path in all_files:
            if file_path.name.lower() not in seen_names and file_path.exists():
                unique_files.append(file_path)
                seen_names.add(file_path.name.lower())
        
        logger.info(f"📊 Total unique files discovered: {len(unique_files)}")
        self.stats['files_found'] = len(unique_files)
        
        return unique_files
    
    def load_progress(self) -> Dict:
        """Загрузка прогресса из предыдущего запуска"""
        
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    
                self.processed_files = set(progress.get('processed_files', []))
                self.failed_files = set(progress.get('failed_files', []))
                
                logger.info(f"📈 Loaded progress: {len(self.processed_files)} processed, {len(self.failed_files)} failed")
                return progress
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to load progress: {e}")
        
        return {}
    
    def save_progress(self):
        """Сохранение текущего прогресса"""
        
        progress = {
            'processed_files': list(self.processed_files),
            'failed_files': list(self.failed_files),
            'stats': self.stats,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ Failed to save progress: {e}")
    
    def save_stats(self):
        """Сохранение детальной статистики"""
        
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ Failed to save stats: {e}")
    
    def process_single_file(self, file_path: Path) -> Dict[str, Any]:
        """Обработка одного файла с улучшенным чанкингом"""
        
        start_time = time.time()
        result = {
            'file_path': str(file_path),
            'success': False,
            'chunks_created': 0,
            'processing_time': 0,
            'error': None,
            'file_size': 0
        }
        
        try:
            # Проверяем размер файла
            if file_path.stat().st_size > 50 * 1024 * 1024:  # 50MB
                raise ValueError(f"File too large: {file_path.stat().st_size / 1024 / 1024:.1f}MB")
            
            result['file_size'] = file_path.stat().st_size
            
            # Читаем содержимое файла
            if file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            else:
                # Для других форматов используем простое чтение
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
                        except ImportError:
                            logger.warning("PyPDF2 not available for PDF processing")
                            raise ValueError("PDF processing library not available")
                    elif file_path.suffix.lower() in ['.docx', '.doc']:
                        # Импорт DOCX обработчика
                        try:
                            from docx import Document
                            doc = Document(str(file_path))
                            content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                        except ImportError:
                            logger.warning("python-docx not available for DOCX processing")
                            raise ValueError("DOCX processing library not available")
                    else:
                        # Для текстовых файлов
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                except Exception as e:
                    # Fallback для бинарных файлов
                    logger.warning(f"⚠️ Skipping file {file_path}: {str(e)}")
                    raise ValueError(f"File format not supported or processing error: {str(e)}")
            
            if not content.strip():
                raise ValueError("Empty file content")
            
            # Обрабатываем с помощью улучшенного RAG тренера
            document_result = self.rag_trainer.process_single_document(content, str(file_path))
            
            chunks_count = len(document_result.get('chunks', []))
            result['chunks_created'] = chunks_count
            result['success'] = True
            
            logger.info(f"✅ Processed {file_path.name}: {chunks_count} chunks")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Failed to process {file_path.name}: {e}")
        
        result['processing_time'] = time.time() - start_time
        return result
    
    def update_stats(self, result: Dict[str, Any]):
        """Обновление статистики обработки"""
        
        if result['success']:
            self.stats['files_processed'] += 1
            self.stats['chunks_created'] += result['chunks_created']
            self.processed_files.add(result['file_path'])
        else:
            self.stats['files_failed'] += 1
            self.failed_files.add(result['file_path'])
            self.stats['processing_errors'].append({
                'file': result['file_path'],
                'error': result['error'],
                'timestamp': datetime.now().isoformat()
            })
        
        # Обновляем прогресс
        total_files = self.stats['files_found']
        processed_total = self.stats['files_processed'] + self.stats['files_failed']
        
        if total_files > 0:
            self.stats['progress_percent'] = (processed_total / total_files) * 100
        
        # Обновляем среднее время обработки
        if self.stats['files_processed'] > 0:
            elapsed_time = time.time() - self.stats['start_time']
            self.stats['average_time_per_file'] = elapsed_time / processed_total
            
            # Оценка времени до завершения
            files_left = total_files - processed_total
            estimated_seconds = files_left * self.stats['average_time_per_file']
            self.stats['estimated_time_left'] = str(timedelta(seconds=int(estimated_seconds)))
    
    def print_progress(self):
        """Вывод прогресса обучения"""
        
        progress = self.stats['progress_percent']
        processed = self.stats['files_processed']
        failed = self.stats['files_failed']
        total = self.stats['files_found']
        chunks = self.stats['chunks_created']
        time_left = self.stats['estimated_time_left']
        
        print(f"\n📊 RAG Training Progress:")
        print(f"  📈 Progress: {progress:.1f}% ({processed + failed}/{total})")
        print(f"  ✅ Processed: {processed} files")
        print(f"  ❌ Failed: {failed} files")
        print(f"  🧩 Chunks created: {chunks}")
        print(f"  ⏱️ Time left: {time_left}")
        print(f"  📄 Current: {self.stats.get('current_file', 'N/A')}")
    
    def start_training(self, resume: bool = True):
        """Запуск полного обучения в фоне"""
        
        logger.info("🚀 Starting background RAG training...")
        
        # Register process with process tracker
        process_tracker.start_process(
            process_id=self.process_id,
            process_type=ProcessType.RAG_TRAINING,
            name="RAG Training Process",
            description="Full RAG training on all documents",
            metadata={
                "base_dir": str(self.base_dir),
                "max_workers": self.max_workers,
                "resume": resume
            }
        )
        
        # Update process tracker status
        process_tracker.update_process(
            self.process_id,
            status=ProcessStatus.RUNNING,
            progress=0,
            metadata_update={"stage": "initializing"}
        )
        
        # Загружаем прогресс если нужно
        if resume:
            self.load_progress()
        
        # Находим все файлы
        all_files = self.discover_files()
        
        if not all_files:
            logger.error("❌ No files found for training!")
            process_tracker.update_process(
                self.process_id,
                status=ProcessStatus.FAILED,
                metadata_update={"stage": "error", "error": "No files found for training"}
            )
            return
        
        # Фильтруем уже обработанные файлы при возобновлении
        if resume:
            files_to_process = [f for f in all_files if str(f) not in self.processed_files]
            logger.info(f"📁 Resuming training: {len(files_to_process)} files left to process")
        else:
            files_to_process = all_files
            self.processed_files.clear()
            self.failed_files.clear()
        
        if not files_to_process:
            logger.info("✅ All files already processed!")
            process_tracker.update_process(
                self.process_id,
                status=ProcessStatus.COMPLETED,
                progress=100,
                metadata_update={"stage": "completed", "message": "All files already processed"}
            )
            return
        
        self.stats['start_time'] = time.time()
        self.stats['files_found'] = len(all_files)
        self.running = True
        
        # Update process tracker
        process_tracker.update_process(
            self.process_id,
            progress=5,
            metadata_update={"stage": "processing", "files_to_process": len(files_to_process)}
        )
        
        # Запускаем отдельный поток для печати прогресса
        progress_thread = threading.Thread(target=self._progress_monitor, daemon=True)
        progress_thread.start()
        
        # Обрабатываем файлы в многопоточном режиме
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Отправляем задачи на обработку
                future_to_file = {
                    executor.submit(self.process_single_file, file_path): file_path 
                    for file_path in files_to_process
                }
                
                # Обрабатываем результаты по мере готовности
                for future in as_completed(future_to_file):
                    if not self.running:
                        break
                    
                    file_path = future_to_file[future]
                    self.stats['current_file'] = file_path.name
                    
                    try:
                        result = future.result(timeout=1800)  # 30 минут таймаут
                        self.update_stats(result)
                        
                        # Update process tracker with progress
                        total_files = self.stats['files_found']
                        processed_total = self.stats['files_processed'] + self.stats['files_failed']
                        progress_percent = (processed_total / total_files) * 100 if total_files > 0 else 0
                        
                        process_tracker.update_process(
                            self.process_id,
                            progress=int(progress_percent),
                            metadata_update={
                                "stage": "processing",
                                "current_file": file_path.name,
                                "files_processed": self.stats['files_processed'],
                                "files_failed": self.stats['files_failed']
                            }
                        )
                        
                        # Сохраняем прогресс каждые 10 файлов
                        if (self.stats['files_processed'] + self.stats['files_failed']) % 10 == 0:
                            self.save_progress()
                            self.save_stats()
                        
                    except Exception as e:
                        logger.error(f"❌ Task failed for {file_path.name}: {e}")
                        self.stats['files_failed'] += 1
                        self.failed_files.add(str(file_path))
                        
                        # Update process tracker with error
                        process_tracker.update_process(
                            self.process_id,
                            metadata_update={
                                "stage": "processing",
                                "error_files": len(self.failed_files),
                                "last_error": str(e)
                            }
                        )
        
        except KeyboardInterrupt:
            logger.info("⚠️ Training interrupted by user")
            process_tracker.update_process(
                self.process_id,
                status=ProcessStatus.CANCELLED,
                metadata_update={"stage": "cancelled", "message": "Training interrupted by user"}
            )
        except Exception as e:
            logger.error(f"❌ Training failed with error: {e}")
            process_tracker.update_process(
                self.process_id,
                status=ProcessStatus.FAILED,
                metadata_update={"stage": "error", "error": str(e)}
            )
        
        finally:
            self.running = False
            self.stats['end_time'] = time.time()
            
            # Сохраняем финальный прогресс и статистику
            self.save_progress()
            self.save_stats()
            
            # Update process tracker with final status
            if self.stats['files_failed'] == 0:
                process_tracker.update_process(
                    self.process_id,
                    status=ProcessStatus.COMPLETED,
                    progress=100,
                    metadata_update={"stage": "completed", "message": "Training completed successfully"}
                )
            else:
                process_tracker.update_process(
                    self.process_id,
                    status=ProcessStatus.COMPLETED,
                    progress=100,
                    metadata_update={
                        "stage": "completed_with_errors",
                        "message": f"Training completed with {self.stats['files_failed']} failed files",
                        "files_processed": self.stats['files_processed'],
                        "files_failed": self.stats['files_failed']
                    }
                )
            
            # Выводим финальный отчет
            self._print_final_report()
    
    def _progress_monitor(self):
        """Мониторинг прогресса в отдельном потоке"""
        
        while self.running:
            self.print_progress()
            time.sleep(30)  # Обновляем каждые 30 секунд
    
    def _print_final_report(self):
        """Вывод финального отчета обучения"""
        
        total_time = self.stats['end_time'] - self.stats['start_time']
        
        logger.info("🎯 RAG Training Completed!")
        logger.info("=" * 50)
        logger.info(f"📊 Final Statistics:")
        logger.info(f"  📁 Files found: {self.stats['files_found']}")
        logger.info(f"  ✅ Successfully processed: {self.stats['files_processed']}")
        logger.info(f"  ❌ Failed: {self.stats['files_failed']}")
        logger.info(f"  🧩 Total chunks created: {self.stats['chunks_created']}")
        logger.info(f"  ⏱️ Total time: {timedelta(seconds=int(total_time))}")
        logger.info(f"  📈 Success rate: {(self.stats['files_processed'] / self.stats['files_found'] * 100):.1f}%")
        
        if self.stats['files_failed'] > 0:
            logger.info(f"⚠️ Failed files:")
            for error in self.stats['processing_errors'][-10:]:  # Показываем последние 10 ошибок
                logger.info(f"    - {Path(error['file']).name}: {error['error']}")
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        logger.info(f"📨 Received signal {signum}, gracefully shutting down...")
        self.running = False

def start_background_training(base_dir: str = "I:/docs", max_workers: int = 4, resume: bool = True):
    """
    🚀 Запуск фонового RAG обучения
    
    Args:
        base_dir: Директория с документами для обучения
        max_workers: Максимальное количество параллельных потоков
        resume: Возобновить предыдущее обучение если есть прогресс
    """
    trainer = BackgroundRAGTrainer(base_dir=base_dir, max_workers=max_workers)
    trainer.start_training(resume=resume)

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Background RAG Training")
    parser.add_argument("--base-dir", default="I:/docs", help="Base directory with documents")
    parser.add_argument("--max-workers", type=int, default=4, help="Maximum number of worker threads")
    parser.add_argument("--no-resume", action="store_true", help="Do not resume from previous progress")
    
    args = parser.parse_args()
    
    # Start training
    start_background_training(
        base_dir=args.base_dir,
        max_workers=args.max_workers,
        resume=not args.no_resume
    )