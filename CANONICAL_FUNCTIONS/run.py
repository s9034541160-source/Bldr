# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: run
# Основной источник: C:\Bldr\system_launcher\gui_launcher.py
# Дубликаты (для справки):
#   - C:\Bldr\bldr_system_launcher.py
#================================================================================
    def run(self):
        """Запуск GUI"""
        try:
            # Обработка закрытия окна
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # Запуск главного цикла
            self.root.mainloop()
            
        except KeyboardInterrupt:
            self._on_closing()