#!/usr/bin/env python3
"""
NTD Reference Extractor - Извлечение ссылок на НТД из документов
Создает внутренний реестр связей между нормативными документами
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class NTDReference:
    """Ссылка на НТД"""
    canonical_id: str
    document_type: str  # 'SP', 'SNiP', 'GOST', 'GESN', 'FER', 'TER', etc.
    full_text: str
    context: str
    position: int
    confidence: float

class NTDReferenceExtractor:
    """Извлечение ссылок на НТД из текста документов"""
    
    def __init__(self):
        self.ntd_patterns = {
            # СП (Своды правил)
            'SP': [
                r'СП\s+\d+\.\d+\.\d{4}',      # СП 16.13330.2017
                r'СП\s+\d+\.\d+\.\d{2}',      # СП 16.13330.17
                r'СП\s+\d+\.\d+',             # СП 16.13330
            ],
            # СНиП (Строительные нормы и правила)
            'SNiP': [
                r'СНиП\s+\d+\.\d+\.\d{4}',    # СНиП 2.01.07-85
                r'СНиП\s+\d+\.\d+',           # СНиП 2.01.07
            ],
            # ГОСТ (Государственные стандарты)
            'GOST': [
                r'ГОСТ\s+\d+\.\d+\.\d{4}',    # ГОСТ 12.1.004-91
                r'ГОСТ\s+\d+\.\d+',            # ГОСТ 12.1.004
            ],
            # ГЭСН (Государственные элементные сметные нормы)
            'GESN': [
                r'ГЭСН[р]?-[А-ЯЁ]+-\w+\d+-\d+',  # ГЭСНр-ОП-Разделы51-69
                r'ГЭСН[р]?-\w+-\d+',              # ГЭСН-ОП-51
                r'ГЭСН[р]?\s*-\s*[А-ЯЁ]+',       # ГЭСНр-ОП
                r'ГЭСН\s+\d+\.\d+\.\d{4}',        # ГЭСН 81-02-09-2001
            ],
            # ФЕР (Федеральные единичные расценки)
            'FER': [
                r'ФЕР[р]?-[А-ЯЁ]+-\w+\d+-\d+',    # ФЕРр-ОП-Разделы51-69
                r'ФЕР[р]?-\w+-\d+',               # ФЕР-ОП-51
                r'ФЕР\s+\d+\.\d+\.\d{4}',         # ФЕР 81-02-09-2001
            ],
            # ТЕР (Территориальные единичные расценки)
            'TER': [
                r'ТЕР\s+\d+\.\d+\.\d{4}',         # ТЕР 81-02-09-2001
            ],
            # ПП (Постановления Правительства)
            'PP': [
                r'Постановление\s+Правительства\s+РФ\s+от\s+\d{1,2}\.\d{1,2}\.\d{4}\s+N\s+\d+',
                r'ПП\s+РФ\s+от\s+\d{1,2}\.\d{1,2}\.\d{4}\s+N\s+\d+',
            ],
            # Приказы
            'PRIKAZ': [
                r'Приказ\s+от\s+\d{1,2}\.\d{1,2}\.\d{4}\s+N\s+\d+',
            ],
            # Федеральные законы
            'FZ': [
                r'Федеральный\s+закон\s+от\s+\d{1,2}\.\d{1,2}\.\d{4}\s+N\s+\d+',
                r'ФЗ\s+от\s+\d{1,2}\.\d{1,2}\.\d{4}\s+N\s+\d+',
            ]
        }
        
        # Контекстные фразы для поиска ссылок
        self.reference_contexts = [
            r'согласно\s+',
            r'в\s+соответствии\s+с\s+',
            r'на\s+основании\s+',
            r'в\s+соответствии\s+с\s+требованиями\s+',
            r'с\s+учетом\s+',
            r'с\s+применением\s+',
            r'с\s+использованием\s+',
            r'с\s+соблюдением\s+',
            r'с\s+учетом\s+положений\s+',
            r'в\s+соответствии\s+с\s+положениями\s+',
        ]
    
    def _canonicalize_ntd_id(self, ntd_id: str) -> str:
        """
        Создает канонический ID НТД, удаляя год, изменения и прочие вариативные суффиксы.
        
        Примеры:
        - 'СП 305.1325800.2017' -> 'СП 305.1325800'
        - 'СП 305.1325800.20' -> 'СП 305.1325800'
        - 'изм.3 к СП 305.1325800.2017' -> 'СП 305.1325800'
        - 'СНиП 2.01.07-85' -> 'СНиП 2.01.07'
        - 'ГОСТ Р 54257-2010' -> 'ГОСТ Р 54257'
        """
        original_id = ntd_id.strip()
        
        # 1. Удаление изменений/поправок в начале
        # Например: "изм.3 к СП 305.1325800.2017" -> "СП 305.1325800.2017"
        ntd_id = re.sub(r'^(изм\.?\s*\d+\s*к\s*|изменение\s*\d+\s*к\s*|поправка\s*\d+\s*к\s*)', '', ntd_id, flags=re.IGNORECASE)
        
        # 2. Удаление префиксов/суффиксов, указывающих на ссылку
        # Например: 'к СП 305', 'см. СП 305', 'Приложение А к'
        ntd_id = re.sub(r'^(к|см\.|приложение\s+\w+\s+к|согласно)\s+', '', ntd_id, flags=re.IGNORECASE)
        
        # 3. Удаление дефисов с годами в СНиП и ГОСТ
        # Например: "СНиП 2.01.07-85" -> "СНиП 2.01.07"
        ntd_id = re.sub(r'-\d{2,4}$', '', ntd_id, flags=re.IGNORECASE)
        
        # 4. Удаление полных годов (20xx или 19xx) в конце ID
        # Например: ".2017", "-2003"
        ntd_id = re.sub(r'([. -])(20|19)\d{2}(\s*ИЗМ\.?\d+)?$', r'', ntd_id, flags=re.IGNORECASE)
        
        # 5. Удаление двухзначных годов ТОЛЬКО если они выглядят как годы (20-99)
        # НО НЕ удаляем части номеров документов (01, 02, 07, etc.)
        # Удаляем только если это явно год в конце строки И это не часть номера документа
        if not re.search(r'\d+\.\d+$', ntd_id):  # Если это не номер документа с точками
            ntd_id = re.sub(r'([. -])([2-9]\d)(\s*ИЗМ\.?\d+)?$', r'', ntd_id, flags=re.IGNORECASE)
        
        # 6. Удаление изменений/поправок в конце
        # Например: "ИЗМ.1", "Поправка", "Изменение N 3"
        ntd_id = re.sub(r'((\sизм(ен|енения|нение)?)(\.|\s?№?)\s?\d+)|(\sпоправка\s?\d+)', '', ntd_id, flags=re.IGNORECASE)
        
        # 7. Финальная нормализация: убираем лишние пробелы, точки и дефисы в конце
        ntd_id = re.sub(r'[. \-]+$', '', ntd_id.strip())
        
        # 8. Нормализация пробелов
        ntd_id = re.sub(r'\s+', ' ', ntd_id)
        
        if ntd_id != original_id:
            logger.debug(f"[NTDReferenceExtractor] Канонизация: '{original_id}' -> '{ntd_id}'")
        
        return ntd_id.upper()
    
    def extract_ntd_references(self, text: str, document_id: str = "") -> List[NTDReference]:
        """
        Извлекает ссылки на НТД из текста документа
        
        Args:
            text: Текст документа
            document_id: Идентификатор документа
            
        Returns:
            Список найденных ссылок на НТД
        """
        logger.info(f"[NTDReferenceExtractor] Извлечение ссылок на НТД из документа: {document_id}")
        
        references = []
        
        # Ищем ссылки по всем типам НТД
        for doc_type, patterns in self.ntd_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    # Извлекаем контекст вокруг найденной ссылки
                    context = self._extract_context(text, match.start(), match.end())
                    
                    # Определяем уверенность на основе контекста
                    confidence = self._calculate_confidence(match.group(), context, doc_type)
                    
                    # КРИТИЧЕСКИ ВАЖНО: Применяем канонизацию!
                    original_text = match.group().strip()
                    canonical_id = self._canonicalize_ntd_id(original_text)
                    
                    # Создаем объект ссылки
                    reference = NTDReference(
                        canonical_id=canonical_id,  # Используем канонический ID!
                        document_type=doc_type,
                        full_text=original_text,  # Оригинальный текст сохраняем
                        context=context,
                        position=match.start(),
                        confidence=confidence
                    )
                    
                    references.append(reference)
                    logger.debug(f"[NTDReferenceExtractor] Найдена ссылка: {reference.canonical_id} (тип: {doc_type}, уверенность: {confidence:.2f})")
        
        # Убираем дубликаты и сортируем по уверенности
        references = self._deduplicate_references(references)
        references.sort(key=lambda x: x.confidence, reverse=True)
        
        logger.info(f"[NTDReferenceExtractor] Найдено {len(references)} ссылок на НТД")
        return references
    
    def _extract_context(self, text: str, start: int, end: int, context_length: int = 100) -> str:
        """Извлекает контекст вокруг найденной ссылки"""
        context_start = max(0, start - context_length)
        context_end = min(len(text), end + context_length)
        
        context = text[context_start:context_end].strip()
        
        # Очищаем контекст от лишних символов
        context = re.sub(r'\s+', ' ', context)
        
        return context
    
    def _calculate_confidence(self, reference_text: str, context: str, doc_type: str) -> float:
        """Вычисляет уверенность в найденной ссылке"""
        confidence = 0.5  # Базовая уверенность
        
        # Повышаем уверенность, если есть контекстные фразы
        for context_phrase in self.reference_contexts:
            if re.search(context_phrase, context, re.IGNORECASE):
                confidence += 0.2
                break
        
        # Повышаем уверенность для полных номеров с годом
        if re.search(r'\d{4}', reference_text):
            confidence += 0.1
        
        # Повышаем уверенность для СП (самые важные документы)
        if doc_type == 'SP':
            confidence += 0.1
        
        # Понижаем уверенность для коротких ссылок
        if len(reference_text) < 10:
            confidence -= 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    def _deduplicate_references(self, references: List[NTDReference]) -> List[NTDReference]:
        """Убирает дубликаты из списка ссылок"""
        seen = set()
        unique_references = []
        
        for ref in references:
            # Создаем ключ для проверки дубликатов
            key = (ref.canonical_id.lower(), ref.document_type)
            
            if key not in seen:
                seen.add(key)
                unique_references.append(ref)
            else:
                # Если дубликат найден, берем тот, у которого выше уверенность
                for i, existing_ref in enumerate(unique_references):
                    if (existing_ref.canonical_id.lower(), existing_ref.document_type) == key:
                        if ref.confidence > existing_ref.confidence:
                            unique_references[i] = ref
                        break
        
        return unique_references
    
    def extract_bibliography_references(self, text: str) -> List[NTDReference]:
        """Извлекает ссылки из раздела 'Библиография' или 'Список литературы'"""
        logger.info("[NTDReferenceExtractor] Поиск ссылок в разделе 'Библиография'")
        
        # Ищем раздел библиографии
        bibliography_patterns = [
            r'БИБЛИОГРАФИЯ[:\s]*\n(.*?)(?=\n\n|\n[А-ЯЁ]|$)',
            r'СПИСОК\s+ЛИТЕРАТУРЫ[:\s]*\n(.*?)(?=\n\n|\n[А-ЯЁ]|$)',
            r'ЛИТЕРАТУРА[:\s]*\n(.*?)(?=\n\n|\n[А-ЯЁ]|$)',
            r'ИСПОЛЬЗОВАННЫЕ\s+ИСТОЧНИКИ[:\s]*\n(.*?)(?=\n\n|\n[А-ЯЁ]|$)',
        ]
        
        bibliography_text = ""
        for pattern in bibliography_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                bibliography_text = match.group(1)
                logger.info(f"[NTDReferenceExtractor] Найден раздел библиографии ({len(bibliography_text)} символов)")
                break
        
        if not bibliography_text:
            logger.info("[NTDReferenceExtractor] Раздел библиографии не найден")
            return []
        
        # Извлекаем ссылки из библиографии
        return self.extract_ntd_references(bibliography_text, "bibliography")
    
    def get_reference_statistics(self, references: List[NTDReference]) -> Dict[str, Any]:
        """Возвращает статистику по найденным ссылкам"""
        if not references:
            return {
                'total_references': 0,
                'by_type': {},
                'high_confidence': 0,
                'average_confidence': 0.0
            }
        
        by_type = {}
        high_confidence = 0
        total_confidence = 0.0
        
        for ref in references:
            # Подсчет по типам
            if ref.document_type not in by_type:
                by_type[ref.document_type] = 0
            by_type[ref.document_type] += 1
            
            # Подсчет высокой уверенности
            if ref.confidence >= 0.7:
                high_confidence += 1
            
            total_confidence += ref.confidence
        
        return {
            'total_references': len(references),
            'by_type': by_type,
            'high_confidence': high_confidence,
            'average_confidence': total_confidence / len(references)
        }

# Example usage
if __name__ == "__main__":
    extractor = NTDReferenceExtractor()
    
    # Тестовый текст
    test_text = """
    Согласно СП 16.13330.2017 "Стальные конструкции" и СНиП 2.01.07-85 "Нагрузки и воздействия",
    конструкции должны быть рассчитаны в соответствии с ГОСТ 12.1.004-91.
    
    В разделе "Библиография" указаны следующие источники:
    1. СП 20.13330.2016 "Нагрузки и воздействия"
    2. ГЭСНр-ОП-Разделы51-69 "Государственные элементные сметные нормы"
    3. ФЕР 81-02-09-2001 "Федеральные единичные расценки"
    """
    
    references = extractor.extract_ntd_references(test_text, "test_document")
    
    print(f"Найдено {len(references)} ссылок на НТД:")
    for ref in references:
        print(f"  - {ref.canonical_id} ({ref.document_type}) - уверенность: {ref.confidence:.2f}")
    
    # Статистика
    stats = extractor.get_reference_statistics(references)
    print(f"\nСтатистика: {stats}")