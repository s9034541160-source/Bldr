"""Conversation History Manager with Compression and Compacting"""

import json
import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Conditional imports for optional dependencies
LANGCHAIN_AVAILABLE = False
TIKTOKEN_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    ChatOpenAI = None

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    tiktoken = None

# Config (сделай global или из core.config)
HISTORY_CONFIG = {
    "max_messages": 20,  # Total per user
    "max_recent_messages": 8,  # В prompt: recent only
    "max_tokens": 1500,  # В formatted history
    "compact_every": 10,  # Compact after N new msgs
    "use_llm_compact": True,  # LLM summary или rule-based
    "compact_model": "Qwen/Qwen2.5-3B-Instruct-GGUF",  # Fast model для summary
    "lm_studio_url": "http://localhost:1234/v1",
    "storage_file": "data/conversation_history.json",  # Persistent
    "session_timeout": timedelta(hours=1)  # Reset old sessions
}

class CompressedConversationHistory:
    """Manager for conversation history with compression."""
    
    def __init__(self, storage_file: str = HISTORY_CONFIG["storage_file"]):
        """
        Initialize compressed conversation history manager.
        
        Args:
            storage_file: Path to storage file for persistent history
        """
        # Create directory if it doesn't exist
        storage_path = Path(storage_file)
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.storage_file = storage_file
        self.histories: Dict[str, List[Dict[str, Any]]] = self._load_history()
        self.tokenizer = None
        if TIKTOKEN_AVAILABLE and tiktoken:
            try:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
            except Exception:
                self.tokenizer = None
    
    def _load_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load history from JSON."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Clean old sessions (older than timeout)
                    now = datetime.now()
                    for user_id in list(data.keys()):
                        data[user_id] = [msg for msg in data[user_id] 
                                       if (now - datetime.fromisoformat(msg.get('timestamp', now.isoformat()))) < HISTORY_CONFIG["session_timeout"]]
                    return data
            except Exception as e:
                print(f"Warning: Failed to load conversation history: {e}")
                return {}
        return {}
    
    def _save_history(self):
        """Save history to JSON."""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.histories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save conversation history: {e}")
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate tokens (fallback if no tokenizer)."""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass
        # Fallback to character-based estimation (rough RU/EN avg)
        return len(text) // 4
    
    def _filter_noise(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Selective filtering: Remove greetings/repeats (no losses, just noise)."""
        filtered = []
        noise_keywords = ["привет", "hello", "hi", "расскажи о себе", "что ты умеешь", "здравствуй", "hey"]  # Add more
        for msg in messages:
            content_lower = msg.get("content", "").lower()
            # Skip short greetings/repeats (keep if task-related)
            if len(msg["content"]) < 20 and any(kw in content_lower for kw in noise_keywords):
                continue
            # Dedup: Skip if similar to previous (simple cosine or exact)
            if filtered and content_lower == filtered[-1].get("content", "").lower():
                continue
            filtered.append(msg)
        return filtered
    
    def _compact_prefix(self, user_id: str, prefix_msgs: List[Dict[str, Any]]) -> str:
        """Compact old messages into summary (hierarchical, minimal losses)."""
        if not prefix_msgs:
            return ""
        
        if not HISTORY_CONFIG["use_llm_compact"] or not LANGCHAIN_AVAILABLE or not ChatOpenAI:
            # Rule-based: Extract key entities (no LLM, fast, ~no losses)
            return self._compact_prefix_rule_based(prefix_msgs)
        
        # LLM-based summary (compact, but accurate)
        try:
            llm = ChatOpenAI(
                base_url=HISTORY_CONFIG["lm_studio_url"],
                model=HISTORY_CONFIG["compact_model"],
                temperature=0.0
            )
            prefix_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in prefix_msgs[-10:]])  # Last 10 for summary
            prompt = f"""Summarize this conversation prefix in 1-2 sentences, keeping key facts (tasks, files, decisions, norms). Be concise, no losses of important info.

Prefix:
{prefix_text}

Summary:"""
            response = llm.invoke(prompt)
            # Handle different response types safely
            if hasattr(response, 'content') and isinstance(response.content, str):
                summary = response.content.strip()
            else:
                summary = str(response).strip()
            # Append as special msg
            if user_id in self.histories:
                self.histories[user_id].insert(0, {  # Prepend to history
                    "role": "summary",
                    "content": summary,
                    "covers_msgs": len(prefix_msgs),
                    "timestamp": datetime.now().isoformat()
                })
            return summary
        except Exception as e:
            print(f"Compact error: {e}")
            # Fallback to rule-based
            return self._compact_prefix_rule_based(prefix_msgs)
    
    def _compact_prefix_rule_based(self, prefix_msgs: List[Dict[str, Any]]) -> str:
        """Rule-based compacting without LLM."""
        entities = []
        for msg in prefix_msgs:
            # Simple NER-like: Extract tasks/files/norms
            tasks = re.findall(r'(задача|письмо|смета|норма|СП-\d+|файл|генерация)', msg.get("content", ""), re.I)
            files = re.findall(r'(docx|pdf|xlsx|path:.*?[\\/])', msg.get("content", ""), re.I)
            if tasks or files:
                entities.append(f"{msg['role']}: {', '.join(tasks + files)}")
        return "Summary: " + " | ".join(entities[-5:])  # Last 5 key points
    
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
    
    def _periodic_compact(self, user_id: str):
        """Full compact: Summarize if > threshold tokens."""
        if user_id not in self.histories:
            return
            
        history = self.histories[user_id]
        total_tokens = sum(self._estimate_tokens(msg["content"]) for msg in history if msg["role"] != "summary")
        if total_tokens > HISTORY_CONFIG["max_tokens"] * 2:  # Buffer
            # Compact half
            mid = len(history) // 2
            prefix = history[:mid]
            summary = self._compact_prefix(user_id, prefix)
            self.histories[user_id] = [{"role": "summary", "content": summary}] + history[mid:]
            self._save_history()
    
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
    
    def get_history_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics about conversation history for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with history statistics
        """
        if user_id not in self.histories:
            return {
                "total_messages": 0,
                "total_tokens": 0,
                "summary_count": 0,
                "recent_messages": 0
            }
        
        history = self.histories[user_id]
        total_tokens = sum(self._estimate_tokens(msg["content"]) for msg in history)
        summary_count = sum(1 for msg in history if msg["role"] == "summary")
        
        return {
            "total_messages": len(history),
            "total_tokens": total_tokens,
            "summary_count": summary_count,
            "recent_messages": len(history[-HISTORY_CONFIG["max_recent_messages"]:] if history else [])
        }
    
    def clear_history(self, user_id: str):
        """
        Clear history for user (e.g., new session).
        
        Args:
            user_id: User identifier
        """
        if user_id in self.histories:
            self.histories[user_id] = []
            self._save_history()
    
    def get_full_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get full history for user (including summaries).
        
        Args:
            user_id: User identifier
            
        Returns:
            List of all messages in history
        """
        return self.histories.get(user_id, []).copy()

# Global compressed conversation history manager
compressed_conversation_history = CompressedConversationHistory()