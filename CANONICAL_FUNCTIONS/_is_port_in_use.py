# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _is_port_in_use
# Основной источник: C:\Bldr\system_launcher\component_manager.py
# Дубликаты (для справки):
#   - C:\Bldr\system_launcher\diagnostic_tools.py
#================================================================================
    def _is_port_in_use(self, port: int) -> bool:
        """Проверка использования порта"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0