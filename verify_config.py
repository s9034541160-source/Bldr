#!/usr/bin/env python3
"""Simple script to verify coordinator configuration"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from core.agents.coordinator_agent import CoordinatorAgent
from core.config import MODELS_CONFIG

def main():
    print("=== Verifying Coordinator Configuration ===")
    
    # Check coordinator model configuration
    coordinator_config = MODELS_CONFIG.get("coordinator", {})
    model_name = coordinator_config.get("model", "")
    print(f"Coordinator model: {model_name}")
    
    if model_name == "qwen/qwen2.5-vl-7b":
        print("✅ SUCCESS: Coordinator model correctly set to qwen/qwen2.5-vl-7b")
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

if __name__ == "__main__":
    main()