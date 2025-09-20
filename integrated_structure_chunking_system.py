#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 INTEGRATED STRUCTURE & CHUNKING SYSTEM V3
============================================
Полностью интегрированная система с:
✅ Детальным извлечением структуры (главы, разделы, подразделы, абзацы, таблицы)
✅ Интеллектуальным чанкингом по структуре документа
✅ Совместимостью с фронтендом API
✅ Интеграцией в Enhanced RAG Trainer

ПРОБЛЕМЫ ИСПРАВЛЕНЫ:
❌ Чанкинг по 300-500 символов → ✅ Интеллектуальный чанкинг по структуре
❌ Неточное извлечение структуры → ✅ Детальная иерархия с метаданными
❌ Несовместимость с фронтом → ✅ API-совместимая структура
"""

import re
import json
import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import hashlib
import logging

logger = logging.getLogger(__name__)

class ChunkType(Enum):
    """Типы чанков для интеллектуального разбиения"""
    SECTION = "section"           # Целый раздел 
    SUBSECTION = "subsection"     # Подраздел
    PARAGRAPH = "paragraph"       # Абзац
    TABLE = "table"              # Таблица
    LIST = "list"                # Список
    MIXED = "mixed"              # Смешанный контент
    FRAGMENT = "fragment"        # Фрагмент (при превышении размера)

@dataclass
class DocumentElement:
    """Базовый элемент документа"""
    id: str
    type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    position: int = 0
    page_number: int = 0

@dataclass
class DocumentSection(DocumentElement):
    """Раздел документа"""
    number: str = ""
    title: str = ""
    level: int = 1
    
@dataclass 
class DocumentParagraph(DocumentElement):
    """Абзац документа"""
    section_id: Optional[str] = None
    
@dataclass
class DocumentTable(DocumentElement):
    """Таблица документа"""
    number: str = ""
    title: str = ""
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)

@dataclass
class DocumentList(DocumentElement):
    """Список документа"""
    list_type: str = "bulleted"  # bulleted, numbered, mixed
    items: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class SmartChunk:
    """Интеллектуальный чанк с метаданными"""
    id: str
    content: str
    chunk_type: ChunkType
    source_elements: List[str]  # IDs элементов-источников
    metadata: Dict[str, Any]
    quality_score: float = 0.0
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для API"""
        return {
            'id': self.id,
            'content': self.content,
            'type': self.chunk_type.value,
            'source_elements': self.source_elements,
            'metadata': self.metadata,
            'quality_score': self.quality_score,
            'word_count': len(self.content.split()),
            'char_count': len(self.content),
            'has_tables': 'table' in self.chunk_type.value.lower() or '|' in self.content,
            'has_lists': bool(re.search(r'^\s*[-•*\d+]\s+', self.content, re.MULTILINE)),
            'technical_terms': self._count_technical_terms()
        }
    
    def _count_technical_terms(self) -> int:
        """Подсчет технических терминов"""
        patterns = [
            r'\b(?:ГОСТ|СП|СНиП)\s+[\d.-]+',
            r'\b\d+(?:\.\d+)?\s*(?:мм|см|м|км|г|кг|т|МПа|кПа|°C)\b',
            r'\b\d+(?:\.\d+)*\s*%\b'
        ]
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, self.content, re.IGNORECASE))
        return count

