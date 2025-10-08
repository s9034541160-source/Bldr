# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _categorize_error
# Основной источник: C:\Bldr\core\tools_system.py
# Дубликаты (для справки):
#================================================================================
    def _categorize_error(self, error_msg: str) -> str:
        """Categorize error based on message content"""
        error_msg_lower = error_msg.lower()
        
        if "invalid" in error_msg_lower or "missing" in error_msg_lower:
            return "validation"
        elif "io" in error_msg_lower or "file" in error_msg_lower or "path" in error_msg_lower:
            return "io"
        elif "import" in error_msg_lower or "module" in error_msg_lower:
            return "dependency"
        elif "network" in error_msg_lower or "connection" in error_msg_lower:
            return "network"
        else:
            return "processing"