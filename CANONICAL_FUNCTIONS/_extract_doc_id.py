# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _extract_doc_id
# Основной источник: C:\Bldr\core\norms_processor.py
# Дубликаты (для справки):
#   - C:\Bldr\core\celery_norms.py
#================================================================================
    def _extract_doc_id(self, filename: str) -> Optional[str]:
        """
        Extract document ID from filename
        
        Args:
            filename: Name of the file
            
        Returns:
            Document ID or None
        """
        filename_lower = filename.lower()
        
        # Patterns for common document types
        patterns = [
            r'(?:сп|гост|снип|фз|тк|санпин|рд|гэсн|фер)-?(\d+[.\d]*)',  # СП31, ГОСТ 123, ФЗ-44
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename_lower, re.IGNORECASE)
            if match:
                # Extract the base part and number
                base_match = re.search(r'(?:сп|гост|снип|фз|тк|санпин|рд|гэсн|фер)', filename_lower, re.IGNORECASE)
                if base_match:
                    base = base_match.group(0).upper()
                    number = match.group(1)
                    return f"{base}{number}"
        
        return None