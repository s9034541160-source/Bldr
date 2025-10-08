# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: clear_history
# Основной источник: C:\Bldr\core\agents\conversation_history_compressed.py
# Дубликаты (для справки):
#   - C:\Bldr\core\agents\conversation_history.py
#================================================================================
    def clear_history(self, user_id: str):
        """
        Clear history for user (e.g., new session).
        
        Args:
            user_id: User identifier
        """
        if user_id in self.histories:
            self.histories[user_id] = []
            self._save_history()