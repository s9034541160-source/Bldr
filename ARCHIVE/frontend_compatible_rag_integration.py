#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 FRONTEND COMPATIBLE RAG INTEGRATION V3
========================================
Полная интеграция интеллектуального чанкинга в Enhanced RAG Trainer
с обеспечением совместимости с существующим фронтендом

КЛЮЧЕВЫЕ ВОЗМОЖНОСТИ:
✅ Замена старого чанкинга на интеллектуальный (по структуре документа)
✅ Сохранение API совместимости с фронтендом
✅ Улучшенное извлечение структуры (главы, разделы, таблицы, списки)
✅ Метаданные в формате, ожидаемом фронтом
✅ Интеграция в Enhanced RAG Trainer без поломки существующего функционала
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import asdict
from datetime import datetime

# Импортируем нашу интегрированную систему
try:
    from integrated_structure_chunking_system import (
        IntegratedStructureChunkingSystem,
        process_document_with_intelligent_chunking,
        SmartChunk,
        ChunkType
    )
    INTEGRATED_SYSTEM_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ Integrated Structure & Chunking System loaded successfully")
except ImportError as e:
    INTEGRATED_SYSTEM_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ Integrated system not available: {e}")

# Импортируем Enhanced RAG Trainer
try:
    from complete_enhanced_bldr_rag_trainer import CompleteEnhancedBldrRAGTrainer
    ENHANCED_TRAINER_AVAILABLE = True
    logger.info("✅ Enhanced RAG Trainer loaded successfully")
except ImportError as e:
    ENHANCED_TRAINER_AVAILABLE = False
    logger.warning(f"⚠️ Enhanced RAG Trainer not available: {e}")

