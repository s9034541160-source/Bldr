# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: add_message
# Основной источник: C:\Bldr\core\agents\conversation_history_compressed.py
# Дубликаты (для справки):
#   - C:\Bldr\core\agents\conversation_history.py
#================================================================================
    def add_message(self, user_id: str, message: Dict[str, Any]):
        """
        Add message and auto-compact if needed.
        
        Args:
            user_id: User identifier
            message: Message to add (should contain 'role' and 'content' keys)
        """
        if user_id not in self.histories:
            self.histories[user_id] = []
        
        # Add timestamp if missing
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        self.histories[user_id].append(message)
        
        # Limit total + filter noise
        history = self._filter_noise(self.histories[user_id])
        if len(history) > HISTORY_CONFIG["max_messages"]:
            # Compact oldest (prefix)
            prefix_len = len(history) - HISTORY_CONFIG["max_recent_messages"]
            prefix = history[:prefix_len]
            summary = self._compact_prefix(user_id, prefix)
            # Replace prefix with summary
            recent = history[prefix_len:]
            self.histories[user_id] = [{"role": "summary", "content": summary, "timestamp": history[0]["timestamp"]}] + recent
        
        # Periodic compact (e.g., every 10 adds)
        if len(self.histories[user_id]) % HISTORY_CONFIG["compact_every"] == 0:
            self._periodic_compact(user_id)
        
        self._save_history()