# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: get_task_status
# Основной источник: C:\Bldr\core\async_ai_processor.py
# Дубликаты (для справки):
#   - C:\Bldr\async_ai_improvements.py
#   - C:\Bldr\core\meta_tools\celery_integration.py
#================================================================================
    def get_task_status(self, task_id: str) -> Optional[AITaskResult]:
        """Get status of a specific task"""
        return self.active_tasks.get(task_id)