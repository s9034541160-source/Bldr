#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 RECURSIVE HIERARCHICAL CHUNKER V3
===================================
Система рекурсивного иерархического чанкинга документов

ПРИНЦИП РАБОТЫ:
📄 Документ
├── 1. Раздел
│   ├── 1.1 Подраздел
│   │   ├── 1.1.1 Подподраздел  ← Чанк (если маленький)
│   │   └── Абзац 1             ← Чанк
│   │   └── Абзац 2             ← Чанк
│   └── 1.2 Подраздел           ← Чанк (если маленький)
│   └── Таблица 1               ← Чанк
└── 2. Раздел                   ← Чанк (если маленький)

ЛОГИКА РАЗБИЕНИЯ:
✅ 1 пункт = 1 чанк (если размер подходящий)
✅ Если пункт слишком большой → разбиваем на под-пункты  
✅ Если под-пунктов нет → разбиваем на абзацы
✅ Таблицы и списки = отдельные чанки
"""

import re
from typing import Dict, List, Any, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ChunkGranularity(Enum):
    """Уровни детализации чанков"""
    DOCUMENT = "document"           # Весь документ (не используется)
    CHAPTER = "chapter"             # Глава (1, 2, 3, ...)
    SECTION = "section"             # Раздел (1.1, 1.2, ...)
    SUBSECTION = "subsection"       # Подраздел (1.1.1, 1.1.2, ...)
    PARAGRAPH = "paragraph"         # Абзац
    SENTENCE = "sentence"           # Предложение (крайний случай)
    TABLE = "table"                 # Таблица
    LIST = "list"                   # Список

@dataclass
class HierarchicalChunk:
    """Иерархический чанк с полными метаданными"""
    id: str
    content: str
    granularity: ChunkGranularity
    
    # Иерархическая информация
    hierarchy_path: str             # "1.2.3" или "1.2.3.paragraph_1"
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    
    # Структурная информация
    number: str = ""                # "1.2.3"
    title: str = ""                 # "Требования к материалам"
    level: int = 1                  # Уровень вложенности
    
    # Содержательные метаданные
    word_count: int = 0
    char_count: int = 0
    technical_terms_count: int = 0
    has_tables: bool = False
    has_lists: bool = False
    has_formulas: bool = False
    
    # Качественные метрики
    content_density: float = 0.0    # Плотность информации
    structural_quality: float = 0.0 # Качество структуры
    completeness: float = 0.0       # Полнота информации
    
    def calculate_metrics(self):
        """Автоматический расчет метрик"""
        self.word_count = len(self.content.split())
        self.char_count = len(self.content)
        self.technical_terms_count = self._count_technical_terms()
        self.has_tables = '|' in self.content or 'Таблица' in self.content
        self.has_lists = bool(re.search(r'^[-•*\d+]\s+', self.content, re.MULTILINE))
        self.has_formulas = bool(re.search(r'[=≤≥±×÷∞]', self.content))
        
        self.content_density = self._calculate_content_density()
        self.structural_quality = self._calculate_structural_quality()
        self.completeness = self._calculate_completeness()
    
    def _count_technical_terms(self) -> int:
        """Подсчет технических терминов"""
        patterns = [
            r'\b(?:ГОСТ|СП|СНиП)\s+[\d.-]+',
            r'\b\d+(?:\.\d+)?\s*(?:мм|см|м|км|г|кг|т|МПа|кПа|°C|%)\b',
            r'\b(?:прочность|нагрузка|материал|конструкция|сопротивление|деформация)\b'
        ]
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, self.content, re.IGNORECASE))
        return count
    
    def _calculate_content_density(self) -> float:
        """Плотность информации (техтермины/слова)"""
        if self.word_count == 0:
            return 0.0
        return min(self.technical_terms_count / self.word_count, 1.0)
    
    def _calculate_structural_quality(self) -> float:
        """Оценка структурного качества"""
        quality = 0.5  # Базовый уровень
        
        # Бонус за наличие заголовка
        if self.title:
            quality += 0.2
        
        # Бонус за правильную нумерацию
        if self.number and re.match(r'\d+(\.\d+)*', self.number):
            quality += 0.1
        
        # Бонус за структурированный контент
        if self.has_tables or self.has_lists:
            quality += 0.1
        
        # Бонус за оптимальную длину
        if 200 <= self.word_count <= 500:
            quality += 0.1
        
        return min(quality, 1.0)
    
    def _calculate_completeness(self) -> float:
        """Оценка полноты информации"""
        completeness = 0.0
        
        # Наличие заголовка
        if self.title:
            completeness += 0.3
        
        # Достаточная длина контента
        if self.word_count >= 50:
            completeness += 0.3
        
        # Наличие технических деталей
        if self.technical_terms_count > 0:
            completeness += 0.2
        
        # Структурированность
        if self.has_tables or self.has_lists:
            completeness += 0.2
        
        return min(completeness, 1.0)
    
    def to_api_format(self) -> Dict[str, Any]:
        """Конвертация в API формат для фронтенда"""
        return {
            'id': self.id,
            'content': self.content,
            'type': self.granularity.value,
            'hierarchy_path': self.hierarchy_path,
            'number': self.number,
            'title': self.title,
            'level': self.level,
            'parent_id': self.parent_id,
            'children_ids': self.children_ids,
            'metadata': {
                'word_count': self.word_count,
                'char_count': self.char_count,
                'technical_terms_count': self.technical_terms_count,
                'has_tables': self.has_tables,
                'has_lists': self.has_lists,
                'has_formulas': self.has_formulas,
                'content_density': self.content_density,
                'structural_quality': self.structural_quality,
                'completeness': self.completeness
            }
        }

class RecursiveHierarchicalChunker:
    """
    🔄 Рекурсивный иерархический чанкер
    
    Создает чанки на основе структуры документа с рекурсивным спуском:
    Документ → Главы → Разделы → Подразделы → Абзацы
    """
    
    def __init__(self, 
                 target_chunk_size: int = 400,
                 min_chunk_size: int = 100, 
                 max_chunk_size: int = 800,
                 preserve_structure: bool = True):
        """
        Args:
            target_chunk_size: Целевой размер чанка в словах
            min_chunk_size: Минимальный размер чанка
            max_chunk_size: Максимальный размер чанка
            preserve_structure: Сохранять структуру документа
        """
        self.target_chunk_size = target_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.preserve_structure = preserve_structure
        
        # Счетчик для уникальных ID
        self.chunk_counter = 0
    
    def create_hierarchical_chunks(self, document_structure: Dict[str, Any]) -> List[HierarchicalChunk]:
        """
        🎯 ГЛАВНЫЙ МЕТОД: Создание иерархических чанков
        
        Args:
            document_structure: Структура документа из AdvancedStructureExtractor
            
        Returns:
            Список иерархических чанков
        """
        logger.info("🔄 Starting recursive hierarchical chunking...")
        
        chunks = []
        sections = document_structure.get('sections', [])
        tables = document_structure.get('tables', [])
        lists = document_structure.get('lists', [])
        
        # Обрабатываем разделы рекурсивно
        for section in sections:
            section_chunks = self._process_section_recursively(section, parent_path="")
            chunks.extend(section_chunks)
        
        # Обрабатываем отдельные таблицы
        for table in tables:
            table_chunk = self._create_table_chunk(table)
            if table_chunk:
                chunks.append(table_chunk)
        
        # Обрабатываем отдельные списки
        for list_group in lists:
            list_chunk = self._create_list_chunk(list_group)
            if list_chunk:
                chunks.append(list_chunk)
        
        # Устанавливаем связи родитель-потомок
        self._establish_parent_child_relationships(chunks)
        
        # Рассчитываем метрики для всех чанков
        for chunk in chunks:
            chunk.calculate_metrics()
        
        logger.info(f"✅ Created {len(chunks)} hierarchical chunks")
        
        return chunks
    
    def _process_section_recursively(self, section: Dict[str, Any], parent_path: str = "", level: int = 1) -> List[HierarchicalChunk]:
        """
        🔄 Рекурсивная обработка раздела
        
        Логика:
        1. Если раздел маленький → делаем 1 чанк
        2. Если есть подразделы → обрабатываем каждый рекурсивно
        3. Если нет подразделов, но раздел большой → разбиваем на абзацы
        """
        chunks = []
        
        section_number = section.get('number', '')
        section_title = section.get('title', '')
        section_content = section.get('content', '')
        subsections = section.get('subsections', [])
        
        # Формируем иерархический путь
        hierarchy_path = f"{parent_path}.{section_number}" if parent_path else section_number
        
        logger.debug(f"🔄 Processing section {hierarchy_path}: '{section_title}'")
        
        # Собираем весь контент раздела (включая подразделы)
        full_section_content = self._gather_full_section_content(section)
        section_word_count = len(full_section_content.split())
        
        # РЕШЕНИЕ 1: Маленький раздел → целиком в чанк
        if section_word_count <= self.target_chunk_size and not subsections:
            chunk = self._create_section_chunk(
                section, hierarchy_path, level, ChunkGranularity.SECTION
            )
            chunks.append(chunk)
            logger.debug(f"  ✅ Small section → single chunk ({section_word_count} words)")
        
        # РЕШЕНИЕ 2: Есть подразделы → обрабатываем рекурсивно
        elif subsections:
            logger.debug(f"  🔄 Section has {len(subsections)} subsections → processing recursively")
            
            # Сначала контент самого раздела (до подразделов)
            if section_content and len(section_content.split()) >= self.min_chunk_size:
                main_chunk = self._create_section_chunk(
                    {'number': section_number, 'title': section_title, 'content': section_content},
                    hierarchy_path, level, ChunkGranularity.SECTION
                )
                chunks.append(main_chunk)
            
            # Затем рекурсивно обрабатываем подразделы
            for i, subsection in enumerate(subsections):
                subsection_chunks = self._process_section_recursively(
                    subsection, hierarchy_path, level + 1
                )
                chunks.extend(subsection_chunks)
        
        # РЕШЕНИЕ 3: Большой раздел без подразделов → разбиваем на абзацы
        else:
            logger.debug(f"  📄 Large section without subsections → splitting into paragraphs ({section_word_count} words)")
            paragraph_chunks = self._split_into_paragraph_chunks(section, hierarchy_path, level)
            chunks.extend(paragraph_chunks)
        
        return chunks
    
    def _gather_full_section_content(self, section: Dict[str, Any]) -> str:
        """Сборка полного контента раздела включая подразделы"""
        content_parts = []
        
        # Заголовок
        if section.get('title'):
            header = f"{section.get('number', '')} {section.get('title', '')}"
            content_parts.append(header)
        
        # Основной контент
        if section.get('content'):
            content_parts.append(section.get('content', ''))
        
        # Рекурсивно добавляем подразделы
        for subsection in section.get('subsections', []):
            subsection_content = self._gather_full_section_content(subsection)
            if subsection_content:
                content_parts.append(subsection_content)
        
        return '\n\n'.join(content_parts)
    
    def _create_section_chunk(self, section: Dict[str, Any], hierarchy_path: str, 
                             level: int, granularity: ChunkGranularity) -> HierarchicalChunk:
        """Создание чанка для раздела"""
        
        section_number = section.get('number', '')
        section_title = section.get('title', '')
        section_content = section.get('content', '')
        
        # Формируем полный контент чанка
        content_parts = []
        if section_title:
            content_parts.append(f"{section_number} {section_title}")
        if section_content:
            content_parts.append(section_content)
        
        full_content = '\n\n'.join(content_parts)
        
        chunk = HierarchicalChunk(
            id=self._generate_chunk_id(),
            content=full_content,
            granularity=granularity,
            hierarchy_path=hierarchy_path,
            number=section_number,
            title=section_title,
            level=level
        )
        
        return chunk
    
    def _split_into_paragraph_chunks(self, section: Dict[str, Any], parent_path: str, level: int) -> List[HierarchicalChunk]:
        """Разбиение раздела на чанки по абзацам"""
        chunks = []
        
        content = section.get('content', '')
        if not content:
            return chunks
        
        # Разбиваем на абзацы
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        current_chunk_content = []
        current_word_count = 0
        paragraph_counter = 1
        
        for paragraph in paragraphs:
            paragraph_words = len(paragraph.split())
            
            # Если добавление абзаца не превышает лимит
            if current_word_count + paragraph_words <= self.target_chunk_size:
                current_chunk_content.append(paragraph)
                current_word_count += paragraph_words
            else:
                # Сохраняем текущий чанк (если есть контент)
                if current_chunk_content and current_word_count >= self.min_chunk_size:
                    chunk = self._create_paragraph_chunk(
                        current_chunk_content, section, parent_path, level, paragraph_counter
                    )
                    chunks.append(chunk)
                    paragraph_counter += 1
                
                # Начинаем новый чанк
                current_chunk_content = [paragraph]
                current_word_count = paragraph_words
        
        # Сохраняем последний чанк
        if current_chunk_content and current_word_count >= self.min_chunk_size:
            chunk = self._create_paragraph_chunk(
                current_chunk_content, section, parent_path, level, paragraph_counter
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_paragraph_chunk(self, paragraphs: List[str], section: Dict[str, Any], 
                              parent_path: str, level: int, paragraph_number: int) -> HierarchicalChunk:
        """Создание чанка из абзацев"""
        
        content = '\n\n'.join(paragraphs)
        hierarchy_path = f"{parent_path}.p{paragraph_number}"
        
        chunk = HierarchicalChunk(
            id=self._generate_chunk_id(),
            content=content,
            granularity=ChunkGranularity.PARAGRAPH,
            hierarchy_path=hierarchy_path,
            number=f"{section.get('number', '')}.{paragraph_number}",
            title=f"Часть {paragraph_number}",
            level=level + 1
        )
        
        return chunk
    
    def _create_table_chunk(self, table: Dict[str, Any]) -> Optional[HierarchicalChunk]:
        """Создание чанка для таблицы"""
        
        table_content = self._format_table_content(table)
        if not table_content or len(table_content.split()) < self.min_chunk_size:
            return None
        
        chunk = HierarchicalChunk(
            id=self._generate_chunk_id(),
            content=table_content,
            granularity=ChunkGranularity.TABLE,
            hierarchy_path=f"table_{table.get('number', 'unknown')}",
            number=table.get('number', ''),
            title=table.get('title', 'Таблица'),
            level=1
        )
        
        return chunk
    
    def _create_list_chunk(self, list_group: Dict[str, Any]) -> Optional[HierarchicalChunk]:
        """Создание чанка для списка"""
        
        list_content = self._format_list_content(list_group)
        if not list_content or len(list_content.split()) < self.min_chunk_size:
            return None
        
        chunk = HierarchicalChunk(
            id=self._generate_chunk_id(),
            content=list_content,
            granularity=ChunkGranularity.LIST,
            hierarchy_path=f"list_{self.chunk_counter}",
            number="",
            title="Список",
            level=1
        )
        
        return chunk
    
    def _format_table_content(self, table: Dict[str, Any]) -> str:
        """Форматирование таблицы в текст"""
        content_parts = []
        
        # Заголовок таблицы
        if table.get('number') or table.get('title'):
            header = f"Таблица {table.get('number', '')} — {table.get('title', '')}"
            content_parts.append(header.strip(' —'))
        
        # Заголовки столбцов
        headers = table.get('headers', [])
        if headers:
            content_parts.append(' | '.join(headers))
            content_parts.append('|'.join(['---'] * len(headers)))
        
        # Строки таблицы
        for row in table.get('rows', []):
            if isinstance(row, list):
                content_parts.append(' | '.join(str(cell) for cell in row))
        
        return '\n'.join(content_parts)
    
    def _format_list_content(self, list_group: Dict[str, Any]) -> str:
        """Форматирование списка в текст"""
        content_parts = []
        
        for item in list_group.get('items', []):
            if isinstance(item, dict):
                marker = item.get('marker', '•')
                text = item.get('text', '')
                content_parts.append(f"{marker} {text}")
            else:
                content_parts.append(f"• {item}")
        
        return '\n'.join(content_parts)
    
    def _establish_parent_child_relationships(self, chunks: List[HierarchicalChunk]):
        """Установка связей родитель-потомок между чанками"""
        
        # Создаем индекс по hierarchy_path
        path_to_chunk = {chunk.hierarchy_path: chunk for chunk in chunks}
        
        for chunk in chunks:
            path_parts = chunk.hierarchy_path.split('.')
            
            # Ищем родителя (путь на уровень выше)
            if len(path_parts) > 1:
                parent_path = '.'.join(path_parts[:-1])
                parent_chunk = path_to_chunk.get(parent_path)
                
                if parent_chunk:
                    chunk.parent_id = parent_chunk.id
                    if chunk.id not in parent_chunk.children_ids:
                        parent_chunk.children_ids.append(chunk.id)
    
    def _generate_chunk_id(self) -> str:
        """Генерация уникального ID для чанка"""
        self.chunk_counter += 1
        return f"chunk_{self.chunk_counter:04d}"

# Функция для интеграции в существующую систему
def create_hierarchical_chunks_from_structure(document_structure: Dict[str, Any], 
                                             target_chunk_size: int = 400) -> List[Dict[str, Any]]:
    """
    🎯 API-совместимая функция для создания иерархических чанков
    
    Args:
        document_structure: Структура документа
        target_chunk_size: Целевой размер чанка в словах
        
    Returns:
        Список чанков в API формате
    """
    
    chunker = RecursiveHierarchicalChunker(target_chunk_size=target_chunk_size)
    hierarchical_chunks = chunker.create_hierarchical_chunks(document_structure)
    
    # Конвертируем в API формат
    api_chunks = [chunk.to_api_format() for chunk in hierarchical_chunks]
    
    return api_chunks

if __name__ == "__main__":
    print("🔄 Recursive Hierarchical Chunker v3 - Ready!")
    print("Создает чанки по принципу: 1 пункт = 1 чанк")
    print("С рекурсивным разбиением по структуре документа")
    
    # Тестовая структура документа
    test_structure = {
        'sections': [
            {
                'number': '1',
                'title': 'ОБЩИЕ ПОЛОЖЕНИЯ',
                'content': 'Общий контент раздела 1...',
                'level': 1,
                'subsections': [
                    {
                        'number': '1.1',
                        'title': 'Область применения',
                        'content': 'Подробное описание области применения документа с техническими требованиями...',
                        'level': 2,
                        'subsections': []
                    },
                    {
                        'number': '1.2', 
                        'title': 'Нормативные ссылки',
                        'content': 'Список нормативных документов с подробными описаниями каждого...',
                        'level': 2,
                        'subsections': []
                    }
                ]
            }
        ],
        'tables': [],
        'lists': []
    }
    
    # Тестируем
    chunks = create_hierarchical_chunks_from_structure(test_structure, target_chunk_size=300)
    
    print(f"\n✅ Создано {len(chunks)} иерархических чанков:")
    for chunk in chunks:
        print(f"  📄 {chunk['hierarchy_path']}: {chunk['title']} ({chunk['metadata']['word_count']} слов)")