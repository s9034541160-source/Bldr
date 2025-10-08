# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _calculate_technical_density
# Основной источник: C:\Bldr\integrated_structure_chunking_system.py
# Дубликаты (для справки):
#   - C:\Bldr\enhanced_structure_extractor.py
#================================================================================
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