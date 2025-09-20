#!/usr/bin/env python3
"""Test script to verify coordinator configuration changes"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from core.agents.coordinator_agent import CoordinatorAgent
from core.config import MODELS_CONFIG

def test_coordinator_config():
    """Test coordinator configuration changes"""
    print("=== Testing Coordinator Configuration ===")
    
    # Check the coordinator model configuration
    coordinator_config = MODELS_CONFIG.get("coordinator", {})
    model_name = coordinator_config.get("model", "")
    print(f"Coordinator model: {model_name}")
    
    if model_name == "qwen/qwen2.5-vl-7b":
        print("✅ SUCCESS: Coordinator model correctly updated to qwen/qwen2.5-vl-7b")
    else:
        print(f"❌ FAILURE: Coordinator model is {model_name}, expected qwen/qwen2.5-vl-7b")
    
    # Initialize coordinator agent
    coordinator = CoordinatorAgent(lm_studio_url="http://localhost:1234/v1")
    
    # Check agent configuration
    agent_config = coordinator.agent_executor
    max_iterations = agent_config.max_iterations
    max_execution_time = agent_config.max_execution_time
    
    print(f"Max iterations: {max_iterations}")
    print(f"Max execution time: {max_execution_time} seconds")
    
    if max_iterations == 4:
        print("✅ SUCCESS: Max iterations correctly set to 4")
    else:
        print(f"❌ FAILURE: Max iterations is {max_iterations}, expected 4")
    
    if max_execution_time == 3600.0:
        print("✅ SUCCESS: Max execution time correctly set to 3600.0 seconds (1 hour)")
    else:
        print(f"❌ FAILURE: Max execution time is {max_execution_time}, expected 3600.0")
    
    # Test simple query
    print("\n=== Testing Simple Query ===")
    start_time = time.time()
    response = coordinator.process_query("привет")
    end_time = time.time()
    
    print(f"Response: {response}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    
    if end_time - start_time < 1.0:
        print("✅ SUCCESS: Simple query processed quickly")
    else:
        print("❌ FAILURE: Simple query took too long")
    
    # Test voice query routing
    print("\n=== Testing Voice Query Routing ===")
    coordinator.set_request_context({
        "user_id": "test_user",
        "audio_path": "test_voice_message.ogg",
        "channel": "ai_shell"
    })
    
    voice_query = "Пожалуйста, транскрибируй это голосовое сообщение"
    plan = coordinator.generate_plan(voice_query)
    
    print(f"Generated plan: {plan}")
    
    # Check if the plan correctly routes to voice transcription
    tasks = plan.get("tasks", [])
    has_transcribe_task = any(task.get("tool") == "transcribe_audio" for task in tasks)
    
    if has_transcribe_task:
        print("✅ SUCCESS: Voice query correctly routed to transcription tool")
    else:
        print("❌ FAILURE: Voice query not routed to transcription tool")

if __name__ == "__main__":
    test_coordinator_config()