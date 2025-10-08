# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: add_dependency
# Основной источник: C:\Bldr\core\meta_tools\dag_orchestrator.py
# Дубликаты (для справки):
#================================================================================
    def add_dependency(self, task_id: str, dependency_id: str) -> None:
        """Добавить зависимость между задачами"""
        if task_id in self.tasks and dependency_id in self.tasks:
            if dependency_id not in self.tasks[task_id].dependencies:
                self.tasks[task_id].dependencies.append(dependency_id)