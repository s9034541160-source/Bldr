#!/usr/bin/env python3
"""
Basic test for coordinator agent
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Set environment variable for OpenAI API key (not actually needed for LM Studio)
os.environ["OPENAI_API_KEY"] = "not-needed"

# Add the core directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from agents.coordinator_agent import CoordinatorAgent

def test_coordinator_basic():
    """Test the coordinator agent basic functionality"""
    print("Testing coordinator agent basic functionality...")
    
    # Initialize the coordinator agent
    coordinator = CoordinatorAgent()
    print("✅ Coordinator agent initialized")
    
    # Test fallback plan generation directly
    print("🧠 Testing fallback plan generation...")
    fallback_plan = coordinator._generate_fallback_plan("Анализ LSR на СП31 + письмо")
    print(f"📋 Fallback plan: {fallback_plan}")
    
    # Parse the fallback plan
    import json
    plan_json = json.loads(fallback_plan)
    print(f"📋 Parsed fallback plan: {plan_json}")
    
    print("🎉 Basic coordinator test completed successfully!")

if __name__ == "__main__":
    test_coordinator_basic()