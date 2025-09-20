#!/usr/bin/env python3
"""
Test script for the coordinator agent
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Set environment variable for OpenAI API key (not actually needed for LM Studio)
os.environ["OPENAI_API_KEY"] = "not-needed"

from core.agents.coordinator_agent import CoordinatorAgent

def test_coordinator_agent():
    """Test the coordinator agent"""
    print("Testing coordinator agent...")
    
    # Test creating a coordinator agent
    try:
        coordinator = CoordinatorAgent()
        print("✅ Coordinator agent created successfully")
        print(f"   System prompt length: {len(coordinator.system_prompt)} characters")
        print(f"   Tools available: {len(coordinator.tools)}")
    except Exception as e:
        print(f"❌ Error creating coordinator agent: {e}")
        return
    
    print("🎉 Coordinator agent test completed successfully!")

if __name__ == "__main__":
    test_coordinator_agent()