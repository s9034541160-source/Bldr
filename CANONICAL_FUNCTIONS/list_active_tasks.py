# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: list_active_tasks
# Основной источник: C:\Bldr\core\async_ai_processor.py
# Дубликаты (для справки):
#   - C:\Bldr\core\meta_tools\celery_integration.py
#================================================================================
    def list_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """List all active tasks"""
        return {
            task_id: asdict(task_result) 
            for task_id, task_result in self.active_tasks.items()
        }