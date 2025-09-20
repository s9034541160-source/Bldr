"""Conversation history management for SuperBuilder agents"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

class ConversationHistory:
    """Manage conversation history for users and sessions"""
    
    def __init__(self, history_dir: str = "data/conversation_history"):
        """
        Initialize conversation history manager.
        
        Args:
            history_dir: Directory to store conversation history files
        """
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_history_file_path(self, user_id: str, session_id: Optional[str] = None) -> Path:
        """
        Get file path for conversation history.
        
        Args:
            user_id: User identifier
            session_id: Optional session identifier
            
        Returns:
            Path to history file
        """
        if session_id:
            return self.history_dir / f"{user_id}_{session_id}.json"
        else:
            return self.history_dir / f"{user_id}.json"
    
    def add_message(self, user_id: str, message: Dict[str, Any], session_id: Optional[str] = None):
        """
        Add a message to conversation history.
        
        Args:
            user_id: User identifier
            message: Message to add (should contain 'role' and 'content' keys)
            session_id: Optional session identifier
        """
        history_file = self._get_history_file_path(user_id, session_id)
        
        # Load existing history
        history = self.get_history(user_id, session_id)
        
        # Add timestamp to message
        message_with_timestamp = message.copy()
        message_with_timestamp["timestamp"] = datetime.now().isoformat()
        
        # Add message to history
        history.append(message_with_timestamp)
        
        # Save updated history
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save conversation history: {e}")
    
    def get_history(self, user_id: str, session_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: User identifier
            session_id: Optional session identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of messages in conversation history
        """
        history_file = self._get_history_file_path(user_id, session_id)
        
        if not history_file.exists():
            return []
        
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
            
            # Return last N messages
            return history[-limit:] if limit > 0 else history
        except Exception as e:
            print(f"Warning: Failed to load conversation history: {e}")
            return []
    
    def clear_history(self, user_id: str, session_id: Optional[str] = None):
        """
        Clear conversation history for a user.
        
        Args:
            user_id: User identifier
            session_id: Optional session identifier
        """
        history_file = self._get_history_file_path(user_id, session_id)
        
        if history_file.exists():
            try:
                history_file.unlink()
            except Exception as e:
                print(f"Warning: Failed to clear conversation history: {e}")
    
    def get_formatted_history(self, user_id: str, session_id: Optional[str] = None, limit: int = 5) -> str:
        """
        Get formatted conversation history as a string for context.
        
        Args:
            user_id: User identifier
            session_id: Optional session identifier
            limit: Maximum number of messages to include
            
        Returns:
            Formatted history string
        """
        history = self.get_history(user_id, session_id, limit)
        
        if not history:
            return ""
        
        formatted_history = "Recent conversation history:\n"
        for msg in history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            formatted_history += f"[{timestamp}] {role}: {content}\n"
        
        return formatted_history

# Global conversation history manager
conversation_history = ConversationHistory()