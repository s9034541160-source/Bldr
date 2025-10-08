# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: get_role_responsibilities
# Основной источник: C:\Bldr\core\model_manager.py
# Дубликаты (для справки):
#   - C:\Bldr\core\config.py
#================================================================================
    def get_role_responsibilities(self, role: str) -> List[str]:
        """
        Get responsibilities for specific role.
        
        Args:
            role: Role name
            
        Returns:
            List of responsibilities
        """
        if role in MODELS_CONFIG:
            return MODELS_CONFIG[role].get('responsibilities', [])
        return []