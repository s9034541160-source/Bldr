# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: start_monitoring
# Основной источник: C:\Bldr\system_launcher\component_manager.py
# Дубликаты (для справки):
#   - C:\Bldr\bldr_system_launcher.py
#   - C:\Bldr\system_launcher\gui_launcher.py
#================================================================================
    def start_monitoring(self):
        """Запуск мониторинга компонентов"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Component monitoring started")