# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: get_capabilities_prompt
# Основной источник: C:\Bldr\core\model_manager.py
# Дубликаты (для справки):
#   - C:\Bldr\core\config.py
#================================================================================
    def get_capabilities_prompt(self, role: str) -> Optional[str]:
        """
        Get capabilities prompt for specific role.
        
        Args:
            role: Role name
            
        Returns:
            Capabilities prompt string or None
        """
        return get_capabilities_prompt(role)