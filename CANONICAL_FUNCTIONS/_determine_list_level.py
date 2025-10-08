# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _determine_list_level
# Основной источник: C:\Bldr\integrated_structure_chunking_system.py
# Дубликаты (для справки):
#   - C:\Bldr\enhanced_structure_extractor.py
#================================================================================
def _determine_list_level(self, line: str) -> int:
    """Определение уровня элемента списка"""
    leading_spaces = len(line) - len(line.lstrip())
    return max(1, leading_spaces // 4 + 1)