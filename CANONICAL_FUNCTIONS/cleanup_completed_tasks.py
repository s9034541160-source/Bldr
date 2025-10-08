# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: cleanup_completed_tasks
# Основной источник: C:\Bldr\core\meta_tools\celery_integration.py
# Дубликаты (для справки):
#   - C:\Bldr\async_ai_improvements.py
#================================================================================
    def cleanup_completed_tasks(self) -> int:
        """
        Очистить завершенные задачи из кеша
        
        Returns:
            Количество очищенных задач
        """
        completed_tasks = []
        
        for task_id, result in self.active_tasks.items():
            if result.ready():
                completed_tasks.append(task_id)
        
        for task_id in completed_tasks:
            del self.active_tasks[task_id]
        
        logger.info(f"Очищено {len(completed_tasks)} завершенных задач")
        return len(completed_tasks)