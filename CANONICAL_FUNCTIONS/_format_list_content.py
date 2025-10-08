# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _format_list_content
# Основной источник: C:\Bldr\recursive_hierarchical_chunker.py
# Дубликаты (для справки):
#   - C:\Bldr\integrated_structure_chunking_system.py
#================================================================================
    def _format_list_content(self, list_group: Dict[str, Any]) -> str:
        """Форматирование списка в текст"""
        content_parts = []
        
        for item in list_group.get('items', []):
            if isinstance(item, dict):
                marker = item.get('marker', '•')
                text = item.get('text', '')
                content_parts.append(f"{marker} {text}")
            else:
                content_parts.append(f"• {item}")
        
        return '\n'.join(content_parts)