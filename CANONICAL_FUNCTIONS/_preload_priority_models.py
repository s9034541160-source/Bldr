# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _preload_priority_models
# Основной источник: C:\Bldr\core\model_manager.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _preload_priority_models(self):
        """Preload priority models to ensure fast response times."""
        priority_roles = ["coordinator", "chief_engineer", "analyst"]
        print("Предзагрузка приоритетных моделей...")
        
        for role in priority_roles:
            if role in MODELS_CONFIG:
                config = MODELS_CONFIG[role]
                try:
                    print(f"Загрузка модели {config['model']} для роли {role} с base_url {config['base_url']}")
                    client = self.get_model_client(role)
                    if client:
                        print(f"✓ Предзагружена модель для роли {role}")
                    else:
                        print(f"✗ Не удалось загрузить модель для роли {role}")
                except Exception as e:
                    print(f"✗ Ошибка при загрузке модели для роли {role}: {e}")
        
        print("Предзагрузка завершена")