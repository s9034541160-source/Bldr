# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: __post_init__
# Основной источник: C:\Bldr\core\async_ai_processor.py
# Дубликаты (для справки):
#   - C:\Bldr\core\process_tracker.py
#   - C:\Bldr\core\meta_tools\dag_orchestrator.py
#   - C:\Bldr\core\meta_tools\dag_orchestrator.py
#================================================================================
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()