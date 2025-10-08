# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: is_success
# Основной источник: C:\Bldr\core\tools_system.py
# Дубликаты (для справки):
#   - C:\Bldr\core\tools_adapter.py
#================================================================================
    def is_success(self) -> bool:
        return self.status == 'success'