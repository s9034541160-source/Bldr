# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: get_model_stats
# Основной источник: C:\Bldr\core\model_manager.py
# Дубликаты (для справки):
#   - C:\Bldr\core\trainer.py
#================================================================================
    def get_model_stats(self) -> Dict[str, Any]:
        """
        Get statistics about loaded models and cache.
        
        Returns:
            Dictionary with model statistics
        """
        return {
            "loaded_models": len(self.model_cache),
            "max_cache_size": self.cache_size,
            "ttl_minutes": self.ttl_minutes,
            "model_details": {
                role: {
                    "usage_stats": {
                        "call_count": self._get_model_call_count(role),  # Track actual model usage
                        "last_access": str(self.last_access.get(f"{role}_{MODELS_CONFIG[role]['base_url']}_{MODELS_CONFIG[role]['model']}", "Never"))
                    }
                } for role in MODELS_CONFIG.keys()
            }
        }