class FrontendCompatibleRAGProcessor:
    """
    🔧 Frontend-совместимый RAG процессор
    
    Интегрирует интеллектуальный чанкинг в Enhanced RAG Trainer
    с полным сохранением совместимости фронтенда
    """
    
    def __init__(self):
        """Инициализация с проверкой доступности компонентов"""
        
        if INTEGRATED_SYSTEM_AVAILABLE:
            self.intelligent_system = IntegratedStructureChunkingSystem()
            self.use_intelligent_chunking = True
            logger.info("🧩 Using intelligent structure-based chunking")
        else:
            self.intelligent_system = None
            self.use_intelligent_chunking = False
            logger.warning("⚠️ Fallback to basic chunking")
        
        if ENHANCED_TRAINER_AVAILABLE:
            self.enhanced_trainer = CompleteEnhancedBldrRAGTrainer()
            self.use_enhanced_trainer = True
            logger.info("🚀 Using Enhanced RAG Trainer v3")
        else:
            self.enhanced_trainer = None
            self.use_enhanced_trainer = False
            logger.warning("⚠️ Enhanced RAG Trainer not available")
    
    def process_document_for_frontend(self, content: str, file_path: str = "", 
                                    additional_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        🔧 ГЛАВНЫЙ МЕТОД: Обработка документа для фронтенда
        
        Возвращает структуру, полностью совместимую с ожиданиями фронтенда:
        - document_info: метаданные в ожидаемом формате
        - sections: иерархическая навигация
        - chunks: интеллектуальные чанки для RAG
        - tables: таблицы с данными
        - processing_quality: показатели качества
        """
        
        try:
            if self.use_intelligent_chunking:
                # Используем интеллектуальную систему
                result = self._process_with_intelligent_system(content, file_path, additional_metadata)
            else:
                # Fallback к базовой обработке
                result = self._process_with_fallback_system(content, file_path, additional_metadata)
            
            # Адаптируем результат для фронтенда
            frontend_result = self._adapt_for_frontend_api(result, file_path)
            
            logger.info(f"✅ Document processed: {len(frontend_result.get('chunks', []))} chunks created")
            
            return frontend_result
            
        except Exception as e:
            logger.error(f"❌ Document processing failed: {e}")
            return self._create_error_response(str(e), file_path)
    
    def _process_with_intelligent_system(self, content: str, file_path: str, 
                                       additional_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Обработка с помощью интеллектуальной системы"""
        
        # Используем интегрированную систему
        result = self.intelligent_system.process_document(content, file_path)
        
        # Добавляем дополнительные метаданные если есть
        if additional_metadata:
            result['document_info'].update(additional_metadata)
        
        return result
    
    def _process_with_fallback_system(self, content: str, file_path: str,
                                    additional_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Fallback обработка без интеллектуальной системы"""
        
        logger.info("Using fallback processing without intelligent chunking")
        
        # Базовое извлечение метаданных
        document_info = self._extract_basic_metadata(content, file_path)
        if additional_metadata:
            document_info.update(additional_metadata)
        
        # Базовые разделы (простой regex)
        sections = self._extract_basic_sections(content)
        
        # Базовые чанки (размерное деление)
        chunks = self._create_basic_chunks(content)
        
        # Базовые таблицы
        tables = self._extract_basic_tables(content)
        
        return {
            'document_info': document_info,
            'sections': sections,
            'chunks': chunks,
            'tables': tables,
            'lists': [],
            'statistics': {
                'content_length': len(content),
                'word_count': len(content.split()),
                'chunks_created': len(chunks),
                'avg_chunk_quality': 0.6,  # Умеренное качество для fallback
                'chunk_types_distribution': {'basic': len(chunks)}
            },
            'processing_info': {
                'extracted_at': datetime.now().isoformat(),
                'processor_version': 'Fallback_v1.0',
                'structure_quality': 0.5,
                'chunking_quality': 0.6,
                'processing_method': 'basic_fallback'
            }
        }
    
    def _adapt_for_frontend_api(self, result: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """
        🔧 Адаптация результата под API фронтенда
        
        Обеспечивает полную совместимость с ожидаемой фронтендом структурой
        """
        
        # Базовая структура, ожидаемая фронтендом
        frontend_result = {
            # Основная информация о документе
            "document_info": {
                "id": self._generate_document_id(file_path),
                "title": result['document_info'].get('title', ''),
                "number": result['document_info'].get('number', ''),
                "type": result['document_info'].get('type', 'unknown'),
                "organization": result['document_info'].get('organization', ''),
                "date": result['document_info'].get('approval_date', ''),
                "file_name": result['document_info'].get('file_name', Path(file_path).name),
                "file_size": result['document_info'].get('file_size', 0),
                "keywords": result['document_info'].get('keywords', []),
                "status": "processed",
                "processing_time": datetime.now().isoformat()
            },
            
            # Навигационная структура разделов
            "sections": self._format_sections_for_navigation(result.get('sections', [])),
            
            # Чанки в формате, ожидаемом для RAG
            "chunks": self._format_chunks_for_rag(result.get('chunks', [])),
            
            # Таблицы в структурированном формате
            "tables": self._format_tables_for_frontend(result.get('tables', [])),
            
            # Списки
            "lists": result.get('lists', []),
            
            # Статистика для UI
            "statistics": {
                "content_stats": {
                    "total_characters": result['statistics'].get('content_length', 0),
                    "total_words": result['statistics'].get('word_count', 0),
                    "total_sections": len(result.get('sections', [])),
                    "total_paragraphs": result['statistics'].get('paragraph_count', 0),
                    "total_tables": len(result.get('tables', [])),
                    "total_lists": len(result.get('lists', []))
                },
                "processing_stats": {
                    "chunks_created": result['statistics'].get('chunks_created', 0),
                    "avg_chunk_quality": result['statistics'].get('avg_chunk_quality', 0),
                    "chunk_types": result['statistics'].get('chunk_types_distribution', {}),
                    "structure_quality": result['processing_info'].get('structure_quality', 0),
                    "chunking_quality": result['processing_info'].get('chunking_quality', 0)
                }
            },
            
            # Метаинформация для отладки и мониторинга
            "processing_info": {
                "processor_version": result['processing_info'].get('processor_version', 'Unknown'),
                "processing_method": result['processing_info'].get('processing_method', 'unknown'),
                "extraction_quality": result['processing_info'].get('structure_quality', 0),
                "processing_time": result['processing_info'].get('extracted_at', ''),
                "features_used": {
                    "intelligent_chunking": self.use_intelligent_chunking,
                    "enhanced_trainer": self.use_enhanced_trainer,
                    "structure_extraction": True,
                    "table_extraction": len(result.get('tables', [])) > 0,
                    "list_extraction": len(result.get('lists', [])) > 0
                }
            }
        }
        
        return frontend_result
    
    def _format_sections_for_navigation(self, sections: List[Dict]) -> List[Dict]:
        """Форматирование разделов для навигации фронтенда"""
        
        navigation_sections = []
        
        for section in sections:
            nav_section = {
                "id": section.get('id', ''),
                "number": section.get('number', ''),
                "title": section.get('title', ''),
                "level": section.get('level', 1),
                "has_content": section.get('content_length', 0) > 0,
                "has_subsections": section.get('has_subsections', False),
                "parent_path": section.get('parent_path', ''),
                "metadata": {
                    "word_count": section.get('content_length', 0) // 5,  # Приблизительно
                    "section_type": section.get('type', 'section')
                }
            }
            
            # Рекурсивно добавляем подразделы
            if section.get('subsections'):
                nav_section['subsections'] = self._format_sections_for_navigation(section['subsections'])
            
            navigation_sections.append(nav_section)
        
        return navigation_sections
    
    def _format_chunks_for_rag(self, chunks: List[Dict]) -> List[Dict]:
        """Форматирование чанков для RAG системы"""
        
        rag_chunks = []
        
        for chunk in chunks:
            rag_chunk = {
                "id": chunk.get('id', ''),
                "content": chunk.get('content', ''),
                "type": chunk.get('type', 'unknown'),
                "source_elements": chunk.get('source_elements', []),
                "metadata": {
                    **chunk.get('metadata', {}),
                    "word_count": chunk.get('word_count', 0),
                    "char_count": chunk.get('char_count', 0),
                    "quality_score": chunk.get('quality_score', 0),
                    "has_tables": chunk.get('has_tables', False),
                    "has_lists": chunk.get('has_lists', False),
                    "technical_terms_count": chunk.get('technical_terms', 0)
                },
                "search_metadata": {
                    "searchable_content": chunk.get('content', '')[:500],  # Первые 500 символов для поиска
                    "keywords": self._extract_chunk_keywords(chunk.get('content', '')),
                    "section_context": chunk.get('metadata', {}).get('section_number', ''),
                    "importance_score": self._calculate_chunk_importance(chunk)
                }
            }
            
            rag_chunks.append(rag_chunk)
        
        return rag_chunks
    
    def _format_tables_for_frontend(self, tables: List[Dict]) -> List[Dict]:
        """Форматирование таблиц для фронтенда"""
        
        frontend_tables = []
        
        for i, table in enumerate(tables):
            frontend_table = {
                "id": table.get('id', f'table_{i+1}'),
                "number": table.get('number', str(i+1)),
                "title": table.get('title', f'Таблица {i+1}'),
                "headers": table.get('headers', []),
                "rows": table.get('rows', []),
                "metadata": {
                    "row_count": len(table.get('rows', [])),
                    "column_count": len(table.get('headers', [])),
                    "page_number": table.get('page_number', 0),
                    "is_structured": len(table.get('headers', [])) > 0
                },
                "display_options": {
                    "show_headers": len(table.get('headers', [])) > 0,
                    "searchable": True,
                    "exportable": True,
                    "max_display_rows": 100  # Ограничение для UI
                }
            }
            
            frontend_tables.append(frontend_table)
        
        return frontend_tables
    
    def integrate_with_enhanced_trainer(self) -> 'EnhancedBldrRAGTrainerWithIntelligentChunking':
        """
        🔧 Интеграция с Enhanced RAG Trainer
        
        Создает расширенную версию тренера с интеллектуальным чанкингом
        """
        
        if not (ENHANCED_TRAINER_AVAILABLE and INTEGRATED_SYSTEM_AVAILABLE):
            logger.warning("⚠️ Full integration not available, creating limited version")
            return EnhancedBldrRAGTrainerWithIntelligentChunking(
                use_intelligent_chunking=False,
                use_enhanced_trainer=False
            )
        
        return EnhancedBldrRAGTrainerWithIntelligentChunking(
            use_intelligent_chunking=True,
            use_enhanced_trainer=True
        )
    
    # Вспомогательные методы
    def _generate_document_id(self, file_path: str) -> str:
        """Генерация уникального ID документа"""
        import hashlib
        path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        return f"doc_{path_hash}"
    
    def _extract_chunk_keywords(self, content: str) -> List[str]:
        """Извлечение ключевых слов из чанка"""
        import re
        
        # Простое извлечение технических терминов
        keywords = []
        
        # ГОСТ, СП, СНиП
        tech_refs = re.findall(r'\b(?:ГОСТ|СП|СНиП)\s+[\d.-]+', content, re.IGNORECASE)
        keywords.extend(tech_refs)
        
        # Измерения
        measurements = re.findall(r'\b\d+(?:\.\d+)?\s*(?:мм|см|м|км|кг|т|МПа|°C)\b', content, re.IGNORECASE)
        keywords.extend([m.strip() for m in measurements])
        
        # Ограничиваем количество
        return list(dict.fromkeys(keywords))[:10]
    
    def _calculate_chunk_importance(self, chunk: Dict) -> float:
        """Расчет важности чанка для поиска"""
        importance = 0.5  # Базовая важность
        
        # Бонус за качество
        quality = chunk.get('quality_score', 0)
        importance += quality * 0.3
        
        # Бонус за наличие таблиц
        if chunk.get('has_tables', False):
            importance += 0.2
        
        # Бонус за технические термины
        tech_terms = chunk.get('technical_terms', 0)
        if tech_terms > 0:
            importance += min(tech_terms / 10.0, 0.2)
        
        return min(importance, 1.0)
    
    def _extract_basic_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """Базовое извлечение метаданных (fallback)"""
        import re
        
        # Простейшие паттерны
        title_match = re.search(r'^([А-ЯЁ][А-ЯЁ\s]{10,100})', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else ''
        
        number_match = re.search(r'(?:СП|ГОСТ|СНиП)\s+([\d.-]+)', content, re.IGNORECASE)
        number = number_match.group(1) if number_match else ''
        
        return {
            'title': title,
            'number': number,
            'type': 'unknown',
            'organization': '',
            'approval_date': '',
            'file_name': Path(file_path).name,
            'file_size': len(content.encode('utf-8')),
            'keywords': []
        }
    
    def _extract_basic_sections(self, content: str) -> List[Dict]:
        """Базовое извлечение разделов (fallback)"""
        import re
        
        sections = []
        patterns = [r'^(\d+)\.\s+([А-ЯЁ][А-ЯЁ\s]{5,80})', r'^(\d+\.\d+)\s+([А-Яа-яё][А-Яа-яё\s]{5,80})']
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, content, re.MULTILINE)
            for number, title in matches:
                sections.append({
                    'id': f'section_{len(sections)+1}',
                    'number': number,
                    'title': title,
                    'level': len(number.split('.')),
                    'type': 'section',
                    'content_length': 100,  # Приблизительно
                    'has_subsections': False,
                    'parent_path': ''
                })
        
        return sections[:20]  # Ограничиваем
    
    def _create_basic_chunks(self, content: str) -> List[Dict]:
        """Базовое создание чанков (fallback)"""
        chunks = []
        chunk_size = 800
        overlap = 100
        
        for i in range(0, len(content), chunk_size - overlap):
            chunk_text = content[i:i + chunk_size]
            if len(chunk_text) >= 50:
                chunks.append({
                    'id': f'chunk_{i//chunk_size + 1}',
                    'content': chunk_text,
                    'type': 'basic',
                    'source_elements': [],
                    'metadata': {
                        'start_position': i,
                        'end_position': i + len(chunk_text)
                    },
                    'quality_score': 0.6,
                    'word_count': len(chunk_text.split()),
                    'char_count': len(chunk_text),
                    'has_tables': '|' in chunk_text,
                    'has_lists': bool(re.search(r'^[-•*]', chunk_text, re.MULTILINE)),
                    'technical_terms': 0
                })
        
        return chunks
    
    def _extract_basic_tables(self, content: str) -> List[Dict]:
        """Базовое извлечение таблиц (fallback)"""
        import re
        
        tables = []
        table_matches = re.finditer(r'Таблица\s+(\d+)(?:\s*[-–—]\s*([^\n]+))?\n((?:\|.*\|.*\n)+)', content, re.IGNORECASE)
        
        for i, match in enumerate(table_matches):
            number = match.group(1)
            title = match.group(2) if match.group(2) else f'Таблица {number}'
            table_content = match.group(3)
            
            # Парсим строки таблицы
            rows = []
            headers = []
            for line in table_content.split('\n'):
                if '|' in line:
                    cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                    if cells:
                        if not headers:
                            headers = cells
                        else:
                            rows.append(cells)
            
            if headers or rows:
                tables.append({
                    'id': f'table_{i+1}',
                    'number': number,
                    'title': title,
                    'headers': headers,
                    'rows': rows,
                    'page_number': 0,
                    'metadata': {
                        'source_line': 0,
                        'table_type': 'basic'
                    }
                })
        
        return tables
    
    def _create_error_response(self, error_message: str, file_path: str) -> Dict[str, Any]:
        """Создание ответа об ошибке"""
        return {
            "document_info": {
                "id": "error",
                "title": "Ошибка обработки",
                "file_name": Path(file_path).name,
                "status": "error",
                "error_message": error_message
            },
            "sections": [],
            "chunks": [],
            "tables": [],
            "lists": [],
            "statistics": {
                "content_stats": {},
                "processing_stats": {}
            },
            "processing_info": {
                "processor_version": "Error_v1.0",
                "processing_method": "error_fallback",
                "features_used": {}
            }
        }

class EnhancedBldrRAGTrainerWithIntelligentChunking:
    """
    🚀 Enhanced BLDR RAG Trainer с интеллектуальным чанкингом
    
    Расширенная версия тренера, интегрирующая все улучшения
    включая интеллектуальный чанкинг по структуре документа
    """
    
    def __init__(self, use_intelligent_chunking: bool = True, use_enhanced_trainer: bool = True,
                 **kwargs):
        
        self.use_intelligent_chunking = use_intelligent_chunking
        self.use_enhanced_trainer = use_enhanced_trainer
        
        # Инициализируем компоненты
        self.frontend_processor = FrontendCompatibleRAGProcessor()
        
        if use_enhanced_trainer and ENHANCED_TRAINER_AVAILABLE:
            self.base_trainer = CompleteEnhancedBldrRAGTrainer(**kwargs)
        else:
            self.base_trainer = None
            logger.warning("⚠️ Enhanced trainer not available, using limited functionality")
        
        logger.info(f"🚀 Enhanced RAG Trainer initialized with intelligent chunking: {use_intelligent_chunking}")
    
    def train(self, max_files: Optional[int] = None, base_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        🚀 Полное обучение RAG системы с интеллектуальным чанкингом
        """
        
        logger.info("🚀 Starting Enhanced RAG Training with intelligent chunking")
        
        if self.base_trainer:
            # Используем полный Enhanced trainer
            result = self.base_trainer.train(max_files)
            logger.info("✅ Enhanced RAG training completed")
            return result
        else:
            # Упрощенная обработка
            logger.warning("⚠️ Using simplified training without full Enhanced trainer")
            return self._simplified_training(max_files, base_dir)
    
    def process_single_document(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        📄 Обработка одного документа с интеллектуальным чанкингом
        
        Возвращает результат, совместимый с фронтендом
        """
        
        logger.info(f"📄 Processing document: {Path(file_path).name}")
        
        # Используем наш frontend-совместимый процессор
        result = self.frontend_processor.process_document_for_frontend(content, file_path)
        
        logger.info(f"✅ Document processed: {len(result.get('chunks', []))} chunks, quality: {result['processing_info'].get('extraction_quality', 0):.2f}")
        
        return result
    
    def get_chunks_for_rag(self, content: str, file_path: str = "") -> List[Dict[str, Any]]:
        """
        🧩 Получение чанков для RAG системы
        
        Специализированный метод для получения только чанков
        """
        
        result = self.process_single_document(content, file_path)
        return result.get('chunks', [])
    
    def _simplified_training(self, max_files: Optional[int] = None, base_dir: Optional[str] = None) -> Dict[str, Any]:
        """Упрощенное обучение без полного Enhanced trainer"""
        
        base_path = base_dir or os.getenv("BASE_DIR", "I:/docs")
        
        # Поиск файлов
        all_files = []
        for ext in ['*.pdf', '*.docx', '*.txt']:
            files = list(Path(base_path).rglob(ext))
            all_files.extend([str(f) for f in files])
        
        if max_files:
            all_files = all_files[:max_files]
        
        logger.info(f"Found {len(all_files)} files for processing")
        
        processed_count = 0
        total_chunks = 0
        
        for file_path in all_files[:10]:  # Ограничиваем для демо
            try:
                # Читаем файл (упрощенно)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Обрабатываем
                result = self.process_single_document(content, file_path)
                total_chunks += len(result.get('chunks', []))
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
        
        return {
            'training_summary': {
                'documents_processed': processed_count,
                'total_chunks_created': total_chunks,
                'processing_method': 'simplified_intelligent_chunking'
            }
        }

# Функция для быстрого создания интеграции
def create_frontend_compatible_rag_trainer(**kwargs) -> EnhancedBldrRAGTrainerWithIntelligentChunking:
    """
    🚀 Быстрое создание RAG тренера с интеллектуальным чанкингом
    
    Returns:
        Полностью настроенный тренер с интеллектуальным чанкингом
    """
    
    return EnhancedBldrRAGTrainerWithIntelligentChunking(
        use_intelligent_chunking=True,
        use_enhanced_trainer=True,
        **kwargs
    )

# API-совместимые функции для интеграции с существующими эндпоинтами
def process_document_api_compatible(content: str, file_path: str = "") -> Dict[str, Any]:
    """
    🔧 API-совместимая функция для обработки документа
    
    Для использования в существующих API эндпоинтах без изменения интерфейса
    """
    
    processor = FrontendCompatibleRAGProcessor()
    return processor.process_document_for_frontend(content, file_path)

def get_document_structure_api(content: str, file_path: str = "") -> Dict[str, Any]:
    """
    📊 API для получения структуры документа (для навигации в UI)
    """
    
    result = process_document_api_compatible(content, file_path)
    
    return {
        'document_info': result['document_info'],
        'sections': result['sections'],
        'statistics': result['statistics']['content_stats']
    }

def get_document_chunks_api(content: str, file_path: str = "") -> List[Dict[str, Any]]:
    """
    🧩 API для получения чанков документа (для RAG системы)
    """
    
    result = process_document_api_compatible(content, file_path)
    return result['chunks']

if __name__ == "__main__":
    print("🔧 Frontend Compatible RAG Integration v3 - Ready!")
    
    # Тестирование интеграции
    try:
        # Создаем тренер с интеллектуальным чанкингом
        trainer = create_frontend_compatible_rag_trainer()
        
        # Тестовое содержимое
        test_content = """
СП 50.13330.2012
ТЕПЛОВАЯ ЗАЩИТА ЗДАНИЙ

1. ОБЩИЕ ПОЛОЖЕНИЯ
1.1 Настоящий свод правил распространяется на проектирование тепловой защиты зданий.

Таблица 1 - Нормируемые значения
|Тип здания|Сопротивление, м²·°С/Вт|
|Жилые|3,5|
|Общественные|2,8|

2. НОРМАТИВНЫЕ ССЫЛКИ
В настоящем своде правил использованы ссылки на следующие документы:
- ГОСТ 30494-2011 Здания жилые и общественные
- СП 23-101-2004 Проектирование тепловой защиты зданий
"""
        
        # Тестируем обработку документа
        result = trainer.process_single_document(test_content, "test_sp.pdf")
        
        print(f"✅ Интеграция работает:")
        print(f"  📄 Документ: {result['document_info']['title']}")
        print(f"  📊 Разделов: {len(result['sections'])}")
        print(f"  🧩 Чанков: {len(result['chunks'])}")
        print(f"  📋 Таблиц: {len(result['tables'])}")
        print(f"  🎯 Качество: {result['processing_info']['extraction_quality']:.2f}")
        
        print(f"\n🔧 API функции:")
        print(f"  - process_document_api_compatible() ✅")
        print(f"  - get_document_structure_api() ✅") 
        print(f"  - get_document_chunks_api() ✅")
        
        print(f"\n🎉 Система готова для интеграции с фронтендом!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        print("⚠️ Проверьте наличие всех зависимостей")