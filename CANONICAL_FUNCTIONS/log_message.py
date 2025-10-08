# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: log_message
# Основной источник: C:\Bldr\bldr_gui.py
# Дубликаты (для справки):
#   - C:\Bldr\bldr_gui_manager.py
#================================================================================
    def log_message(self, message):
        """Thread-safe log: Queue if not main thread"""
        if threading.current_thread() is threading.main_thread():
            self._log_impl(message)
        else:
            self.log_queue.put(message)