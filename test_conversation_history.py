#!/usr/bin/env python3
"""Test script to verify conversation history functionality"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from core.agents.conversation_history import conversation_history

def test_conversation_history():
    """Test conversation history functionality"""
    user_id = "test_user"
    
    # Clear any existing history for this user
    conversation_history.clear_history(user_id)
    
    # Add some messages
    conversation_history.add_message(user_id, {
        "role": "user",
        "content": "Привет, как дела?"
    })
    
    conversation_history.add_message(user_id, {
        "role": "assistant",
        "content": "Привет! У меня всё хорошо, спасибо. Как я могу вам помочь?"
    })
    
    conversation_history.add_message(user_id, {
        "role": "user",
        "content": "Расскажи о себе"
    })
    
    # Get history
    history = conversation_history.get_history(user_id, limit=5)
    print("Conversation history:")
    for msg in history:
        print(f"  {msg['role']}: {msg['content']}")
    
    # Get formatted history
    formatted_history = conversation_history.get_formatted_history(user_id, limit=3)
    print("\nFormatted history:")
    print(formatted_history)
    
    # Clear history
    conversation_history.clear_history(user_id)
    print("\nHistory cleared")

if __name__ == "__main__":
    test_conversation_history()