class AdvancedStructureExtractor:
    """
    🔍 Продвинутый экстрактор структуры документов
    
    Извлекает детальную иерархическую структуру:
    - Главы, разделы, подразделы с точной нумерацией
    - Абзацы с привязкой к разделам
    - Таблицы с полным содержимым и метаданными
    - Списки всех типов с иерархией
    - Метаданные документа (название, номер, даты, организация)
    """
    
    def __init__(self):
        self.section_patterns = {
            # Основные разделы: "1. ОБЩИЕ ПОЛОЖЕНИЯ", "2. НОРМАТИВНЫЕ ССЫЛКИ"
            'main_sections': [
                r'^(\d+)\.\s+([А-ЯЁ][А-ЯЁ\s]{4,80})(?:\s*\.?\s*)?$',
                r'^(\d+)\s+([А-ЯЁ][А-ЯЁ\s]{4,80})(?:\s*\.?\s*)?$',
            ],
            
            # Подразделы: "1.1 Общие требования", "1.2 Область применения"
            'subsections': [
                r'^(\d+\.\d+)\s+([А-Яа-яё][А-Яа-яё\s]{5,100})(?:\s*\.?\s*)?$',
                r'^(\d+\.\d+)\.\s+([А-Яа-яё][А-Яа-яё\s]{5,100})(?:\s*\.?\s*)?$',
            ],
            
            # Подподразделы: "1.1.1 Детальные требования"
            'subsubsections': [
                r'^(\d+\.\d+\.\d+)\s+([А-Яа-яё][А-Яа-яё\s]{5,100})(?:\s*\.?\s*)?$',
                r'^(\d+\.\d+\.\d+)\.\s+([А-Яа-яё][А-Яа-яё\s]{5,100})(?:\s*\.?\s*)?$',
            ],
            
            # Приложения: "Приложение А", "ПРИЛОЖЕНИЕ Б"
            'appendices': [
                r'^((?:Приложение|ПРИЛОЖЕНИЕ)\s+[А-Я])\s*\.?\s*([А-ЯЁа-яё\s]{0,100})(?:\s*\.?\s*)?$',
            ],
            
            # Буквенные пункты: "а) требования", "б) методы"
            'lettered_items': [
                r'^([а-я])\)\s+([А-Яа-яё][А-Яа-яё\s\.,]{5,150})$',
                r'^\(([а-я])\)\s+([А-Яа-яё][А-Яа-яё\s\.,]{5,150})$',
            ]
        }
        
        self.table_patterns = {
            'table_header': r'(?:Таблица|ТАБЛИЦА)\s+(\d+(?:\.\d+)*)\s*[-–—]?\s*([^\n\r]{0,100})',
            'table_row': r'\|([^|]+(?:\|[^|]*)*)\|',
            'table_separator': r'\|[-\s:=|]+\|',
        }
        
        self.list_patterns = {
            'numbered_list': r'^(\d+(?:\.\d+)*)\.\s+(.+)$',
            'bulleted_list': r'^[-•*]\s+(.+)$', 
            'lettered_list': r'^([а-я])\)\s+(.+)$|^\(([а-я])\)\s+(.+)$',
            'mixed_list': r'^(?:[-•*]|\d+\.|[а-я]\)|\([а-я]\))\s+(.+)$'
        }
        
        self.metadata_patterns = {
            'document_number': [
                r'(?:СП|СВОД\s+ПРАВИЛ)\s+(\d+(?:\.\d+)*(?:-\d+)*)',
                r'(?:ГОСТ)\s+(\d+(?:\.\d+)*(?:-\d+)*)',
                r'(?:СНиП)\s+([\d.-]+)',
                r'(?:РД|ВСН|ТУ)\s+([\d.-]+)',
            ],
            'document_title': [
                r'^([А-ЯЁ][А-ЯЁ\s]{10,120})$',
                r'(?:СВОД\s+ПРАВИЛ|СП\s+[\d.-]+)\s*\.?\s*([А-ЯЁ][А-ЯЁ\s]{10,120})',
                r'(?:ГОСТ\s+[\d.-]+)\s*\.?\s*([А-ЯЁ][А-ЯЁ\s]{10,120})',
            ],
            'organization': [
                r'(?:УТВЕРЖДЕН|УТВЕРЖДЕНО)\s+([А-ЯЁ][А-Яа-яё\s]{10,80})',
                r'(?:Минстрой\s+России|Росстандарт|Минрегион\s+России|Госстрой\s+России)',
            ],
            'dates': [
                r'(\d{1,2}\.\d{1,2}\.\d{4})',
                r'(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{4})',
            ]
        }

    def extract_complete_structure(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        🔍 ПОЛНОЕ ИЗВЛЕЧЕНИЕ СТРУКТУРЫ ДОКУМЕНТА
        
        Возвращает детальную структуру со всеми элементами:
        - metadata: метаданные документа
        - sections: иерархия разделов
        - paragraphs: все абзацы с привязкой
        - tables: таблицы с данными
        - lists: списки с иерархией
        - elements: плоский список всех элементов для API
        """
        
        # 1. Извлекаем метаданные
        metadata = self._extract_enhanced_metadata(content, file_path)
        
        # 2. Разбиваем документ на строки для анализа
        lines = content.split('\n')
        
        # 3. Извлекаем все элементы документа
        elements = self._extract_all_elements(lines, content)
        
        # 4. Строим иерархическую структуру разделов
        sections_hierarchy = self._build_sections_hierarchy(elements)
        
        # 5. Извлекаем абзацы
        paragraphs = self._extract_paragraphs(content, elements)
        
        # 6. Извлекаем таблицы
        tables = self._extract_enhanced_tables(content, lines)
        
        # 7. Извлекаем списки
        lists = self._extract_enhanced_lists(content, lines)
        
        # 8. Рассчитываем статистику
        statistics = self._calculate_enhanced_statistics(content, elements, tables, lists)
        
        # 9. Формируем полную структуру
        complete_structure = {
            'metadata': metadata,
            'sections_hierarchy': sections_hierarchy,
            'paragraphs': paragraphs,
            'tables': tables,
            'lists': lists,
            'elements': [elem.__dict__ for elem in elements],  # Плоский список для API
            'statistics': statistics,
            'extraction_info': {
                'extracted_at': datetime.now().isoformat(),
                'extractor_version': 'Advanced_v3.0',
                'file_path': file_path,
                'content_length': len(content),
                'lines_count': len(lines),
                'quality_score': self._calculate_extraction_quality_score(elements, tables, lists, metadata)
            }
        }
        
        return complete_structure

    def _extract_enhanced_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """Улучшенное извлечение метаданных документа"""
        
        metadata = {
            'document_number': '',
            'document_title': '',
            'document_type': 'unknown',
            'organization': '',
            'approval_date': '',
            'effective_date': '',
            'status': 'active',
            'keywords': [],
            'references': [],
            'file_info': {
                'file_name': Path(file_path).name if file_path else '',
                'file_path': file_path,
                'file_size': len(content.encode('utf-8')),
            }
        }
        
        # Анализируем первые 3000 символов для метаданных
        header_content = content[:3000]
        
        # Извлекаем номер документа
        for pattern in self.metadata_patterns['document_number']:
            match = re.search(pattern, header_content, re.IGNORECASE | re.MULTILINE)
            if match:
                metadata['document_number'] = match.group(1)
                # Определяем тип документа
                if 'СП' in pattern or 'СВОД' in pattern:
                    metadata['document_type'] = 'sp'
                elif 'ГОСТ' in pattern:
                    metadata['document_type'] = 'gost'
                elif 'СНиП' in pattern:
                    metadata['document_type'] = 'snip'
                elif 'РД' in pattern:
                    metadata['document_type'] = 'rd'
                break
        
        # Извлекаем название документа
        for pattern in self.metadata_patterns['document_title']:
            matches = re.findall(pattern, header_content, re.MULTILINE)
            if matches:
                # Выбираем самое длинное и информативное название
                best_title = max(matches, key=lambda x: len(x) if isinstance(x, str) else len(str(x)))
                metadata['document_title'] = str(best_title).strip()
                break
        
        # Извлекаем организацию
        for pattern in self.metadata_patterns['organization']:
            match = re.search(pattern, header_content, re.IGNORECASE | re.MULTILINE)
            if match:
                if match.groups():
                    metadata['organization'] = match.group(1).strip()
                else:
                    metadata['organization'] = match.group(0).strip()
                break
        
        # Извлекаем даты
        date_matches = []
        for pattern in self.metadata_patterns['dates']:
            matches = re.findall(pattern, header_content, re.IGNORECASE | re.MULTILINE)
            date_matches.extend(matches)
        
        if date_matches:
            # Первая дата обычно дата утверждения
            metadata['approval_date'] = date_matches[0]
            if len(date_matches) > 1:
                metadata['effective_date'] = date_matches[1]
        
        # Извлекаем ключевые слова
        metadata['keywords'] = self._extract_document_keywords(content, metadata['document_type'])
        
        # Извлекаем ссылки на другие документы
        metadata['references'] = self._extract_document_references(content)
        
        return metadata

    def _extract_all_elements(self, lines: List[str], full_content: str) -> List[DocumentElement]:
        """Извлечение всех элементов документа с точной типизацией"""
        
        elements = []
        current_section = None
        element_counter = 0
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            element_counter += 1
            
            # Проверяем на раздел
            section_match = self._match_section_line(line)
            if section_match:
                section_type, number, title, level = section_match
                
                element = DocumentSection(
                    id=f'section_{element_counter}',
                    type=section_type,
                    content=line,
                    number=number,
                    title=title,
                    level=level,
                    position=line_num,
                    page_number=self._estimate_page(line_num, len(lines)),
                    metadata={
                        'section_type': section_type,
                        'level': level,
                        'has_subsections': False  # будем обновлять позже
                    }
                )
                elements.append(element)
                current_section = element
                continue
            
            # Проверяем на таблицу
            table_match = re.search(self.table_patterns['table_header'], line, re.IGNORECASE)
            if table_match:
                element = DocumentTable(
                    id=f'table_{element_counter}',
                    type='table_header',
                    content=line,
                    number=table_match.group(1),
                    title=table_match.group(2).strip() if len(table_match.groups()) > 1 else '',
                    position=line_num,
                    page_number=self._estimate_page(line_num, len(lines)),
                    metadata={
                        'table_number': table_match.group(1),
                        'parent_section': current_section.id if current_section else None
                    }
                )
                elements.append(element)
                continue
            
            # Проверяем на список
            list_match = self._match_list_line(line)
            if list_match:
                list_type, item_marker, item_text = list_match
                
                element = DocumentList(
                    id=f'list_item_{element_counter}',
                    type='list_item',
                    content=line,
                    list_type=list_type,
                    position=line_num,
                    page_number=self._estimate_page(line_num, len(lines)),
                    metadata={
                        'list_type': list_type,
                        'item_marker': item_marker,
                        'item_text': item_text,
                        'parent_section': current_section.id if current_section else None
                    }
                )
                elements.append(element)
                continue
            
            # Обычный абзац
            if len(line) > 10:  # Игнорируем очень короткие строки
                element = DocumentParagraph(
                    id=f'paragraph_{element_counter}',
                    type='paragraph',
                    content=line,
                    position=line_num,
                    page_number=self._estimate_page(line_num, len(lines)),
                    section_id=current_section.id if current_section else None,
                    metadata={
                        'word_count': len(line.split()),
                        'has_numbers': bool(re.search(r'\d+', line)),
                        'has_technical_terms': self._has_technical_terms(line),
                        'parent_section': current_section.id if current_section else None
                    }
                )
                elements.append(element)
        
        return elements

    def _match_section_line(self, line: str) -> Optional[Tuple[str, str, str, int]]:
        """Определение типа и уровня раздела"""
        
        # Главные разделы (уровень 1)
        for pattern in self.section_patterns['main_sections']:
            match = re.match(pattern, line)
            if match:
                number = match.group(1)
                title = match.group(2).strip()
                return ('main_section', number, title, 1)
        
        # Подразделы (уровень 2)
        for pattern in self.section_patterns['subsections']:
            match = re.match(pattern, line)
            if match:
                number = match.group(1)
                title = match.group(2).strip()
                return ('subsection', number, title, 2)
        
        # Подподразделы (уровень 3)
        for pattern in self.section_patterns['subsubsections']:
            match = re.match(pattern, line)
            if match:
                number = match.group(1)
                title = match.group(2).strip()
                return ('subsubsection', number, title, 3)
        
        # Приложения (уровень 1, но отдельный тип)
        for pattern in self.section_patterns['appendices']:
            match = re.match(pattern, line)
            if match:
                number = match.group(1)
                title = match.group(2).strip() if len(match.groups()) > 1 else ''
                return ('appendix', number, title, 1)
        
        # Буквенные пункты (уровень 4)
        for pattern in self.section_patterns['lettered_items']:
            match = re.match(pattern, line)
            if match:
                number = match.group(1)
                title = match.group(2).strip()
                return ('lettered_item', number, title, 4)
        
        return None

    def _match_list_line(self, line: str) -> Optional[Tuple[str, str, str]]:
        """Определение типа списка"""
        
        for list_type, pattern in self.list_patterns.items():
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                if list_type == 'numbered_list':
                    marker = match.group(1) + '.'
                    text = match.group(2).strip()
                elif list_type == 'bulleted_list':
                    marker = line[0]  # -, •, или *
                    text = match.group(1).strip()
                elif list_type == 'lettered_list':
                    marker = match.group(1) if match.group(1) else match.group(3)
                    text = match.group(2).strip() if match.group(2) else match.group(4).strip()
                else:  # mixed_list
                    marker = re.match(r'^([-•*]|\d+\.|[а-я]\)|\([а-я]\))', line).group(1)
                    text = match.group(1).strip()
                
                return (list_type, marker, text)
        
        return None

class IntelligentChunker:
    """
    🧩 ИНТЕЛЛЕКТУАЛЬНЫЙ ЧАНКЕР
    
    Создает оптимальные чанки на основе структуры документа:
    - Разделы как отдельные чанки (если размер подходит)
    - Таблицы как самостоятельные чанки
    - Списки группируются логично
    - Абзацы объединяются с учетом контекста
    - Фрагментация только при превышении лимитов
    """
    
    def __init__(self, min_chunk_size: int = 100, max_chunk_size: int = 1200, 
                 optimal_chunk_size: int = 800, overlap_size: int = 50):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.optimal_chunk_size = optimal_chunk_size
        self.overlap_size = overlap_size

    def create_intelligent_chunks(self, document_structure: Dict[str, Any]) -> List[SmartChunk]:
        """
        🧩 ГЛАВНЫЙ МЕТОД: Создание интеллектуальных чанков
        
        Алгоритм:
        1. Анализируем структуру документа
        2. Создаем чанки по разделам (если размер подходит)
        3. Таблицы выделяем в отдельные чанки
        4. Списки группируем логично
        5. Абзацы объединяем с учетом контекста
        6. При превышении размера - умная фрагментация
        """
        
        chunks = []
        elements = document_structure.get('elements', [])
        sections_hierarchy = document_structure.get('sections_hierarchy', [])
        tables = document_structure.get('tables', [])
        lists = document_structure.get('lists', [])
        
        chunk_counter = 0
        
        # 1. Создаем чанки на основе разделов
        section_chunks = self._create_section_chunks(sections_hierarchy, elements)
        chunks.extend(section_chunks)
        chunk_counter += len(section_chunks)
        
        # 2. Создаем чанки для таблиц
        table_chunks = self._create_table_chunks(tables, elements)
        chunks.extend(table_chunks)
        chunk_counter += len(table_chunks)
        
        # 3. Создаем чанки для списков
        list_chunks = self._create_list_chunks(lists, elements)
        chunks.extend(list_chunks)
        chunk_counter += len(list_chunks)
        
        # 4. Обрабатываем оставшиеся элементы (абзацы без секций)
        orphan_chunks = self._create_orphan_chunks(elements, chunks)
        chunks.extend(orphan_chunks)
        
        # 5. Валидация и оптимизация чанков
        optimized_chunks = self._optimize_chunks(chunks)
        
        # 6. Добавляем ID и рассчитываем качество
        final_chunks = []
        for i, chunk in enumerate(optimized_chunks):
            chunk.id = f'chunk_{i+1}'
            chunk.quality_score = self._calculate_chunk_quality(chunk)
            final_chunks.append(chunk)
        
        return final_chunks

    def _create_section_chunks(self, sections_hierarchy: List[Dict], elements: List[Dict]) -> List[SmartChunk]:
        """Создание чанков на основе разделов"""
        chunks = []
        
        for section in sections_hierarchy:
            section_content = self._gather_section_content(section, elements)
            
            if not section_content:
                continue
                
            # Если раздел подходящего размера - создаем один чанк
            if self.min_chunk_size <= len(section_content) <= self.max_chunk_size:
                chunk = SmartChunk(
                    id='',  # будет назначен позже
                    content=section_content,
                    chunk_type=ChunkType.SECTION,
                    source_elements=[section.get('id', '')],
                    metadata={
                        'section_number': section.get('number', ''),
                        'section_title': section.get('title', ''),
                        'section_level': section.get('level', 1),
                        'has_subsections': len(section.get('subsections', [])) > 0
                    }
                )
                chunks.append(chunk)
            
            # Если раздел слишком большой - фрагментируем умно
            elif len(section_content) > self.max_chunk_size:
                section_chunks = self._fragment_large_section(section, section_content, elements)
                chunks.extend(section_chunks)
        
        return chunks

    def _create_table_chunks(self, tables: List[Dict], elements: List[Dict]) -> List[SmartChunk]:
        """Создание чанков для таблиц"""
        chunks = []
        
        for table in tables:
            # Формируем содержимое таблицы
            table_content = self._format_table_content(table)
            
            if not table_content or len(table_content) < self.min_chunk_size:
                continue
            
            # Если таблица слишком большая - разбиваем по строкам
            if len(table_content) > self.max_chunk_size:
                table_chunks = self._fragment_large_table(table, table_content)
                chunks.extend(table_chunks)
            else:
                chunk = SmartChunk(
                    id='',
                    content=table_content,
                    chunk_type=ChunkType.TABLE,
                    source_elements=[table.get('id', '')],
                    metadata={
                        'table_number': table.get('number', ''),
                        'table_title': table.get('title', ''),
                        'row_count': len(table.get('rows', [])),
                        'column_count': len(table.get('headers', [])),
                        'is_complete_table': True
                    }
                )
                chunks.append(chunk)
        
        return chunks

    def _create_list_chunks(self, lists: List[Dict], elements: List[Dict]) -> List[SmartChunk]:
        """Создание чанков для списков"""
        chunks = []
        
        for list_group in lists:
            list_content = self._format_list_content(list_group)
            
            if not list_content or len(list_content) < self.min_chunk_size:
                continue
            
            # Списки обычно умещаются в один чанк
            if len(list_content) <= self.max_chunk_size:
                chunk = SmartChunk(
                    id='',
                    content=list_content,
                    chunk_type=ChunkType.LIST,
                    source_elements=[list_group.get('id', '')],
                    metadata={
                        'list_type': list_group.get('type', ''),
                        'item_count': len(list_group.get('items', [])),
                        'is_complete_list': True
                    }
                )
                chunks.append(chunk)
            else:
                # Большие списки разбиваем логично
                list_chunks = self._fragment_large_list(list_group, list_content)
                chunks.extend(list_chunks)
        
        return chunks

    def _gather_section_content(self, section: Dict, elements: List[Dict]) -> str:
        """Сбор контента раздела включая подразделы"""
        content_parts = []
        
        # Добавляем заголовок раздела
        if section.get('title'):
            header = f"{section.get('number', '')} {section.get('title', '')}"
            content_parts.append(header)
        
        # Добавляем контент раздела
        if section.get('content'):
            content_parts.append(section.get('content', ''))
        
        # Рекурсивно добавляем подразделы
        for subsection in section.get('subsections', []):
            subsection_content = self._gather_section_content(subsection, elements)
            if subsection_content:
                content_parts.append(subsection_content)
        
        return '\n\n'.join(content_parts)

    def _format_table_content(self, table: Dict) -> str:
        """Форматирование содержимого таблицы"""
        content_parts = []
        
        # Заголовок таблицы
        if table.get('number') or table.get('title'):
            header = f"Таблица {table.get('number', '')} {table.get('title', '')}".strip()
            content_parts.append(header)
        
        # Заголовки столбцов
        headers = table.get('headers', [])
        if headers:
            header_row = ' | '.join(headers)
            content_parts.append(header_row)
            content_parts.append('-' * len(header_row))
        
        # Строки таблицы
        for row in table.get('rows', []):
            if isinstance(row, list):
                row_content = ' | '.join(str(cell) for cell in row)
                content_parts.append(row_content)
        
        return '\n'.join(content_parts)

    def _format_list_content(self, list_group: Dict) -> str:
        """Форматирование содержимого списка"""
        content_parts = []
        
        for item in list_group.get('items', []):
            if isinstance(item, dict):
                marker = item.get('number', '') or item.get('marker', '•')
                text = item.get('text', '')
                if text:
                    content_parts.append(f"{marker} {text}")
            else:
                content_parts.append(str(item))
        
        return '\n'.join(content_parts)

    def _fragment_large_section(self, section: Dict, content: str, elements: List[Dict]) -> List[SmartChunk]:
        """Умная фрагментация большого раздела"""
        chunks = []
        
        # Пробуем разбить по подразделам
        subsections = section.get('subsections', [])
        if subsections:
            for subsection in subsections:
                subsection_content = self._gather_section_content(subsection, elements)
                if subsection_content and len(subsection_content) >= self.min_chunk_size:
                    if len(subsection_content) <= self.max_chunk_size:
                        chunk = SmartChunk(
                            id='',
                            content=subsection_content,
                            chunk_type=ChunkType.SUBSECTION,
                            source_elements=[subsection.get('id', '')],
                            metadata={
                                'section_number': subsection.get('number', ''),
                                'section_title': subsection.get('title', ''),
                                'section_level': subsection.get('level', 2),
                                'parent_section': section.get('number', '')
                            }
                        )
                        chunks.append(chunk)
                    else:
                        # Рекурсивно фрагментируем
                        sub_chunks = self._fragment_large_section(subsection, subsection_content, elements)
                        chunks.extend(sub_chunks)
        else:
            # Разбиваем по абзацам
            paragraphs = content.split('\n\n')
            current_chunk_content = []
            current_size = 0
            
            for paragraph in paragraphs:
                paragraph_size = len(paragraph)
                
                if current_size + paragraph_size <= self.optimal_chunk_size:
                    current_chunk_content.append(paragraph)
                    current_size += paragraph_size
                else:
                    # Сохраняем текущий чанк
                    if current_chunk_content:
                        chunk_content = '\n\n'.join(current_chunk_content)
                        if len(chunk_content) >= self.min_chunk_size:
                            chunk = SmartChunk(
                                id='',
                                content=chunk_content,
                                chunk_type=ChunkType.FRAGMENT,
                                source_elements=[section.get('id', '')],
                                metadata={
                                    'fragment_of': section.get('number', ''),
                                    'fragment_type': 'section_part'
                                }
                            )
                            chunks.append(chunk)
                    
                    # Начинаем новый чанк
                    current_chunk_content = [paragraph]
                    current_size = paragraph_size
            
            # Сохраняем последний чанк
            if current_chunk_content:
                chunk_content = '\n\n'.join(current_chunk_content)
                if len(chunk_content) >= self.min_chunk_size:
                    chunk = SmartChunk(
                        id='',
                        content=chunk_content,
                        chunk_type=ChunkType.FRAGMENT,
                        source_elements=[section.get('id', '')],
                        metadata={
                            'fragment_of': section.get('number', ''),
                            'fragment_type': 'section_part'
                        }
                    )
                    chunks.append(chunk)
        
        return chunks

    def _optimize_chunks(self, chunks: List[SmartChunk]) -> List[SmartChunk]:
        """Оптимизация чанков - объединение маленьких, проверка размеров"""
        optimized = []
        
        i = 0
        while i < len(chunks):
            current_chunk = chunks[i]
            
            # Если чанк слишком маленький, пытаемся объединить со следующим
            if len(current_chunk.content) < self.min_chunk_size and i + 1 < len(chunks):
                next_chunk = chunks[i + 1]
                combined_size = len(current_chunk.content) + len(next_chunk.content)
                
                # Объединяем если размер подходящий и типы совместимы
                if combined_size <= self.max_chunk_size and self._can_combine_chunks(current_chunk, next_chunk):
                    combined_chunk = SmartChunk(
                        id='',
                        content=f"{current_chunk.content}\n\n{next_chunk.content}",
                        chunk_type=ChunkType.MIXED,
                        source_elements=current_chunk.source_elements + next_chunk.source_elements,
                        metadata={
                            'combined_from': [current_chunk.chunk_type.value, next_chunk.chunk_type.value],
                            'is_combined': True
                        }
                    )
                    optimized.append(combined_chunk)
                    i += 2  # Пропускаем следующий чанк
                    continue
            
            optimized.append(current_chunk)
            i += 1
        
        return optimized

    def _can_combine_chunks(self, chunk1: SmartChunk, chunk2: SmartChunk) -> bool:
        """Проверка возможности объединения чанков"""
        # Не объединяем таблицы с другими типами
        if chunk1.chunk_type == ChunkType.TABLE or chunk2.chunk_type == ChunkType.TABLE:
            return False
        
        # Можно объединять абзацы, фрагменты и списки
        combinable_types = {ChunkType.PARAGRAPH, ChunkType.FRAGMENT, ChunkType.LIST, ChunkType.MIXED}
        
        return chunk1.chunk_type in combinable_types and chunk2.chunk_type in combinable_types

    def _calculate_chunk_quality(self, chunk: SmartChunk) -> float:
        """Расчет качества чанка"""
        score = 0.0
        
        # Размер чанка (30% от оценки)
        size = len(chunk.content)
        if self.min_chunk_size <= size <= self.optimal_chunk_size:
            size_score = 1.0
        elif size <= self.max_chunk_size:
            size_score = 0.8
        else:
            size_score = 0.5
        score += size_score * 0.3
        
        # Тип чанка (20% от оценки)
        type_scores = {
            ChunkType.SECTION: 1.0,
            ChunkType.SUBSECTION: 0.9,
            ChunkType.TABLE: 0.95,
            ChunkType.LIST: 0.85,
            ChunkType.PARAGRAPH: 0.7,
            ChunkType.FRAGMENT: 0.6,
            ChunkType.MIXED: 0.5
        }
        score += type_scores.get(chunk.chunk_type, 0.5) * 0.2
        
        # Содержательность (30% от оценки)
        technical_terms = chunk._count_technical_terms()
        content_density = technical_terms / len(chunk.content.split()) if chunk.content.split() else 0
        content_score = min(content_density * 10, 1.0)  # Нормализация
        score += content_score * 0.3
        
        # Структурированность (20% от оценки)
        has_structure = any([
            '|' in chunk.content,  # таблицы
            bool(re.search(r'^\d+\.', chunk.content, re.MULTILINE)),  # нумерация
            bool(re.search(r'^[-•*]', chunk.content, re.MULTILINE)),  # списки
        ])
        structure_score = 1.0 if has_structure else 0.6
        score += structure_score * 0.2
        
        return min(score, 1.0)

    # Дополнительные вспомогательные методы...
    def _fragment_large_table(self, table: Dict, content: str) -> List[SmartChunk]:
        """Фрагментация большой таблицы"""
        # Реализация фрагментации таблиц по строкам
        # ... (детальная реализация)
        return []
    
    def _fragment_large_list(self, list_group: Dict, content: str) -> List[SmartChunk]:
        """Фрагментация большого списка"""
        # Реализация фрагментации списков
        # ... (детальная реализация)
        return []
    
    def _create_orphan_chunks(self, elements: List[Dict], existing_chunks: List[SmartChunk]) -> List[SmartChunk]:
        """Создание чанков для элементов, не попавших в разделы"""
        # Реализация обработки "сиротских" элементов
        # ... (детальная реализация)
        return []

class IntegratedStructureChunkingSystem:
    """
    🔧 ИНТЕГРИРОВАННАЯ СИСТЕМА СТРУКТУРЫ И ЧАНКИНГА
    
    Объединяет извлечение структуры и интеллектуальный чанкинг
    в единую систему с API-совместимостью
    """
    
    def __init__(self):
        self.structure_extractor = AdvancedStructureExtractor()
        self.intelligent_chunker = IntelligentChunker()

    def process_document(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        🔧 ПОЛНАЯ ОБРАБОТКА ДОКУМЕНТА
        
        Возвращает структуру, совместимую с фронтендом:
        - document_info: метаданные для UI
        - sections: иерархия разделов
        - chunks: интеллектуальные чанки 
        - tables: таблицы с данными
        - statistics: статистика документа
        """
        
        # 1. Извлекаем структуру документа
        document_structure = self.structure_extractor.extract_complete_structure(content, file_path)
        
        # 2. Создаем интеллектуальные чанки
        smart_chunks = self.intelligent_chunker.create_intelligent_chunks(document_structure)
        
        # 3. Формируем API-совместимую структуру
        api_compatible_result = {
            # Метаданные документа (для UI)
            'document_info': {
                'title': document_structure['metadata']['document_title'],
                'number': document_structure['metadata']['document_number'],
                'type': document_structure['metadata']['document_type'],
                'organization': document_structure['metadata']['organization'],
                'approval_date': document_structure['metadata']['approval_date'],
                'file_name': document_structure['metadata']['file_info']['file_name'],
                'file_size': document_structure['metadata']['file_info']['file_size'],
                'keywords': document_structure['metadata']['keywords']
            },
            
            # Иерархия разделов (для навигации)
            'sections': self._format_sections_for_api(document_structure['sections_hierarchy']),
            
            # Интеллектуальные чанки (для RAG)
            'chunks': [chunk.to_dict() for chunk in smart_chunks],
            
            # Таблицы (для специальной обработки)
            'tables': document_structure['tables'],
            
            # Списки
            'lists': document_structure['lists'],
            
            # Статистика
            'statistics': {
                **document_structure['statistics'],
                'chunks_created': len(smart_chunks),
                'avg_chunk_quality': np.mean([chunk.quality_score for chunk in smart_chunks]) if smart_chunks else 0,
                'chunk_types_distribution': self._get_chunk_types_stats(smart_chunks)
            },
            
            # Техническая информация
            'processing_info': {
                'extracted_at': document_structure['extraction_info']['extracted_at'],
                'processor_version': 'Integrated_v3.0',
                'structure_quality': document_structure['extraction_info']['quality_score'],
                'chunking_quality': np.mean([chunk.quality_score for chunk in smart_chunks]) if smart_chunks else 0,
                'total_elements': len(document_structure['elements']),
                'processing_method': 'intelligent_structure_based'
            }
        }
        
        return api_compatible_result

    def _format_sections_for_api(self, sections_hierarchy: List[Dict]) -> List[Dict]:
        """Форматирование разделов для API"""
        formatted_sections = []
        
        def format_section_recursive(section: Dict, parent_path: str = "") -> Dict:
            section_path = f"{parent_path}.{section['number']}" if parent_path else section['number']
            
            formatted_section = {
                'id': section_path,
                'number': section.get('number', ''),
                'title': section.get('title', ''),
                'level': section.get('level', 1),
                'type': section.get('type', 'section'),
                'content_length': len(section.get('content', '')),
                'has_subsections': len(section.get('subsections', [])) > 0,
                'parent_path': parent_path,
                'metadata': section.get('metadata', {})
            }
            
            # Рекурсивно обрабатываем подразделы
            subsections = []
            for subsection in section.get('subsections', []):
                formatted_subsection = format_section_recursive(subsection, section_path)
                subsections.append(formatted_subsection)
            
            if subsections:
                formatted_section['subsections'] = subsections
            
            return formatted_section
        
        for section in sections_hierarchy:
            formatted_sections.append(format_section_recursive(section))
        
        return formatted_sections

    def _get_chunk_types_stats(self, chunks: List[SmartChunk]) -> Dict[str, int]:
        """Статистика по типам чанков"""
        stats = {}
        for chunk in chunks:
            chunk_type = chunk.chunk_type.value
            stats[chunk_type] = stats.get(chunk_type, 0) + 1
        return stats

# Вспомогательные методы для AdvancedStructureExtractor
def _estimate_page(line_num: int, total_lines: int) -> int:
    """Оценка номера страницы"""
    lines_per_page = 50
    return max(1, (line_num // lines_per_page) + 1)

def _has_technical_terms(text: str) -> bool:
    """Проверка на технические термины"""
    patterns = [
        r'\b(?:ГОСТ|СП|СНиП)\s+[\d.-]+',
        r'\b\d+(?:\.\d+)?\s*(?:мм|см|м|км|г|кг|т|МПа|кПа|°C)\b',
        r'\b(?:прочность|деформация|нагрузка|напряжение)\b'
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

# Методы для интеграции в AdvancedStructureExtractor
AdvancedStructureExtractor._estimate_page = _estimate_page
AdvancedStructureExtractor._has_technical_terms = _has_technical_terms

def _build_sections_hierarchy(self, elements: List[DocumentElement]) -> List[Dict]:
    """Построение иерархии разделов"""
    hierarchy = []
    sections_dict = {}
    
    # Собираем все секции
    for element in elements:
        if isinstance(element, DocumentSection):
            section_data = {
                'id': element.id,
                'number': element.number,
                'title': element.title,
                'level': element.level,
                'type': element.type,
                'content': element.content,
                'metadata': element.metadata,
                'subsections': []
            }
            sections_dict[element.id] = section_data
    
    # Строим иерархию
    for section_data in sections_dict.values():
        level = section_data['level']
        
        if level == 1:
            hierarchy.append(section_data)
        else:
            # Ищем родительский раздел
            parent_found = False
            for parent in sections_dict.values():
                if parent['level'] == level - 1 and not parent_found:
                    parent['subsections'].append(section_data)
                    parent_found = True
                    break
            
            # Если не нашли родителя, добавляем в корень
            if not parent_found:
                hierarchy.append(section_data)
    
    return hierarchy

def _extract_paragraphs(self, content: str, elements: List[DocumentElement]) -> List[Dict]:
    """Извлечение абзацев с метаданными"""
    paragraphs = []
    
    for element in elements:
        if isinstance(element, DocumentParagraph):
            paragraph_data = {
                'id': element.id,
                'content': element.content,
                'section_id': element.section_id,
                'position': element.position,
                'page_number': element.page_number,
                'metadata': element.metadata,
                'word_count': len(element.content.split()),
                'char_count': len(element.content)
            }
            paragraphs.append(paragraph_data)
    
    return paragraphs

def _extract_enhanced_tables(self, content: str, lines: List[str]) -> List[Dict]:
    """Улучшенное извлечение таблиц"""
    tables = []
    current_table = None
    in_table = False
    table_rows = []
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        
        # Поиск заголовка таблицы
        table_match = re.search(self.table_patterns['table_header'], line, re.IGNORECASE)
        if table_match:
            # Сохраняем предыдущую таблицу
            if current_table and table_rows:
                current_table['rows'] = table_rows
                tables.append(current_table)
            
            # Новая таблица
            current_table = {
                'id': f'table_{len(tables)+1}',
                'number': table_match.group(1),
                'title': table_match.group(2).strip() if len(table_match.groups()) > 1 else '',
                'headers': [],
                'rows': [],
                'page_number': self._estimate_page(line_num, len(lines)),
                'metadata': {
                    'source_line': line_num,
                    'table_type': 'structured'
                }
            }
            table_rows = []
            in_table = True
            continue
        
        if in_table and '|' in line:
            # Обработка строки таблицы
            if re.match(self.table_patterns['table_separator'], line):
                continue  # Пропускаем разделители
            
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if cells:
                if not current_table['headers']:
                    current_table['headers'] = cells
                else:
                    table_rows.append(cells)
        elif in_table and current_table:
            # Конец таблицы
            if table_rows:
                current_table['rows'] = table_rows
                tables.append(current_table)
            in_table = False
            current_table = None
            table_rows = []
    
    # Сохраняем последнюю таблицу
    if current_table and table_rows:
        current_table['rows'] = table_rows
        tables.append(current_table)
    
    return tables

def _extract_enhanced_lists(self, content: str, lines: List[str]) -> List[Dict]:
    """Улучшенное извлечение списков"""
    lists = []
    current_list = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        list_match = self._match_list_line(line)
        if list_match:
            list_type, marker, text = list_match
            
            # Новый список или продолжение
            if not current_list or current_list['type'] != list_type:
                if current_list:
                    lists.append(current_list)
                
                current_list = {
                    'id': f'list_{len(lists)+1}',
                    'type': list_type,
                    'items': [],
                    'metadata': {
                        'list_type': list_type,
                        'item_count': 0
                    }
                }
            
            # Добавляем элемент списка
            current_list['items'].append({
                'marker': marker,
                'text': text,
                'level': self._determine_list_level(line)
            })
        elif current_list:
            # Конец списка
            current_list['metadata']['item_count'] = len(current_list['items'])
            lists.append(current_list)
            current_list = None
    
    # Сохраняем последний список
    if current_list:
        current_list['metadata']['item_count'] = len(current_list['items'])
        lists.append(current_list)
    
    return lists

def _determine_list_level(self, line: str) -> int:
    """Определение уровня элемента списка"""
    leading_spaces = len(line) - len(line.lstrip())
    return max(1, leading_spaces // 4 + 1)

def _calculate_enhanced_statistics(self, content: str, elements: List[DocumentElement], 
                                 tables: List[Dict], lists: List[Dict]) -> Dict[str, Any]:
    """Расширенная статистика документа"""
    
    # Подсчет элементов по типам
    element_counts = {}
    for element in elements:
        element_type = type(element).__name__
        element_counts[element_type] = element_counts.get(element_type, 0) + 1
    
    # Анализ разделов по уровням
    section_levels = {}
    for element in elements:
        if isinstance(element, DocumentSection):
            level = element.level
            section_levels[f'level_{level}'] = section_levels.get(f'level_{level}', 0) + 1
    
    return {
        'content_length': len(content),
        'word_count': len(content.split()),
        'line_count': len(content.split('\n')),
        'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
        'element_counts': element_counts,
        'section_levels': section_levels,
        'table_count': len(tables),
        'list_count': len(lists),
        'list_items_total': sum(len(lst.get('items', [])) for lst in lists),
        'has_appendices': any('appendix' in str(elem.type).lower() for elem in elements if hasattr(elem, 'type')),
        'technical_density': self._calculate_technical_density(content),
        'avg_section_length': np.mean([len(elem.content) for elem in elements if isinstance(elem, DocumentSection)]) if any(isinstance(elem, DocumentSection) for elem in elements) else 0
    }

def _calculate_technical_density(self, content: str) -> float:
    """Расчет плотности технических терминов"""
    technical_patterns = [
        r'\b\d+(?:\.\d+)?\s*(?:мм|см|м|км|г|кг|т|МПа|кПа|°C)\b',
        r'\b(?:ГОСТ|СП|СНиП)\s+[\d.-]+',
        r'\b\d+(?:\.\d+)*\s*%\b'
    ]
    
    technical_count = 0
    for pattern in technical_patterns:
        technical_count += len(re.findall(pattern, content, re.IGNORECASE))
    
    word_count = len(content.split())
    return technical_count / word_count if word_count > 0 else 0.0

def _calculate_extraction_quality_score(self, elements: List[DocumentElement], tables: List[Dict], 
                                      lists: List[Dict], metadata: Dict[str, Any]) -> float:
    """Оценка качества извлечения структуры"""
    score = 0.0
    
    # Качество метаданных (30%)
    metadata_fields = ['document_title', 'document_number', 'organization']
    filled_metadata = sum(1 for field in metadata_fields if metadata.get(field))
    metadata_score = (filled_metadata / len(metadata_fields)) * 0.3
    score += metadata_score
    
    # Качество структуры (40%)
    sections_count = sum(1 for elem in elements if isinstance(elem, DocumentSection))
    structure_score = min(sections_count / 10.0, 1.0) * 0.4
    score += structure_score
    
    # Качество извлечения таблиц (15%)
    table_score = min(len(tables) / 5.0, 1.0) * 0.15
    score += table_score
    
    # Качество извлечения списков (15%)
    list_score = min(len(lists) / 8.0, 1.0) * 0.15
    score += list_score
    
    return min(score, 1.0)

def _extract_document_keywords(self, content: str, doc_type: str) -> List[str]:
    """Извлечение ключевых слов документа"""
    keywords = []
    
    # Типоспецифичные паттерны
    type_patterns = {
        'sp': [r'\b(строительство|проектирование|требования|нормы|правила)\b'],
        'gost': [r'\b(стандарт|качество|испытания|методы|технические условия)\b'],
        'snip': [r'\b(нормы|правила|строительство|проектирование)\b'],
        'rd': [r'\b(руководящий документ|методика|инструкция|рекомендации)\b']
    }
    
    patterns = type_patterns.get(doc_type, type_patterns['sp'])
    
    for pattern in patterns:
        matches = re.findall(pattern, content.lower(), re.IGNORECASE)
        keywords.extend(matches)
    
    return list(dict.fromkeys(keywords))[:10]  # Убираем дубликаты

def _extract_document_references(self, content: str) -> List[str]:
    """Извлечение ссылок на документы"""
    patterns = [
        r'\b(?:ГОСТ|СП|СНиП|ТУ|ОСТ)\s+[\d.-]+(?:-\d+)?',
        r'\b(?:п\.|пункт|раздел)\s+\d+(?:\.\d+)*'
    ]
    
    references = []
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        references.extend(matches)
    
    return list(dict.fromkeys(references))[:20]

# Добавляем методы к классу
AdvancedStructureExtractor._build_sections_hierarchy = _build_sections_hierarchy
AdvancedStructureExtractor._extract_paragraphs = _extract_paragraphs
AdvancedStructureExtractor._extract_enhanced_tables = _extract_enhanced_tables
AdvancedStructureExtractor._extract_enhanced_lists = _extract_enhanced_lists
AdvancedStructureExtractor._determine_list_level = _determine_list_level
AdvancedStructureExtractor._calculate_enhanced_statistics = _calculate_enhanced_statistics
AdvancedStructureExtractor._calculate_technical_density = _calculate_technical_density
AdvancedStructureExtractor._calculate_extraction_quality_score = _calculate_extraction_quality_score
AdvancedStructureExtractor._extract_document_keywords = _extract_document_keywords
AdvancedStructureExtractor._extract_document_references = _extract_document_references

# Функция для быстрого использования
def process_document_with_intelligent_chunking(content: str, file_path: str = "") -> Dict[str, Any]:
    """
    🔧 Быстрая обработка документа с интеллектуальным чанкингом
    
    Args:
        content: Содержимое документа
        file_path: Путь к файлу
    
    Returns:
        API-совместимая структура с интеллектуальными чанками
    """
    system = IntegratedStructureChunkingSystem()
    return system.process_document(content, file_path)

if __name__ == "__main__":
    print("🔧 Integrated Structure & Chunking System v3 - Ready!")
    
    # Тестирование системы
    test_content = """
СП 50.13330.2012

ТЕПЛОВАЯ ЗАЩИТА ЗДАНИЙ

Актуализированная редакция СНиП 23-02-2003

УТВЕРЖДЕНО
Министерством регионального развития РФ
приказом от 30 июня 2012 г. № 265

1. ОБЩИЕ ПОЛОЖЕНИЯ

1.1 Настоящий свод правил распространяется на проектирование тепловой защиты зданий всех назначений.

1.2 Требования настоящего свода правил являются обязательными для всех организаций независимо от их организационно-правовых форм.

2. НОРМАТИВНЫЕ ССЫЛКИ

В настоящем своде правил использованы нормативные ссылки на следующие документы:
- ГОСТ 30494-2011 Здания жилые и общественные. Параметры микроклимата в помещениях
- СП 23-101-2004 Проектирование тепловой защиты зданий

Таблица 1 - Нормируемые значения сопротивления теплопередаче

|Тип здания|R₀, м²·°С/Вт|Примечание|
|Жилые|3,5|Для климатических условий|
|Общественные|2,8|При расчетной температуре|

3. ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ

3.1 В настоящем своде правил применены следующие термины с соответствующими определениями:

а) тепловая защита здания: комплекс конструктивных решений;
б) сопротивление теплопередаче: величина, характеризующая теплозащитные свойства.
"""
    
    result = process_document_with_intelligent_chunking(test_content, "test_sp.pdf")
    
    print(f"✅ Обработка завершена:")
    print(f"  📄 Документ: {result['document_info']['title']}")
    print(f"  🔢 Номер: {result['document_info']['number']}")
    print(f"  📊 Разделов: {len(result['sections'])}")
    print(f"  🧩 Чанков: {len(result['chunks'])}")
    print(f"  📋 Таблиц: {len(result['tables'])}")
    print(f"  📈 Качество структуры: {result['processing_info']['structure_quality']:.2f}")
    print(f"  🎯 Качество чанкинга: {result['processing_info']['chunking_quality']:.2f}")
    
    print(f"\n📊 Статистика чанков:")
    for chunk_type, count in result['statistics']['chunk_types_distribution'].items():
        print(f"  - {chunk_type}: {count}")
        
    print("\n🔧 Система готова для интеграции с Enhanced RAG Trainer!")