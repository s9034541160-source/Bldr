# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _extract_version
# Основной источник: C:\Bldr\core\norms_scan.py
# Дубликаты (для справки):
#   - C:\Bldr\core\celery_norms.py
#================================================================================
    def _extract_version(self, filename: str) -> str:
        """
        Extract version from filename
        
        Args:
            filename: Name of the file
            
        Returns:
            Version string or 'unknown'
        """
        # Look for patterns like v2023, 2023, v.2023
        version_patterns = [
            r'[vв]?\.?\s*(\d{4})',  # v2023, 2023, v.2023, в2023
            r'(\d{4})\s*г\.?',      # 2023 г.
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return 'unknown'