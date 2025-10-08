# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: clear_logs
# Основной источник: C:\Bldr\bldr_gui.py
# Дубликаты (для справки):
#   - C:\Bldr\bldr_system_launcher.py
#================================================================================
    def clear_logs(self):
        """Clear the log area"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)