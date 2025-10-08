# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: get_role_exclusions
# Основной источник: C:\Bldr\core\model_manager.py
# Дубликаты (для справки):
#   - C:\Bldr\core\config.py
#================================================================================
    def get_role_exclusions(self, role: str) -> List[str]:
        """
        Get exclusions for specific role.
        
        Args:
            role: Role name
            
        Returns:
            List of exclusions
        """
        if role in MODELS_CONFIG:
            return MODELS_CONFIG[role].get('exclusions', [])
        return []