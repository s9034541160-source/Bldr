"""
Сервис для классификации документов по ГОСТ 21.101-2020
"""

from typing import Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """Классификатор документов по ГОСТ 21.101-2020"""
    
    # Классификация по ГОСТ 21.101-2020 (основные типы)
    GOST_CLASSIFICATION = {
        "project_documentation": {
            "codes": ["ПД", "ПЗ", "ПР", "ПО"],
            "patterns": [
                r"проектн",
                r"проектн",
                r"рабоч",
                r"рабоч",
            ]
        },
        "working_drawings": {
            "codes": ["АР", "КР", "ОВ", "ВК", "ЭО", "СС", "АС"],
            "patterns": [
                r"архитектурн",
                r"конструктивн",
                r"отоплен",
                r"водопровод",
                r"электро",
                r"связь",
                r"автоматизац"
            ]
        },
        "specifications": {
            "codes": ["СП", "ВР", "МР", "ЭР"],
            "patterns": [
                r"спецификац",
                r"ведомость",
                r"материал",
                r"элемент"
            ]
        },
        "estimates": {
            "codes": ["СМ", "ЛСР"],
            "patterns": [
                r"смет",
                r"локальн",
                r"ресурс"
            ]
        },
        "contracts": {
            "codes": ["ДОГ", "ДС"],
            "patterns": [
                r"договор",
                r"контракт",
                r"соглашен"
            ]
        },
        "reports": {
            "codes": ["ОТЧ", "АКТ"],
            "patterns": [
                r"отчет",
                r"акт",
                r"протокол"
            ]
        }
    }
    
    def classify_document(
        self,
        title: str,
        file_name: str,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Классификация документа
        
        Args:
            title: Название документа
            file_name: Имя файла
            content: Содержимое документа (опционально)
            
        Returns:
            Результат классификации
        """
        text = f"{title} {file_name}".lower()
        if content:
            text += f" {content[:1000].lower()}"  # Первые 1000 символов
        
        # Поиск по паттернам
        classification = None
        confidence = 0.0
        matched_patterns = []
        
        for category, data in self.GOST_CLASSIFICATION.items():
            for pattern in data["patterns"]:
                if re.search(pattern, text, re.IGNORECASE):
                    matched_patterns.append({
                        "category": category,
                        "pattern": pattern,
                        "codes": data["codes"]
                    })
                    if not classification:
                        classification = category
                        confidence = 0.7
                    else:
                        confidence = min(0.9, confidence + 0.1)
        
        # Если не найдено, используем расширение файла
        if not classification:
            classification = self._classify_by_extension(file_name)
            confidence = 0.5
        
        return {
            "classification": classification,
            "confidence": confidence,
            "gost_codes": matched_patterns[0]["codes"] if matched_patterns else [],
            "matched_patterns": matched_patterns
        }
    
    def _classify_by_extension(self, file_name: str) -> str:
        """Классификация по расширению файла"""
        ext = file_name.split(".")[-1].lower()
        
        extension_map = {
            "pdf": "project_documentation",
            "dwg": "working_drawings",
            "xlsx": "specifications",
            "xls": "specifications",
            "doc": "project_documentation",
            "docx": "project_documentation"
        }
        
        return extension_map.get(ext, "other")
    
    def extract_metadata(
        self,
        file_name: str,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Извлечение метаданных из документа
        
        Args:
            file_name: Имя файла
            content: Содержимое документа
            
        Returns:
            Словарь метаданных
        """
        metadata = {
            "file_name": file_name,
            "file_extension": file_name.split(".")[-1].lower() if "." in file_name else "",
        }
        
        # Извлечение номера проекта из имени файла
        project_match = re.search(r"проект[_\s]*(\d+)", file_name, re.IGNORECASE)
        if project_match:
            metadata["project_number"] = project_match.group(1)
        
        # Извлечение даты из имени файла
        date_match = re.search(r"(\d{4}[-_]\d{2}[-_]\d{2})", file_name)
        if date_match:
            metadata["date_in_filename"] = date_match.group(1)
        
        # Извлечение версии
        version_match = re.search(r"[vV](\d+)", file_name)
        if version_match:
            metadata["version_in_filename"] = version_match.group(1)
        
        # Если есть содержимое, пытаемся извлечь больше информации
        if content:
            # Поиск email
            email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", content)
            if email_match:
                metadata["email"] = email_match.group(0)
            
            # Поиск телефона
            phone_match = re.search(r"\+?[7-8]?\s?\(?\d{3}\)?\s?\d{3}[-_]?\d{2}[-_]?\d{2}", content)
            if phone_match:
                metadata["phone"] = phone_match.group(0)
        
        return metadata


# Глобальный экземпляр классификатора
document_classifier = DocumentClassifier()

