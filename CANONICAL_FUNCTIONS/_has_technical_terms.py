# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _has_technical_terms
# Основной источник: C:\Bldr\integrated_structure_chunking_system.py
# Дубликаты (для справки):
#   - C:\Bldr\enhanced_structure_extractor.py
#================================================================================
def _has_technical_terms(text: str) -> bool:
    """Проверка на технические термины"""
    patterns = [
        r'\b(?:ГОСТ|СП|СНиП)\s+[\d.-]+',
        r'\b\d+(?:\.\d+)?\s*(?:мм|см|м|км|г|кг|т|МПа|кПа|°C)\b',
        r'\b(?:прочность|деформация|нагрузка|напряжение)\b'
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)