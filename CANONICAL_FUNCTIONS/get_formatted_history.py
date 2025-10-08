# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: get_formatted_history
# Основной источник: C:\Bldr\core\agents\conversation_history_compressed.py
# Дубликаты (для справки):
#   - C:\Bldr\core\agents\conversation_history.py
#================================================================================
    def get_formatted_history(self, user_id: str, max_tokens: Optional[int] = None) -> str:
        """
        Get formatted history for prompt: Recent + summaries (compressed).
        
        Args:
            user_id: User identifier
            max_tokens: Maximum tokens for formatted history
            
        Returns:
            Formatted history string
        """
        if user_id not in self.histories:
            return ""
        
        max_tokens = max_tokens or HISTORY_CONFIG["max_tokens"]
        history = self.histories[user_id]
        
        # Prioritize: Summaries first (old), then recent verbatim
        formatted = []
        current_tokens = 0
        
        # Add summaries (old context)
        for msg in reversed(history):  # Reverse to get oldest first
            if msg["role"] == "summary":
                content = f"Summary of previous: {msg['content']}"
                tokens = self._estimate_tokens(content)
                if current_tokens + tokens > max_tokens:
                    break
                formatted.append(content)
                current_tokens += tokens
        
        # Add recent messages verbatim (last N or until tokens)
        recent = history[-HISTORY_CONFIG["max_recent_messages"]:]
        for msg in reversed(recent):  # Chronological in prompt
            if msg["role"] == "summary":
                continue  # Already added
            content = f"{msg['role']}: {msg['content']}"
            tokens = self._estimate_tokens(content)
            if current_tokens + tokens > max_tokens:
                break
            formatted.append(content)
            current_tokens += tokens
        
        # Reverse back to chronological
        formatted.reverse()
        return "\n".join(formatted) if formatted else ""