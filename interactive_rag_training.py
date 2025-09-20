#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 INTERACTIVE RAG TRAINING
===========================
Интерактивное RAG-обучение с подробным выводом процесса
для наблюдения за каждым шагом обработки документов

ВОЗМОЖНОСТИ:
✅ Живой вывод прогресса обработки каждого файла
✅ Детальная статистика по каждому документу
✅ Визуализация структуры извлеченных данных
✅ Отображение качества чанкинга в реальном времени
✅ Возможность остановки в любой момент
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from colorama import init, Fore, Style, Back
init()  # Инициализация colorama для Windows

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Импорт нашего улучшенного RAG тренера
try:
    from working_frontend_rag_integration import create_working_rag_trainer
    ENHANCED_RAG_AVAILABLE = True
except ImportError as e:
    print(f"❌ Failed to import enhanced RAG trainer: {e}")
    ENHANCED_RAG_AVAILABLE = False
    sys.exit(1)

class InteractiveRAGTrainer:
    """
    🎯 Интерактивный RAG тренер с подробным выводом
    """
    
    def __init__(self, base_dir: str = "I:/docs"):
        self.base_dir = Path(base_dir)
        self.stats = {
            'start_time': None,
            'files_found': 0,
            'files_processed': 0,
            'files_failed': 0,
            'chunks_created': 0,
            'total_sections': 0,
            'total_tables': 0,
            'total_lists': 0,
            'processing_errors': []
        }
        
        print(f"{Fore.CYAN}🚀 Initializing Interactive RAG Trainer...{Style.RESET_ALL}")
        self.rag_trainer = create_working_rag_trainer(use_intelligent_chunking=True)
        print(f"{Fore.GREEN}✅ Enhanced RAG Trainer ready!{Style.RESET_ALL}")
        print(f"{Fore.BLUE}📁 Base directory: {self.base_dir}{Style.RESET_ALL}")
        
        # Проверяем доступность папки
        if not self.base_dir.exists():
            print(f"{Fore.RED}❌ Base directory not found: {self.base_dir}{Style.RESET_ALL}")
            sys.exit(1)
    
    def discover_files(self, limit: int = None) -> List[Path]:
        """Поиск документов с ограничением количества"""
        
        print(f"\n{Fore.YELLOW}🔍 Discovering files for training...{Style.RESET_ALL}")
        
        extensions = ['*.pdf', '*.docx', '*.doc', '*.txt', '*.rtf']
        all_files = []
        
        for ext in extensions:
            try:
                files = list(self.base_dir.rglob(ext))
                all_files.extend(files)
                print(f"  {Fore.CYAN}📄 Found {len(files)} {ext} files{Style.RESET_ALL}")
            except Exception as e:
                print(f"  {Fore.RED}⚠️ Error searching for {ext}: {e}{Style.RESET_ALL}")
        
        # Убираем дубликаты
        unique_files = []
        seen_names = set()
        
        for file_path in all_files:
            if file_path.name.lower() not in seen_names and file_path.exists():
                unique_files.append(file_path)
                seen_names.add(file_path.name.lower())
        
        # Ограничиваем количество если указано
        if limit:
            unique_files = unique_files[:limit]
            print(f"{Fore.YELLOW}⚠️ Limited to first {limit} files{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}📊 Total files to process: {len(unique_files)}{Style.RESET_ALL}")
        self.stats['files_found'] = len(unique_files)
        
        return unique_files
    
    def print_file_header(self, file_path: Path, index: int, total: int):
        """Печать заголовка для файла"""
        
        progress = (index / total) * 100
        print(f"\n{Back.BLUE}{Fore.WHITE} FILE {index}/{total} ({progress:.1f}%) {Style.RESET_ALL}")
        print(f"{Fore.CYAN}📄 Processing: {file_path.name}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}📁 Path: {file_path}{Style.RESET_ALL}")
        
        # Информация о файле
        try:
            size = file_path.stat().st_size
            size_mb = size / (1024 * 1024)
            print(f"{Fore.BLUE}📏 Size: {size_mb:.2f} MB{Style.RESET_ALL}")
        except:
            print(f"{Fore.RED}⚠️ Cannot read file size{Style.RESET_ALL}")
        
        print("─" * 60)
    
    def process_single_file(self, file_path: Path, index: int, total: int) -> Dict[str, Any]:
        """Обработка одного файла с подробным выводом"""
        
        self.print_file_header(file_path, index, total)
        
        start_time = time.time()
        result = {
            'file_path': str(file_path),
            'success': False,
            'chunks_created': 0,
            'sections_found': 0,
            'tables_found': 0,
            'lists_found': 0,
            'processing_time': 0,
            'error': None,
            'quality_score': 0
        }
        
        try:
            print(f"{Fore.YELLOW}⏳ Reading file content...{Style.RESET_ALL}")
            
            # Проверяем размер файла
            if file_path.stat().st_size > 50 * 1024 * 1024:  # 50MB
                raise ValueError(f"File too large: {file_path.stat().st_size / 1024 / 1024:.1f}MB")
            
            # Читаем содержимое
            content = ""
            if file_path.suffix.lower() in ['.txt', '.rtf']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            elif file_path.suffix.lower() in ['.pdf', '.docx', '.doc']:
                # Для демонстрации пока читаем как текст
                print(f"{Fore.YELLOW}📄 Note: Reading {file_path.suffix} as text (PDF/DOCX parsing not implemented yet){Style.RESET_ALL}")
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except:
                    raise ValueError("Binary file - cannot read as text")
            
            if not content.strip():
                raise ValueError("Empty file content")
            
            print(f"{Fore.GREEN}✅ Content loaded: {len(content)} characters{Style.RESET_ALL}")
            
            # Обрабатываем с помощью улучшенного RAG тренера
            print(f"{Fore.YELLOW}🧠 Processing with Enhanced RAG Trainer...{Style.RESET_ALL}")
            
            document_result = self.rag_trainer.process_single_document(content, str(file_path))
            
            # Извлекаем результаты
            chunks = document_result.get('chunks', [])
            sections = document_result.get('sections', [])
            tables = document_result.get('tables', [])
            lists = document_result.get('lists', [])
            
            result['chunks_created'] = len(chunks)
            result['sections_found'] = len(sections)
            result['tables_found'] = len(tables)
            result['lists_found'] = len(lists)
            
            # Рассчитываем качество
            quality = document_result.get('processing_info', {}).get('extraction_quality', 0)
            result['quality_score'] = quality
            
            result['success'] = True
            
            # Выводим подробные результаты
            self.print_processing_results(document_result, chunks, sections, tables, lists)
            
        except Exception as e:
            result['error'] = str(e)
            print(f"{Fore.RED}❌ Processing failed: {e}{Style.RESET_ALL}")
        
        result['processing_time'] = time.time() - start_time
        
        # Выводим итоги обработки файла
        self.print_file_summary(result)
        
        return result
    
    def print_processing_results(self, document_result: Dict, chunks: List, sections: List, tables: List, lists: List):
        """Детальный вывод результатов обработки"""
        
        print(f"\n{Fore.GREEN}🎯 PROCESSING RESULTS:{Style.RESET_ALL}")
        
        # Информация о документе
        doc_info = document_result.get('document_info', {})
        if doc_info.get('title'):
            print(f"  📄 Title: {Fore.CYAN}{doc_info['title']}{Style.RESET_ALL}")
        if doc_info.get('number'):
            print(f"  🔢 Number: {Fore.CYAN}{doc_info['number']}{Style.RESET_ALL}")
        if doc_info.get('type'):
            print(f"  📝 Type: {Fore.CYAN}{doc_info['type']}{Style.RESET_ALL}")
        
        # Структура документа
        print(f"\n{Fore.YELLOW}📋 DOCUMENT STRUCTURE:{Style.RESET_ALL}")
        print(f"  🧩 Chunks: {Fore.GREEN}{len(chunks)}{Style.RESET_ALL}")
        print(f"  📑 Sections: {Fore.GREEN}{len(sections)}{Style.RESET_ALL}")
        print(f"  📊 Tables: {Fore.GREEN}{len(tables)}{Style.RESET_ALL}")
        print(f"  📄 Lists: {Fore.GREEN}{len(lists)}{Style.RESET_ALL}")
        
        # Показываем первые несколько разделов
        if sections:
            print(f"\n{Fore.BLUE}📑 SECTIONS PREVIEW:{Style.RESET_ALL}")
            for i, section in enumerate(sections[:3]):
                print(f"  {i+1}. [{section.get('number', 'N/A')}] {section.get('title', 'Untitled')[:50]}...")
            if len(sections) > 3:
                print(f"    ... and {len(sections) - 3} more sections")
        
        # Показываем таблицы
        if tables:
            print(f"\n{Fore.BLUE}📊 TABLES PREVIEW:{Style.RESET_ALL}")
            for i, table in enumerate(tables[:2]):
                title = table.get('title', f'Table {i+1}')
                headers = table.get('headers', [])
                rows = table.get('rows', [])
                print(f"  {i+1}. {title}")
                print(f"     Headers: {headers[:3]}{' ...' if len(headers) > 3 else ''}")
                print(f"     Rows: {len(rows)}")
        
        # Показываем качество чанков
        if chunks:
            print(f"\n{Fore.BLUE}🧩 CHUNKS QUALITY:{Style.RESET_ALL}")
            qualities = [chunk.get('metadata', {}).get('quality_score', 0) for chunk in chunks]
            avg_quality = sum(qualities) / len(qualities) if qualities else 0
            print(f"  📈 Average quality: {Fore.GREEN}{avg_quality:.2f}{Style.RESET_ALL}")
            
            # Показываем типы чанков
            chunk_types = {}
            for chunk in chunks:
                chunk_type = chunk.get('type', 'unknown')
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            print(f"  📊 Chunk types:")
            for chunk_type, count in chunk_types.items():
                print(f"    - {chunk_type}: {count}")
    
    def print_file_summary(self, result: Dict):
        """Вывод итогов обработки файла"""
        
        print(f"\n{Back.GREEN if result['success'] else Back.RED}{Fore.WHITE} FILE SUMMARY {Style.RESET_ALL}")
        
        if result['success']:
            print(f"{Fore.GREEN}✅ SUCCESS{Style.RESET_ALL}")
            print(f"  ⏱️ Time: {result['processing_time']:.2f}s")
            print(f"  🧩 Chunks: {result['chunks_created']}")
            print(f"  📑 Sections: {result['sections_found']}")
            print(f"  📊 Tables: {result['tables_found']}")
            print(f"  📄 Lists: {result['lists_found']}")
            print(f"  📈 Quality: {result['quality_score']:.2f}")
        else:
            print(f"{Fore.RED}❌ FAILED{Style.RESET_ALL}")
            print(f"  ❌ Error: {result['error']}")
            print(f"  ⏱️ Time: {result['processing_time']:.2f}s")
        
        print("═" * 60)
    
    def update_global_stats(self, result: Dict):
        """Обновление глобальной статистики"""
        
        if result['success']:
            self.stats['files_processed'] += 1
            self.stats['chunks_created'] += result['chunks_created']
            self.stats['total_sections'] += result['sections_found']
            self.stats['total_tables'] += result['tables_found']
            self.stats['total_lists'] += result['lists_found']
        else:
            self.stats['files_failed'] += 1
            self.stats['processing_errors'].append({
                'file': Path(result['file_path']).name,
                'error': result['error']
            })
    
    def print_progress_stats(self):
        """Вывод общей статистики прогресса"""
        
        total_processed = self.stats['files_processed'] + self.stats['files_failed']
        progress = (total_processed / self.stats['files_found']) * 100 if self.stats['files_found'] > 0 else 0
        
        print(f"\n{Back.CYAN}{Fore.WHITE} OVERALL PROGRESS: {progress:.1f}% {Style.RESET_ALL}")
        print(f"{Fore.CYAN}📊 Total Progress: {total_processed}/{self.stats['files_found']} files{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Successful: {self.stats['files_processed']}{Style.RESET_ALL}")
        print(f"{Fore.RED}❌ Failed: {self.stats['files_failed']}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}🧩 Total Chunks: {self.stats['chunks_created']}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}📑 Total Sections: {self.stats['total_sections']}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}📊 Total Tables: {self.stats['total_tables']}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}📄 Total Lists: {self.stats['total_lists']}{Style.RESET_ALL}")
        
        if self.stats['start_time']:
            elapsed = time.time() - self.stats['start_time']
            avg_time = elapsed / total_processed if total_processed > 0 else 0
            remaining_files = self.stats['files_found'] - total_processed
            estimated_time = remaining_files * avg_time
            
            print(f"{Fore.YELLOW}⏱️ Elapsed: {timedelta(seconds=int(elapsed))}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}📈 Est. remaining: {timedelta(seconds=int(estimated_time))}{Style.RESET_ALL}")
    
    def start_training(self, max_files: int = None, show_progress_every: int = 5):
        """Запуск интерактивного обучения"""
        
        print(f"\n{Back.MAGENTA}{Fore.WHITE} 🚀 STARTING INTERACTIVE RAG TRAINING 🚀 {Style.RESET_ALL}")
        
        # Поиск файлов
        files = self.discover_files(limit=max_files)
        
        if not files:
            print(f"{Fore.RED}❌ No files found for training!{Style.RESET_ALL}")
            return
        
        # Подтверждение от пользователя
        print(f"\n{Fore.YELLOW}❓ Ready to process {len(files)} files?{Style.RESET_ALL}")
        response = input(f"{Fore.CYAN}Press Enter to continue or 'q' to quit: {Style.RESET_ALL}")
        if response.lower() == 'q':
            print(f"{Fore.YELLOW}👋 Training cancelled{Style.RESET_ALL}")
            return
        
        self.stats['start_time'] = time.time()
        
        try:
            for index, file_path in enumerate(files, 1):
                # Обрабатываем файл
                result = self.process_single_file(file_path, index, len(files))
                self.update_global_stats(result)
                
                # Показываем общий прогресс через определенное количество файлов
                if index % show_progress_every == 0 or index == len(files):
                    self.print_progress_stats()
                
                # Пауза между файлами для наблюдения
                if index < len(files):
                    time.sleep(0.5)  # Небольшая пауза для читаемости
        
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️ Training interrupted by user{Style.RESET_ALL}")
        
        # Финальный отчет
        self.print_final_report()
    
    def print_final_report(self):
        """Финальный отчет обучения"""
        
        total_time = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        success_rate = (self.stats['files_processed'] / self.stats['files_found']) * 100 if self.stats['files_found'] > 0 else 0
        
        print(f"\n{Back.GREEN}{Fore.WHITE} 🎯 FINAL TRAINING REPORT 🎯 {Style.RESET_ALL}")
        print("=" * 60)
        print(f"{Fore.CYAN}📊 STATISTICS:{Style.RESET_ALL}")
        print(f"  📁 Files found: {self.stats['files_found']}")
        print(f"  ✅ Successfully processed: {Fore.GREEN}{self.stats['files_processed']}{Style.RESET_ALL}")
        print(f"  ❌ Failed: {Fore.RED}{self.stats['files_failed']}{Style.RESET_ALL}")
        print(f"  📈 Success rate: {Fore.GREEN}{success_rate:.1f}%{Style.RESET_ALL}")
        print(f"  ⏱️ Total time: {Fore.YELLOW}{timedelta(seconds=int(total_time))}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}🎯 RESULTS:{Style.RESET_ALL}")
        print(f"  🧩 Total chunks created: {Fore.GREEN}{self.stats['chunks_created']}{Style.RESET_ALL}")
        print(f"  📑 Total sections found: {Fore.GREEN}{self.stats['total_sections']}{Style.RESET_ALL}")
        print(f"  📊 Total tables extracted: {Fore.GREEN}{self.stats['total_tables']}{Style.RESET_ALL}")
        print(f"  📄 Total lists found: {Fore.GREEN}{self.stats['total_lists']}{Style.RESET_ALL}")
        
        if self.stats['processing_errors']:
            print(f"\n{Fore.RED}⚠️ ERRORS (last 5):{Style.RESET_ALL}")
            for error in self.stats['processing_errors'][-5:]:
                print(f"  - {error['file']}: {error['error']}")
        
        print(f"\n{Fore.GREEN}🎉 RAG Training completed successfully!{Style.RESET_ALL}")

def main():
    """Основная функция"""
    
    print(f"{Fore.MAGENTA}🚀 Interactive RAG Training System{Style.RESET_ALL}")
    print(f"{Fore.BLUE}Enhanced with Intelligent Document Chunking{Style.RESET_ALL}")
    print("=" * 60)
    
    # Параметры
    base_dir = input(f"{Fore.CYAN}📁 Enter base directory (default: I:/docs): {Style.RESET_ALL}").strip() or "I:/docs"
    
    try:
        max_files = input(f"{Fore.CYAN}📊 Max files to process (default: all): {Style.RESET_ALL}").strip()
        max_files = int(max_files) if max_files else None
    except ValueError:
        max_files = None
    
    # Создаем и запускаем тренер
    trainer = InteractiveRAGTrainer(base_dir=base_dir)
    trainer.start_training(max_files=max_files)

if __name__ == "__main__":
    main()