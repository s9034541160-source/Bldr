# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _count_technical_terms
# Основной источник: C:\Bldr\recursive_hierarchical_chunker.py
# Дубликаты (для справки):
#   - C:\Bldr\integrated_structure_chunking_system.py
#================================================================================
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