# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _format_table_content
# Основной источник: C:\Bldr\recursive_hierarchical_chunker.py
# Дубликаты (для справки):
#   - C:\Bldr\integrated_structure_chunking_system.py
#================================================================================
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