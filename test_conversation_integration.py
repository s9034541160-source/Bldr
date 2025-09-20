#!/usr/bin/env python3
"""Test script to verify conversation history integration"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from core.agents.conversation_history import conversation_history

def test_conversation_integration():
    """Test conversation history integration"""
    user_id = "integration_test_user"
    
    # Clear any existing history
    conversation_history.clear_history(user_id)
    
    # Simulate a conversation
    messages = [
        {"role": "user", "content": "Привет"},
        {"role": "assistant", "content": "Привет! Рад вас видеть. Чем могу помочь?"},
        {"role": "user", "content": "Расскажи о своих возможностях"},
        {"role": "assistant", "content": "Я могу помочь с различными задачами в строительной сфере, включая поиск нормативной документации, расчет смет, создание проектной документации и многое другое."},
        {"role": "user", "content": "Спасибо за информацию"}
    ]
    
    # Add messages to history
    for message in messages:
        conversation_history.add_message(user_id, message)
        print(f"Added message: {message['role']}: {message['content']}")
    
    # Retrieve and display history
    print("\nRetrieved conversation history:")
    history = conversation_history.get_history(user_id)
    for i, msg in enumerate(history):
        print(f"{i+1}. {msg['role']}: {msg['content']}")
    
    # Test formatted history
    print("\nFormatted history (last 3 messages):")
    formatted = conversation_history.get_formatted_history(user_id, limit=3)
    print(formatted)
    
    # Test that history is persisted
    print("\nTesting persistence by creating new instance...")
    from core.agents.conversation_history import ConversationHistory
    new_history = ConversationHistory()
    retrieved_history = new_history.get_history(user_id)
    print(f"Retrieved {len(retrieved_history)} messages from persisted history")
    
    # Clear history
    conversation_history.clear_history(user_id)
    print("\nHistory cleared successfully!")
    
    # Verify it's cleared
    final_history = conversation_history.get_history(user_id)
    print(f"Final history length: {len(final_history)}")

if __name__ == "__main__":
    test_conversation_integration()