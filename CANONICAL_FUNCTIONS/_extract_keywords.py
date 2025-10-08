# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _extract_keywords
# Основной источник: C:\Bldr\working_frontend_rag_integration.py
# Дубликаты (для справки):
#   - C:\Bldr\enhanced_structure_extractor.py
#================================================================================
    def _extract_keywords(self, content: str) -> List[str]:
        """Извлечение ключевых слов"""
        
        keywords = []
        
        # Технические термины
        tech_patterns = [
            r'\b(?:ГОСТ|СП|СНиП)\s+[\d.-]+',
            r'\b\d+(?:\.\d+)?\s*(?:мм|см|м|км|кг|т|МПа|°C|кВт|Вт)\b',
            r'\b(?:теплопроводность|сопротивление|коэффициент|температура|влажность)\b',
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            keywords.extend([m.strip() for m in matches])
        
        # Ограничиваем количество и убираем дубликаты
        return list(dict.fromkeys(keywords))[:15]