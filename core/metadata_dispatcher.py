#!/usr/bin/env python3
"""
Диспетчер метаданных с сценарной идентификацией
Универсальная архитектура для извлечения метаданных разных типов документов
"""
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DocumentMetadata:
    """Универсальная структура метаданных документа"""
    canonical_id: str = ""
    title: str = ""
    doc_type: str = ""
    doc_numbers: List[str] = None
    authors: List[str] = None
    dates: List[str] = None
    materials: List[str] = None
    finances: List[str] = None
    quality_score: float = 0.0
    extraction_method: str = ""
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.doc_numbers is None:
            self.doc_numbers = []
        if self.authors is None:
            self.authors = []
        if self.dates is None:
            self.dates = []
        if self.materials is None:
            self.materials = []
        if self.finances is None:
            self.finances = []

class MetadataDispatcher:
    """Диспетчер метаданных с сценарной идентификацией"""
    
    def __init__(self):
        self.strategies = {
            'norms': self._strategy_strict_ntd_parsing,
            'smeta': self._strategy_strict_smeta_parsing,
            'legal': self._strategy_strict_legal_parsing,
            'project': self._strategy_project_parsing,
            'book': self._strategy_nlp_parsing,
            'course': self._strategy_nlp_parsing,
            'manual': self._strategy_hybrid_parsing,
            'default': self._strategy_aggressive_fallback
        }
    
    def extract_metadata(self, content: str, doc_type_info: Dict[str, Any], 
                        file_path: str = "") -> DocumentMetadata:
        """
        Главный диспетчер для извлечения метаданных
        
        Args:
            content: Содержимое документа
            doc_type_info: Информация о типе документа
            file_path: Путь к файлу (для fallback)
            
        Returns:
            DocumentMetadata объект
        """
        doc_type = doc_type_info.get('doc_type', 'default')
        subtype = doc_type_info.get('subtype', '')
        
        logger.info(f"[MetadataDispatcher] Обработка документа типа: {doc_type}/{subtype}")
        
        # Выбираем стратегию
        strategy = self.strategies.get(doc_type, self.strategies['default'])
        
        try:
            # 1. Сначала пытаемся строгое извлечение
            metadata = strategy(content, doc_type_info, file_path)
            
            # 2. Если строгое не сработало, пробуем NLP
            if not metadata.canonical_id and doc_type in ['book', 'course', 'manual']:
                logger.info(f"[MetadataDispatcher] Строгое извлечение не сработало, пробуем NLP для {doc_type}")
                nlp_metadata = self._strategy_nlp_parsing(content, doc_type_info, file_path)
                if nlp_metadata.canonical_id:
                    metadata = nlp_metadata
            
            # 3. Финальный fallback
            if not metadata.canonical_id:
                logger.warning(f"[MetadataDispatcher] Все стратегии не сработали, используем агрессивный fallback")
                fallback_metadata = self._strategy_aggressive_fallback(content, doc_type_info, file_path)
                if fallback_metadata.canonical_id:
                    metadata = fallback_metadata
            
            # 4. Устанавливаем метод извлечения
            if metadata.canonical_id:
                metadata.extraction_method = strategy.__name__
                metadata.confidence = self._calculate_confidence(metadata)
            
            logger.info(f"[MetadataDispatcher] Результат: {metadata.canonical_id} (метод: {metadata.extraction_method}, уверенность: {metadata.confidence:.2f})")
            return metadata
            
        except Exception as e:
            logger.error(f"[MetadataDispatcher] Ошибка в стратегии {strategy.__name__}: {e}")
            return DocumentMetadata()
    
    def _strategy_strict_ntd_parsing(self, content: str, doc_type_info: Dict, file_path: str) -> DocumentMetadata:
        """Стратегия 1: Строгий парсинг для НТД (СП, СНиП, ГОСТ)"""
        metadata = DocumentMetadata()
        metadata.doc_type = "norms"
        
        # Извлекаем из заголовка (первые 2000 символов)
        header_text = content[:2000] if content else ""
        
        # Паттерны для НТД
        ntd_patterns = [
            r'СП\s+\d+\.\d+\.\d{4}',      # СП 16.13330.2017
            r'СП\s+\d+\.\d+\.\d{2}',      # СП 16.13330.17
            r'СП\s+\d+\.\d+',             # СП 16.13330
            r'СНиП\s+\d+\.\d+\.\d{4}',    # СНиП 2.01.07-85
            r'СНиП\s+\d+\.\d+',           # СНиП 2.01.07
            r'ГОСТ\s+\d+\.\d+\.\d{4}',    # ГОСТ 12.1.004-91
            r'ГОСТ\s+\d+\.\d+',           # ГОСТ 12.1.004
        ]
        
        for pattern in ntd_patterns:
            matches = re.findall(pattern, header_text, re.IGNORECASE)
            if matches:
                metadata.canonical_id = matches[0]
                metadata.doc_numbers = matches
                metadata.title = f"Свод правил {matches[0]}"
                break
        
        # Извлекаем даты
        date_patterns = [
            r'\d{4}',  # Год
            r'\d{1,2}\.\d{1,2}\.\d{4}',  # Дата
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, header_text)
            metadata.dates.extend(matches)
        
        return metadata
    
    def _strategy_strict_smeta_parsing(self, content: str, doc_type_info: Dict, file_path: str) -> DocumentMetadata:
        """Стратегия 2: Строгий парсинг для сметных нормативов (ГЭСН, ФЕР, ТЕР)"""
        metadata = DocumentMetadata()
        metadata.doc_type = "smeta"
        
        # Сначала пробуем извлечь из текста
        header_text = content[:2000] if content else ""
        
        # Расширенные паттерны для ГЭСН/ФЕР
        smeta_patterns = [
            r'ГЭСН[р]?-[А-ЯЁ]+-\w+\d+-\d+',  # ГЭСНр-ОП-Разделы51-69
            r'ГЭСН[р]?-\w+-\d+',              # ГЭСН-ОП-51
            r'ГЭСН[р]?\s*-\s*[А-ЯЁ]+',       # ГЭСНр-ОП
            r'ФЕР[р]?-[А-ЯЁ]+-\w+\d+-\d+',    # ФЕРр-ОП-Разделы51-69
            r'ФЕР[р]?-\w+-\d+',               # ФЕР-ОП-51
            r'ГЭСН\s+\d+\.\d+\.\d{4}',        # ГЭСН 81-02-09-2001
            r'ФЕР\s+\d+\.\d+\.\d{4}',         # ФЕР 81-02-09-2001
        ]
        
        for pattern in smeta_patterns:
            matches = re.findall(pattern, header_text, re.IGNORECASE)
            if matches:
                metadata.canonical_id = matches[0]
                metadata.doc_numbers = matches
                metadata.title = f"Сметные нормативы {matches[0]}"
                break
        
        # Если не нашли в тексте, пробуем из имени файла
        if not metadata.canonical_id and file_path:
            filename = Path(file_path).stem
            # Убираем хеш-префиксы
            if '_' in filename:
                parts = filename.split('_')
                for part in reversed(parts):
                    if any(c.isalpha() for c in part):
                        filename = part
                        break
            
            for pattern in smeta_patterns:
                matches = re.findall(pattern, filename, re.IGNORECASE)
                if matches:
                    metadata.canonical_id = matches[0]
                    metadata.doc_numbers = matches
                    metadata.title = f"Сметные нормативы {matches[0]}"
                    metadata.extraction_method = "filename_fallback"
                    break
        
        return metadata
    
    def _strategy_strict_legal_parsing(self, content: str, doc_type_info: Dict, file_path: str) -> DocumentMetadata:
        """Стратегия 3: Строгий парсинг для правовых документов"""
        metadata = DocumentMetadata()
        metadata.doc_type = "legal"
        
        header_text = content[:2000] if content else ""
        
        # Паттерны для правовых документов
        legal_patterns = [
            r'Постановление\s+Правительства\s+РФ\s+от\s+\d{1,2}\.\d{1,2}\.\d{4}\s+N\s+\d+',
            r'Приказ\s+от\s+\d{1,2}\.\d{1,2}\.\d{4}\s+N\s+\d+',
            r'Федеральный\s+закон\s+от\s+\d{1,2}\.\d{1,2}\.\d{4}\s+N\s+\d+',
            r'ПП\s+РФ\s+от\s+\d{1,2}\.\d{1,2}\.\d{4}\s+N\s+\d+',
        ]
        
        for pattern in legal_patterns:
            matches = re.findall(pattern, header_text, re.IGNORECASE)
            if matches:
                metadata.canonical_id = matches[0]
                metadata.doc_numbers = matches
                metadata.title = matches[0]
                break
        
        return metadata
    
    def _strategy_project_parsing(self, content: str, doc_type_info: Dict, file_path: str) -> DocumentMetadata:
        """Стратегия 4: Парсинг для проектных документов (ППР, ПОС)"""
        metadata = DocumentMetadata()
        metadata.doc_type = "project"
        
        # Ищем ключевые фразы для проектных документов
        key_phrases = [
            r'Номер\s+проекта[:\s]+([А-ЯЁа-яё0-9\-\s]+)',
            r'Идентификатор[:\s]+([А-ЯЁа-яё0-9\-\s]+)',
            r'Код\s+проекта[:\s]+([А-ЯЁа-яё0-9\-\s]+)',
            r'ППР[-\s]*([А-ЯЁа-яё0-9\-\s]+)',
            r'ПОС[-\s]*([А-ЯЁа-яё0-9\-\s]+)',
        ]
        
        for pattern in key_phrases:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                project_id = matches[0].strip()
                metadata.canonical_id = f"ПРОЕКТ-{project_id}"
                metadata.doc_numbers = [project_id]
                metadata.title = f"Проект {project_id}"
                break
        
        return metadata
    
    def _strategy_nlp_parsing(self, content: str, doc_type_info: Dict, file_path: str) -> DocumentMetadata:
        """Стратегия 5: NLP-парсинг для книг, курсов, образовательных материалов"""
        metadata = DocumentMetadata()
        metadata.doc_type = doc_type_info.get('doc_type', 'book')
        
        # Извлекаем заголовок из первых 3 страниц
        title_text = content[:3000] if content else ""
        
        # Ищем основные заголовки
        title_patterns = [
            r'^([А-ЯЁа-яё\s]{10,100})$',  # Строки только с русскими буквами
            r'^([А-ЯЁ][А-ЯЁа-яё\s]{9,99})$',  # Заголовки с заглавной буквы
        ]
        
        lines = title_text.split('\n')
        for line in lines[:20]:  # Проверяем первые 20 строк
            line = line.strip()
            if len(line) > 10 and len(line) < 100:
                for pattern in title_patterns:
                    match = re.match(pattern, line)
                    if match:
                        metadata.title = match.group(1).strip()
                        metadata.canonical_id = metadata.title
                        break
                if metadata.canonical_id:
                    break
        
        # Ищем авторов
        author_patterns = [
            r'Автор[:\s]+([А-ЯЁа-яё\s\.]+)',
            r'Составитель[:\s]+([А-ЯЁа-яё\s\.]+)',
            r'([А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.[А-ЯЁ]\.)',  # Фамилия И.О.
        ]
        
        for pattern in author_patterns:
            matches = re.findall(pattern, title_text, re.IGNORECASE)
            metadata.authors.extend(matches)
        
        return metadata
    
    def _strategy_hybrid_parsing(self, content: str, doc_type_info: Dict, file_path: str) -> DocumentMetadata:
        """Стратегия 6: Гибридный парсинг для методических рекомендаций"""
        metadata = DocumentMetadata()
        metadata.doc_type = "manual"
        
        # Сначала строгий поиск номера
        number_patterns = [
            r'МР\s+N\s+(\d+)',
            r'РД\s+N\s+(\d+)',
            r'Методические\s+Рекомендации\s+N\s+(\d+)',
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                metadata.doc_numbers = matches
                metadata.canonical_id = f"МР-{matches[0]}"
                break
        
        # Затем NLP для названия
        if not metadata.canonical_id:
            nlp_metadata = self._strategy_nlp_parsing(content, doc_type_info, file_path)
            if nlp_metadata.canonical_id:
                metadata = nlp_metadata
        
        return metadata
    
    def _strategy_aggressive_fallback(self, content: str, doc_type_info: Dict, file_path: str) -> DocumentMetadata:
        """Стратегия 7: Агрессивный fallback для всех типов"""
        metadata = DocumentMetadata()
        metadata.doc_type = doc_type_info.get('doc_type', 'unknown')
        
        # Пробуем все паттерны подряд
        all_patterns = [
            r'СП\s+\d+\.\d+\.\d{4}',
            r'СНиП\s+\d+\.\d+\.\d{4}',
            r'ГОСТ\s+\d+\.\d+\.\d{4}',
            r'ГЭСН[р]?-[А-ЯЁ]+-\w+\d+-\d+',
            r'ФЕР[р]?-[А-ЯЁ]+-\w+\d+-\d+',
            r'Постановление\s+Правительства',
            r'Приказ\s+от',
        ]
        
        for pattern in all_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                metadata.canonical_id = matches[0]
                metadata.doc_numbers = matches
                metadata.title = matches[0]
                break
        
        # Если ничего не нашли, используем имя файла
        if not metadata.canonical_id and file_path:
            filename = Path(file_path).stem
            # Убираем хеш-префиксы
            if '_' in filename:
                parts = filename.split('_')
                for part in reversed(parts):
                    if any(c.isalpha() for c in part):
                        filename = part
                        break
            
            metadata.canonical_id = filename
            metadata.title = filename
        
        return metadata
    
    def _calculate_confidence(self, metadata: DocumentMetadata) -> float:
        """Вычисляет уверенность в извлеченных метаданных"""
        confidence = 0.0
        
        if metadata.canonical_id:
            confidence += 0.4
        
        if metadata.doc_numbers:
            confidence += 0.2
        
        if metadata.authors:
            confidence += 0.1
        
        if metadata.dates:
            confidence += 0.1
        
        if metadata.title and len(metadata.title) > 10:
            confidence += 0.2
        
        return min(confidence, 1.0)

# Example usage
if __name__ == "__main__":
    dispatcher = MetadataDispatcher()
    
    # Тестовые данные
    test_content = "СП 88.13330.2014 Защитные сооружения гражданской обороны"
    test_doc_type = {'doc_type': 'norms', 'subtype': 'sp'}
    
    metadata = dispatcher.extract_metadata(test_content, test_doc_type)
    print(f"Canonical ID: {metadata.canonical_id}")
    print(f"Title: {metadata.title}")
    print(f"Method: {metadata.extraction_method}")
    print(f"Confidence: {metadata.confidence}")
