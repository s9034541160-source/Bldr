"""
Сервис для классификации документов по ГОСТ 21.101-2020
"""

from typing import Dict, Any, Optional, List
import re
import logging

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """Классификатор документов по ГОСТ 21.101-2020"""
    
    # Словарь соответствий типов документов ГОСТ
    GOST_CLASSIFICATION = {
        # Основные рабочие документы
        "project_documentation": {
            "codes": ["ПД", "ПЗ", "ПМ"],
            "patterns": [r"проект", r"проектная", r"рабочая документация"],
            "description": "Проектная документация"
        },
        "working_drawings": {
            "codes": ["АР", "КР", "ОВ", "ВК", "ЭО", "СС", "АС"],
            "patterns": [r"чертеж", r"план", r"разрез", r"схема"],
            "description": "Рабочие чертежи"
        },
        "specifications": {
            "codes": ["ВР", "СП", "СПД"],
            "patterns": [r"спецификация", r"ведомость"],
            "description": "Спецификации и ведомости"
        },
        "estimates": {
            "codes": ["СМР", "ОС", "ОБ"],
            "patterns": [r"смета", r"расчет", r"стоимость"],
            "description": "Сметная документация"
        },
        "contracts": {
            "codes": ["ДОГ", "ДС"],
            "patterns": [r"договор", r"контракт", r"соглашение"],
            "description": "Договорная документация"
        },
        "acts": {
            "codes": ["АВ", "АС", "АО"],
            "patterns": [r"акт", r"приемка", r"выполненных работ"],
            "description": "Акты выполненных работ"
        },
        "reports": {
            "codes": ["ОТЧ", "ПО"],
            "patterns": [r"отчет", r"протокол"],
            "description": "Отчеты и протоколы"
        }
    }
    
    def classify_document(
        self,
        file_name: str,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Классификация документа по ГОСТ 21.101-2020
        
        Args:
            file_name: Имя файла
            title: Название документа
            content: Содержимое документа (опционально)
            
        Returns:
            Результат классификации с кодом ГОСТ и типом
        """
        text_to_analyze = f"{file_name} {title or ''} {content or ''}".lower()
        
        # Поиск по паттернам
        best_match = None
        best_score = 0
        
        for doc_type, info in self.GOST_CLASSIFICATION.items():
            score = 0
            
            # Проверка паттернов
            for pattern in info["patterns"]:
                if re.search(pattern, text_to_analyze, re.IGNORECASE):
                    score += 1
            
            # Проверка кодов ГОСТ в названии
            for code in info["codes"]:
                if code.lower() in text_to_analyze:
                    score += 2  # Коды имеют больший вес
            
            if score > best_score:
                best_score = score
                best_match = doc_type
        
        # Определение кода ГОСТ
        gost_code = None
        if best_match:
            codes = self.GOST_CLASSIFICATION[best_match]["codes"]
            # Пытаемся найти код в тексте
            for code in codes:
                if code.lower() in text_to_analyze:
                    gost_code = code
                    break
            # Если код не найден, берем первый из списка
            if not gost_code:
                gost_code = codes[0]
        
        return {
            "document_type": best_match or "unknown",
            "gost_code": gost_code,
            "gost_description": self.GOST_CLASSIFICATION.get(best_match, {}).get("description", "Не определено"),
            "confidence": min(best_score / 3.0, 1.0) if best_match else 0.0
        }
    
    def extract_metadata(
        self,
        file_name: str,
        file_path: str,
        mime_type: str,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Извлечение метаданных из документа
        
        Args:
            file_name: Имя файла
            file_path: Путь к файлу
            mime_type: MIME тип
            content: Содержимое документа (опционально)
            
        Returns:
            Словарь метаданных
        """
        metadata = {
            "file_name": file_name,
            "file_extension": file_name.split(".")[-1].lower() if "." in file_name else "",
            "mime_type": mime_type,
            "file_type": self._detect_file_type(mime_type),
        }
        
        # Извлечение информации из имени файла
        # Паттерн: [Код проекта]_[Тип]_[Номер]_[Название].[расширение]
        file_pattern = re.match(r"([A-Z0-9]+)_([A-Z]+)_(\d+)_(.+)\.", file_name.upper())
        if file_pattern:
            metadata["project_code"] = file_pattern.group(1)
            metadata["document_code"] = file_pattern.group(2)
            metadata["document_number"] = file_pattern.group(3)
            metadata["document_name"] = file_pattern.group(4)
        
        # Извлечение даты из имени файла (если есть)
        date_pattern = re.search(r"(\d{4})[._-](\d{2})[._-](\d{2})", file_name)
        if date_pattern:
            metadata["date"] = f"{date_pattern.group(1)}-{date_pattern.group(2)}-{date_pattern.group(3)}"
        
        # Классификация по ГОСТ
        classification = self.classify_document(file_name, content=content)
        metadata.update(classification)
        
        return metadata
    
    def _detect_file_type(self, mime_type: str) -> str:
        """Определение типа файла по MIME типу"""
        type_mapping = {
            "application/pdf": "pdf",
            "application/msword": "doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            "application/vnd.ms-excel": "xls",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
            "text/plain": "text",
            "image/jpeg": "image",
            "image/png": "image",
            "image/gif": "image"
        }
        return type_mapping.get(mime_type, "unknown")


# Глобальный экземпляр классификатора
document_classifier = DocumentClassifier()
