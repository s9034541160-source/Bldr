#!/usr/bin/env python3
"""Test script to verify voice transcription functionality"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from core.agents.coordinator_agent import CoordinatorAgent

def test_voice_transcription():
    """Test voice transcription functionality"""
    # Initialize coordinator agent
    coordinator = CoordinatorAgent(lm_studio_url="http://localhost:1234/v1")
    
    # Set request context with audio path
    coordinator.set_request_context({
        "user_id": "test_user",
        "audio_path": "test_voice_message.ogg",
        "channel": "ai_shell"
    })
    
    # Test voice transcription query
    print("=== Test 1: Voice transcription query ===")
    voice_query = "Пожалуйста, транскрибируй это голосовое сообщение и проанализируй его содержание. Если есть вопросы о строительных нормах, найди подходящие ответы в базе знаний."
    print(f"Query: {voice_query}")
    
    # Generate plan
    plan = coordinator.generate_plan(voice_query)
    print(f"Generated plan: {plan}")
    
    # Check if the plan correctly routes to voice transcription
    tasks = plan.get("tasks", [])
    has_transcribe_task = any(task.get("tool") == "transcribe_audio" for task in tasks)
    
    if has_transcribe_task:
        print("✅ SUCCESS: Plan correctly routes to voice transcription")
    else:
        print("❌ FAILURE: Plan does not route to voice transcription")
    
    # Test processing the query
    print("\n=== Test 2: Processing voice query ===")
    response = coordinator.process_query(voice_query)
    print(f"Response: {response}")
    
    # Test with different voice-related queries
    print("\n=== Test 3: Different voice queries ===")
    voice_queries = [
        "Транскрибируй голосовое сообщение",
        "Transcribe this voice message",
        "Проанализируй аудио"
    ]
    
    for query in voice_queries:
        plan = coordinator.generate_plan(query)
        tasks = plan.get("tasks", [])
        has_transcribe_task = any(task.get("tool") == "transcribe_audio" for task in tasks)
        
        if has_transcribe_task:
            print(f"✅ '{query}' -> correctly routed to voice transcription")
        else:
            print(f"❌ '{query}' -> not routed to voice transcription")

if __name__ == "__main__":
    test_voice_transcription()