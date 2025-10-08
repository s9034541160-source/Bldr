# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: get_service_config
# Основной источник: C:\Bldr\core\plugin_manager.py
# Дубликаты (для справки):
#   - C:\Bldr\plugins\third_party_integration_plugin.py
#================================================================================
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        Get configuration for a service
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service configuration or empty dict if not found
        """
        return self.third_party_configs.get(service_name, {})