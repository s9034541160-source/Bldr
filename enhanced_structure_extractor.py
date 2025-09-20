#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 ENHANCED STRUCTURE EXTRACTOR V3
==================================
Детальное извлечение структуры документа с полными метаданными

УЛУЧШЕНИЯ СТРУКТУРНОГО АНАЛИЗА:
✅ Детальное извлечение всех абзацев с иерархией
✅ Точное определение пунктов и подпунктов (1.1, 1.2.1, и т.д.)
✅ Извлечение таблиц с содержимым и метаданными
✅ Обнаружение списков (маркированные, нумерованные, многоуровневые)
✅ Извлечение названия документа и номера СП/ГОСТ/СНиП
✅ Определение организации-разработчика и даты утверждения
✅ Совместимость с существующим фронтом
✅ JSON-структура с полными метаданными
"""

import re
import json
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

@dataclass
class DocumentSection:
    """Структура секции документа"""
    number: str
    title: str
    level: int
    content: str
    subsections: List['DocumentSection'] = field(default_factory=list)
    paragraphs: List[str] = field(default_factory=list)
    tables: List[Dict] = field(default_factory=list)
    lists: List[Dict] = field(default_factory=list)
    page_numbers: List[int] = field(default_factory=list)

@dataclass
class DocumentTable:
    """Структура таблицы документа"""
    number: str
    title: str
    headers: List[str]
    rows: List[List[str]]
    caption: str = ""
    page_number: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DocumentList:
    """Структура списка документа"""
    list_type: str  # 'numbered', 'bulleted', 'multilevel'
    items: List[Dict]
    level: int = 1
    parent_section: str = ""

class EnhancedStructureExtractor:
    """
    🔍 Улучшенный экстрактор структуры документов
    
    Извлекает детальную структуру с полными метаданными:
    - Все абзацы с иерархией
    - Пункты и подпункты (1.1, 1.2.1 и т.д.)
    - Таблицы с содержимым
    - Списки всех типов
    - Метаданные документа (название, номер, дата, организация)
    """
    
    def __init__(self):
        # Паттерны для различных типов разделов
        self.section_patterns = {
            'numbered': [
                r'^(\d+(?:\.\d+)*)\s+([А-ЯЁ][^.\n]{5,100})$',  # 1. ОСНОВНЫЕ ПОЛОЖЕНИЯ
                r'^(\d+(?:\.\d+)*)\s+([А-Яа-яё\s]{10,80}[^.]?)$',  # 1.1 Общие требования
                r'^(\d+(?:\.\d+)*\.?\s*)([А-ЯЁ\s]{5,60})$',  # 1.1. ТРЕБОВАНИЯ
            ],
            'lettered': [
                r'^([а-я]\)|\([а-я]\))\s+([А-Яа-яё\s]{5,80})$',  # а) требования
                r'^([А-Я]\)|\([А-Я]\))\s+([А-Яа-яё\s]{5,80})$',  # А) ТРЕБОВАНИЯ
            ],
            'appendix': [
                r'^(Приложение\s+[А-Я])\s*\.?\s*([А-Яа-яё\s]{5,100})$',
                r'^(ПРИЛОЖЕНИЕ\s+[А-Я])\s*\.?\s*([А-ЯЁ\s]{5,100})$',
            ]
        }
        
        # Паттерны для таблиц
        self.table_patterns = {
            'table_start': r'(?:Таблица|ТАБЛИЦА)\s+(\d+(?:\.\d+)*)\s*[-–—]?\s*([^\n]{0,80})',
            'table_row': r'\|([^|]+)\|',
            'table_separator': r'\|[-\s:|]+\|',
        }
        
        # Паттерны для списков
        self.list_patterns = {
            'numbered': r'^(\d+(?:\.\d+)*)\.\s+(.+)$',
            'bulleted': r'^[-•*]\s+(.+)$',
            'lettered': r'^[а-я]\)\s+(.+)$|^\([а-я]\)\s+(.+)$',
        }
        
        # Паттерны для метаданных документа
        self.metadata_patterns = {
            'document_number': [
                r'(?:СП|СВОД\s+ПРАВИЛ)\s+(\d+(?:\.\d+)*(?:-\d+)?)',
                r'(?:ГОСТ)\s+(\d+(?:\.\d+)*(?:-\d+)?)',
                r'(?:СНиП)\s+([\d.-]+)',
                r'№\s*([А-Я0-9.-]+)',
            ],
            'document_title': [
                r'^([А-ЯЁ][^.\n]{20,120})$',  # Первая заглавная строка
                r'(?:СВОД\s+ПРАВИЛ|СП\s+\d+[^.]*)\s*\.?\s*([А-ЯЁ][^\n]{20,120})',
                r'(?:ГОСТ\s+\d+[^.]*)\s*\.?\s*([А-ЯЁ][^\n]{20,120})',
            ],
            'organization': [
                r'(?:УТВЕРЖДЕН|УТВЕРЖДЕНО)\s+([А-ЯЁ][А-Яа-яё\s]{5,60})',
                r'(?:Минстрой\s+России|Росстандарт|Минрегион\s+России)',
                r'([А-ЯЁ][А-Яа-яё\s]{5,40}(?:институт|центр|организация|предприятие))',
            ],
            'approval_date': [
                r'(?:утверждено|утвержден)\s+.*?(\d{1,2}\.\d{1,2}\.\d{4})',
                r'(?:от|№)\s*.*?(\d{1,2}\.\d{1,2}\.\d{4})',
                r'(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{4})',
            ],
            'effective_date': [
                r'(?:вводится\s+в\s+действие|действует\s+с)\s+(\d{1,2}\.\d{1,2}\.\d{4})',
                r'(?:с\s+)(\d{1,2}\.\d{1,2}\.\d{4})',
            ]
        }

    def extract_full_structure(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        🔍 ГЛАВНЫЙ МЕТОД: Полное извлечение структуры документа
        
        Returns:
            Dict with complete document structure including:
            - metadata: document info (title, number, dates, organization)
            - sections: hierarchical sections with all content
            - tables: all tables with data and metadata
            - lists: all lists with structure
            - paragraphs: all paragraphs with metadata
            - statistics: document statistics
        """
        
        # 1. Извлечение метаданных документа
        metadata = self._extract_document_metadata(content, file_path)
        
        # 2. Извлечение иерархической структуры разделов
        sections = self._extract_hierarchical_sections(content)
        
        # 3. Извлечение всех таблиц
        tables = self._extract_all_tables(content)
        
        # 4. Извлечение всех списков
        lists = self._extract_all_lists(content)
        
        # 5. Извлечение всех абзацев
        paragraphs = self._extract_all_paragraphs(content, sections)
        
        # 6. Статистика документа
        statistics = self._calculate_document_statistics(content, sections, tables, lists)
        
        # 7. Формируем полную структуру
        full_structure = {
            'metadata': metadata,
            'sections': [self._section_to_dict(section) for section in sections],
            'tables': [self._table_to_dict(table) for table in tables],
            'lists': [self._list_to_dict(list_item) for list_item in lists],
            'paragraphs': paragraphs,
            'statistics': statistics,
            'extraction_info': {
                'extracted_at': datetime.now().isoformat(),
                'extractor_version': 'Enhanced_v3.0',
                'file_path': file_path,
                'content_length': len(content),
                'extraction_quality_score': self._calculate_extraction_quality(sections, tables, lists, metadata)
            }
        }
        
        return full_structure

    def _extract_document_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """Извлечение метаданных документа"""
        metadata = {
            'document_number': '',
            'document_title': '',
            'document_type': 'unknown',
            'organization': '',
            'approval_date': '',
            'effective_date': '',
            'keywords': [],
            'file_info': {
                'file_name': Path(file_path).name if file_path else '',
                'file_path': file_path,
            }
        }
        
        # Первые 2000 символов для поиска метаданных
        header_content = content[:2000]
        
        # Извлечение номера документа и определение типа
        for pattern in self.metadata_patterns['document_number']:
            match = re.search(pattern, header_content, re.IGNORECASE | re.MULTILINE)
            if match:
                metadata['document_number'] = match.group(1)
                # Определяем тип документа
                if 'СП' in pattern or 'СВОД' in pattern:
                    metadata['document_type'] = 'sp'  # Свод правил
                elif 'ГОСТ' in pattern:
                    metadata['document_type'] = 'gost'  # ГОСТ
                elif 'СНиП' in pattern:
                    metadata['document_type'] = 'snip'  # СНиП
                break
        
        # Извлечение названия документа
        for pattern in self.metadata_patterns['document_title']:
            matches = re.findall(pattern, header_content, re.MULTILINE)
            if matches:
                # Берем самое длинное совпадение (обычно это полное название)
                metadata['document_title'] = max(matches, key=len).strip()
                break
        
        # Извлечение организации
        for pattern in self.metadata_patterns['organization']:
            match = re.search(pattern, header_content, re.IGNORECASE | re.MULTILINE)
            if match:
                metadata['organization'] = match.group(1).strip() if match.groups() else match.group(0).strip()
                break
        
        # Извлечение дат
        for pattern in self.metadata_patterns['approval_date']:
            match = re.search(pattern, header_content, re.IGNORECASE | re.MULTILINE)
            if match:
                metadata['approval_date'] = match.group(1)
                break
        
        for pattern in self.metadata_patterns['effective_date']:
            match = re.search(pattern, header_content, re.IGNORECASE | re.MULTILINE)
            if match:
                metadata['effective_date'] = match.group(1)
                break
        
        # Извлечение ключевых слов
        keywords = self._extract_keywords(content, metadata['document_type'])
        metadata['keywords'] = keywords
        
        return metadata

    def _extract_hierarchical_sections(self, content: str) -> List[DocumentSection]:
        """Извлечение иерархической структуры разделов"""
        sections = []
        lines = content.split('\n')
        current_section = None
        current_subsection = None
        current_content = []
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                if current_content and current_content[-1]:  # Избегаем дублирования пустых строк
                    current_content.append('')
                continue
            
            # Проверяем, является ли строка заголовком раздела
            section_match = self._match_section_header(line)
            
            if section_match:
                # Сохраняем предыдущий раздел
                if current_section:
                    current_section.content = '\n'.join(current_content).strip()
                    if current_subsection:
                        current_section.subsections.append(current_subsection)
                        current_subsection = None
                    sections.append(current_section)
                
                # Создаем новый раздел
                number, title, level = section_match
                current_section = DocumentSection(
                    number=number,
                    title=title,
                    level=level,
                    content="",
                    page_numbers=[self._estimate_page_number(line_num, len(lines))]
                )
                current_content = []
                
                # Проверяем, является ли это подразделом
                if level > 1 and sections:
                    # Это подраздел, добавляем к родительскому разделу
                    parent_section = sections[-1]
                    if current_subsection and current_subsection.level < level:
                        current_subsection.content = '\n'.join(current_content).strip()
                        parent_section.subsections.append(current_subsection)
                    current_subsection = current_section
                    current_section = parent_section
                    current_content = []
            else:
                # Обычная строка содержимого
                current_content.append(line)
        
        # Сохраняем последний раздел
        if current_section:
            current_section.content = '\n'.join(current_content).strip()
            if current_subsection:
                current_section.subsections.append(current_subsection)
            sections.append(current_section)
        
        return sections

    def _match_section_header(self, line: str) -> Optional[Tuple[str, str, int]]:
        """Определение, является ли строка заголовком раздела"""
        
        # Проверяем нумерованные разделы
        for pattern in self.section_patterns['numbered']:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                number = match.group(1)
                title = match.group(2).strip()
                level = len(number.split('.'))
                return (number, title, level)
        
        # Проверяем буквенные разделы
        for pattern in self.section_patterns['lettered']:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                number = match.group(1)
                title = match.group(2).strip()
                return (number, title, 2)  # Буквенные разделы обычно уровня 2
        
        # Проверяем приложения
        for pattern in self.section_patterns['appendix']:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                number = match.group(1)
                title = match.group(2).strip() if len(match.groups()) > 1 else ""
                return (number, title, 1)  # Приложения - уровень 1
        
        return None

    def _extract_all_tables(self, content: str) -> List[DocumentTable]:
        """Извлечение всех таблиц из документа"""
        tables = []
        lines = content.split('\n')
        current_table = None
        in_table = False
        table_rows = []
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Поиск начала таблицы
            table_start_match = re.search(self.table_patterns['table_start'], line, re.IGNORECASE)
            if table_start_match:
                # Сохраняем предыдущую таблицу
                if current_table and table_rows:
                    current_table.rows = table_rows
                    tables.append(current_table)
                
                # Начинаем новую таблицу
                table_number = table_start_match.group(1)
                table_title = table_start_match.group(2).strip() if len(table_start_match.groups()) > 1 else ""
                
                current_table = DocumentTable(
                    number=table_number,
                    title=table_title,
                    headers=[],
                    rows=[],
                    page_number=self._estimate_page_number(line_num, len(lines))
                )
                table_rows = []
                in_table = True
                continue
            
            if in_table:
                # Проверяем, является ли строка строкой таблицы
                if '|' in line:
                    # Разделительная строка (пропускаем)
                    if re.match(self.table_patterns['table_separator'], line):
                        continue
                    
                    # Обычная строка таблицы
                    cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                    if cells:
                        if not current_table.headers:
                            current_table.headers = cells
                        else:
                            table_rows.append(cells)
                else:
                    # Конец таблицы
                    if current_table and table_rows:
                        current_table.rows = table_rows
                        tables.append(current_table)
                    in_table = False
                    current_table = None
                    table_rows = []
        
        # Сохраняем последнюю таблицу
        if current_table and table_rows:
            current_table.rows = table_rows
            tables.append(current_table)
        
        return tables

    def _extract_all_lists(self, content: str) -> List[DocumentList]:
        """Извлечение всех списков из документа"""
        lists = []
        lines = content.split('\n')
        current_list = None
        current_items = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            list_match = None
            list_type = None
            
            # Проверяем разные типы списков
            for list_pattern_name, pattern in self.list_patterns.items():
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    list_match = match
                    list_type = list_pattern_name
                    break
            
            if list_match:
                # Если это новый тип списка, сохраняем предыдущий
                if current_list and current_list.list_type != list_type and current_items:
                    current_list.items = current_items
                    lists.append(current_list)
                    current_items = []
                
                # Создаем новый список или продолжаем текущий
                if not current_list or current_list.list_type != list_type:
                    current_list = DocumentList(
                        list_type=list_type,
                        items=[],
                        level=1
                    )
                
                # Добавляем элемент списка
                item_text = list_match.group(1) if list_match.group(1) else list_match.group(2)
                if item_text:
                    current_items.append({
                        'text': item_text.strip(),
                        'number': list_match.group(0).split()[0] if list_type == 'numbered' else '',
                        'level': self._determine_list_level(line)
                    })
            else:
                # Завершаем текущий список
                if current_list and current_items:
                    current_list.items = current_items
                    lists.append(current_list)
                    current_list = None
                    current_items = []
        
        # Сохраняем последний список
        if current_list and current_items:
            current_list.items = current_items
            lists.append(current_list)
        
        return lists

    def _extract_all_paragraphs(self, content: str, sections: List[DocumentSection]) -> List[Dict[str, Any]]:
        """Извлечение всех абзацев с метаданными"""
        paragraphs = []
        
        # Разбиваем на абзацы
        raw_paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        for i, paragraph in enumerate(raw_paragraphs):
            # Определяем, к какому разделу относится абзац
            parent_section = self._find_parent_section(paragraph, sections)
            
            # Анализируем содержимое абзаца
            paragraph_info = {
                'id': f'p_{i}',
                'text': paragraph,
                'section': parent_section.number if parent_section else '',
                'section_title': parent_section.title if parent_section else '',
                'word_count': len(paragraph.split()),
                'char_count': len(paragraph),
                'has_numbers': bool(re.search(r'\d+', paragraph)),
                'has_technical_terms': self._has_technical_terms(paragraph),
                'is_list_item': self._is_list_item(paragraph),
                'is_table_content': '|' in paragraph,
                'references': self._extract_references(paragraph),
                'position': i
            }
            
            paragraphs.append(paragraph_info)
        
        return paragraphs

    def _calculate_document_statistics(self, content: str, sections: List[DocumentSection], 
                                     tables: List[DocumentTable], lists: List[DocumentList]) -> Dict[str, Any]:
        """Расчет статистики документа"""
        
        lines = content.split('\n')
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        words = content.split()
        
        return {
            'content_length': len(content),
            'line_count': len(lines),
            'paragraph_count': len(paragraphs),
            'word_count': len(words),
            'section_count': len(sections),
            'subsection_count': sum(len(section.subsections) for section in sections),
            'table_count': len(tables),
            'list_count': len(lists),
            'list_item_count': sum(len(lst.items) for lst in lists),
            'avg_section_length': np.mean([len(section.content) for section in sections]) if sections else 0,
            'longest_section': max((len(section.content) for section in sections), default=0),
            'has_appendices': any('приложение' in section.number.lower() for section in sections),
            'technical_density': self._calculate_technical_density(content),
        }

    def _calculate_extraction_quality(self, sections: List[DocumentSection], tables: List[DocumentTable], 
                                    lists: List[DocumentList], metadata: Dict[str, Any]) -> float:
        """Оценка качества извлечения структуры"""
        quality_score = 0.0
        
        # Качество извлечения разделов (40%)
        if sections:
            section_score = min(len(sections) / 10.0, 1.0) * 0.4
            quality_score += section_score
        
        # Качество извлечения метаданных (30%)
        metadata_fields = ['document_number', 'document_title', 'organization']
        filled_fields = sum(1 for field in metadata_fields if metadata.get(field))
        metadata_score = (filled_fields / len(metadata_fields)) * 0.3
        quality_score += metadata_score
        
        # Качество извлечения таблиц (15%)
        if tables:
            table_score = min(len(tables) / 5.0, 1.0) * 0.15
            quality_score += table_score
        
        # Качество извлечения списков (15%)
        if lists:
            list_score = min(len(lists) / 10.0, 1.0) * 0.15
            quality_score += list_score
        
        return min(quality_score, 1.0)

    # Вспомогательные методы
    def _section_to_dict(self, section: DocumentSection) -> Dict[str, Any]:
        """Конвертация секции в словарь"""
        return {
            'number': section.number,
            'title': section.title,
            'level': section.level,
            'content': section.content,
            'subsections': [self._section_to_dict(sub) for sub in section.subsections],
            'paragraphs': section.paragraphs,
            'tables': section.tables,
            'lists': section.lists,
            'page_numbers': section.page_numbers
        }
    
    def _table_to_dict(self, table: DocumentTable) -> Dict[str, Any]:
        """Конвертация таблицы в словарь"""
        return {
            'number': table.number,
            'title': table.title,
            'headers': table.headers,
            'rows': table.rows,
            'caption': table.caption,
            'page_number': table.page_number,
            'metadata': table.metadata,
            'row_count': len(table.rows),
            'column_count': len(table.headers) if table.headers else 0
        }
    
    def _list_to_dict(self, lst: DocumentList) -> Dict[str, Any]:
        """Конвертация списка в словарь"""
        return {
            'type': lst.list_type,
            'items': lst.items,
            'level': lst.level,
            'parent_section': lst.parent_section,
            'item_count': len(lst.items)
        }
    
    def _estimate_page_number(self, line_num: int, total_lines: int) -> int:
        """Приблизительная оценка номера страницы"""
        lines_per_page = 50  # Примерно 50 строк на страницу
        return max(1, (line_num // lines_per_page) + 1)
    
    def _find_parent_section(self, paragraph: str, sections: List[DocumentSection]) -> Optional[DocumentSection]:
        """Поиск родительского раздела для абзаца"""
        # Простая эвристика - ищем раздел с наиболее похожим содержимым
        best_match = None
        best_similarity = 0
        
        for section in sections:
            if paragraph in section.content:
                return section
            
            # Простая мера сходства по общим словам
            paragraph_words = set(paragraph.lower().split())
            section_words = set(section.content.lower().split())
            common_words = paragraph_words & section_words
            if common_words:
                similarity = len(common_words) / len(paragraph_words)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = section
        
        return best_match
    
    def _has_technical_terms(self, text: str) -> bool:
        """Проверка на наличие технических терминов"""
        technical_terms = [
            r'\b(?:ГОСТ|СП|СНиП)\s+[\d.-]+',
            r'\b\d+\s*(?:мм|см|м|км|мг|г|кг|т)\b',
            r'\b\d+\s*(?:°C|МПа|кПа|Н|кН)\b',
            r'\b(?:прочность|деформация|нагрузка|напряжение|модуль)\b'
        ]
        return any(re.search(term, text, re.IGNORECASE) for term in technical_terms)
    
    def _is_list_item(self, text: str) -> bool:
        """Проверка, является ли текст элементом списка"""
        return bool(re.match(r'^\s*(?:\d+\.|\w\)|[-•*])\s+', text))
    
    def _extract_references(self, text: str) -> List[str]:
        """Извлечение ссылок на нормативные документы"""
        references = []
        patterns = [
            r'\b(?:ГОСТ|СП|СНиП)\s+[\d.-]+(?:-\d+)?',
            r'\b(?:п\.|пункт)\s+\d+(?:\.\d+)*',
            r'\b(?:табл\.|таблица)\s+\d+(?:\.\d+)*'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references.extend(matches)
        
        return references
    
    def _determine_list_level(self, line: str) -> int:
        """Определение уровня вложенности элемента списка"""
        # Считаем количество пробелов или табов в начале строки
        leading_spaces = len(line) - len(line.lstrip())
        return max(1, leading_spaces // 4 + 1)  # 4 пробела = 1 уровень
    
    def _extract_keywords(self, content: str, doc_type: str) -> List[str]:
        """Извлечение ключевых слов документа"""
        keywords = []
        
        # Типоспецифические ключевые слова
        type_keywords = {
            'sp': ['строительство', 'проектирование', 'требования', 'нормы'],
            'gost': ['стандарт', 'качество', 'испытания', 'методы'],
            'snip': ['нормы', 'правила', 'строительство', 'проектирование']
        }
        
        # Общие технические термины
        general_patterns = [
            r'\b(?:прочность|деформация|нагрузка|напряжение)\b',
            r'\b(?:материал|конструкция|элемент|узел)\b',
            r'\b(?:контроль|проверка|измерение|расчет)\b'
        ]
        
        # Извлекаем типоспецифические ключевые слова
        if doc_type in type_keywords:
            for keyword in type_keywords[doc_type]:
                if keyword in content.lower():
                    keywords.append(keyword)
        
        # Извлекаем общие термины
        for pattern in general_patterns:
            matches = re.findall(pattern, content.lower(), re.IGNORECASE)
            keywords.extend(matches)
        
        # Убираем дубликаты и ограничиваем количество
        return list(dict.fromkeys(keywords))[:15]
    
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


# Функция для быстрого использования
def extract_document_structure(content: str, file_path: str = "") -> Dict[str, Any]:
    """
    🔍 Быстрое извлечение структуры документа
    
    Args:
        content: Текст документа
        file_path: Путь к файлу (опционально)
    
    Returns:
        Полная структура документа с метаданными
    """
    extractor = EnhancedStructureExtractor()
    return extractor.extract_full_structure(content, file_path)


# Функция для проверки совместимости с фронтом
def get_frontend_compatible_structure(content: str, file_path: str = "") -> Dict[str, Any]:
    """
    🔧 Получение структуры в формате, совместимом с фронтом
    
    Адаптирует структуру под ожидаемый фронтом формат
    """
    structure = extract_document_structure(content, file_path)
    
    # Адаптируем под ожидаемый фронтом формат
    frontend_structure = {
        # Основные метаданные (как ожидает фронт)
        'document_info': {
            'title': structure['metadata']['document_title'],
            'number': structure['metadata']['document_number'],
            'type': structure['metadata']['document_type'],
            'organization': structure['metadata']['organization'],
            'date': structure['metadata']['approval_date'],
            'file_name': structure['metadata']['file_info']['file_name']
        },
        
        # Структура разделов (плоский список для совместимости)
        'sections': [],
        
        # Таблицы в ожидаемом формате
        'tables': [
            {
                'id': f'table_{i}',
                'number': table['number'],
                'title': table['title'],
                'data': {
                    'headers': table['headers'],
                    'rows': table['rows']
                },
                'page': table['page_number']
            }
            for i, table in enumerate(structure['tables'])
        ],
        
        # Статистика
        'statistics': structure['statistics'],
        
        # Качество извлечения
        'extraction_quality': structure['extraction_info']['extraction_quality_score'],
        
        # Совместимость
        'compatibility_version': 'v3.0_frontend_compatible'
    }
    
    # Преобразуем иерархические разделы в плоский список
    def flatten_sections(sections, parent_path=""):
        flat_sections = []
        for section in sections:
            section_path = f"{parent_path}.{section['number']}" if parent_path else section['number']
            
            flat_section = {
                'id': section_path,
                'number': section['number'],
                'title': section['title'],
                'level': section['level'],
                'content': section['content'],
                'parent': parent_path,
                'has_subsections': len(section['subsections']) > 0,
                'word_count': len(section['content'].split()) if section['content'] else 0
            }
            flat_sections.append(flat_section)
            
            # Рекурсивно добавляем подразделы
            if section['subsections']:
                flat_sections.extend(flatten_sections(section['subsections'], section_path))
        
        return flat_sections
    
    frontend_structure['sections'] = flatten_sections(structure['sections'])
    
    return frontend_structure


if __name__ == "__main__":
    # Пример использования
    print("🔍 Enhanced Structure Extractor v3 - Ready!")
    
    # Тестовое содержимое
    test_content = """
СП 50.13330.2012

ТЕПЛОВАЯ ЗАЩИТА ЗДАНИЙ

Актуализированная редакция СНиП 23-02-2003

УТВЕРЖДЕНО
Министерством регионального развития РФ
31 мая 2012 г. № 269

1. ОБЩИЕ ПОЛОЖЕНИЯ

1.1 Настоящий свод правил распространяется на проектирование тепловой защиты зданий.

1.2 Требования настоящего свода правил обязательны для всех организаций.

2. НОРМАТИВНЫЕ ССЫЛКИ

В настоящем своде правил использованы ссылки на следующие документы:
- ГОСТ 30494-2011 Здания жилые и общественные. Параметры микроклимата в помещениях
- СП 23-101-2004 Проектирование тепловой защиты зданий

Таблица 1 - Нормируемые значения

|Тип здания|Сопротивление теплопередаче, м²·°С/Вт|
|Жилые|3,5|
|Общественные|2,8|
"""
    
    # Извлекаем структуру
    structure = extract_document_structure(test_content, "test_sp.pdf")
    
    print(f"✅ Извлечено:")
    print(f"  📋 Название: {structure['metadata']['document_title']}")
    print(f"  🔢 Номер: {structure['metadata']['document_number']}")
    print(f"  📊 Разделов: {len(structure['sections'])}")
    print(f"  📋 Таблиц: {len(structure['tables'])}")
    print(f"  🎯 Качество: {structure['extraction_info']['extraction_quality_score']:.2f}")
    
    # Проверяем совместимость с фронтом
    frontend_structure = get_frontend_compatible_structure(test_content, "test_sp.pdf")
    print(f"  🔧 Фронт совместимость: {frontend_structure['compatibility_version']}")