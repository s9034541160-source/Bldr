#!/usr/bin/env python3
"""
Test script for the multi-agent coordinator system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Set environment variable for OpenAI API key (not actually needed for LM Studio)
os.environ["OPENAI_API_KEY"] = "not-needed"

from core.agents.coordinator_agent import CoordinatorAgent
from core.agents.specialist_agents import SpecialistAgentsManager

def test_multi_agent_system():
    """Test the multi-agent system with a sample query"""
    print("Testing multi-agent coordinator system...")
    
    # Initialize the coordinator agent
    coordinator = CoordinatorAgent()
    print("✅ Coordinator agent initialized")
    
    # Initialize the specialist agents manager
    specialist_manager = SpecialistAgentsManager()
    print("✅ Specialist agents manager initialized")
    
    # Test query
    query = "Анализ LSR на СП31 + письмо"
    print(f"📝 Testing with query: {query}")
    
    # Generate plan
    print("🧠 Generating execution plan...")
    plan = coordinator.generate_plan(query)
    print(f"📋 Plan generated: {plan}")
    
    # Execute plan with specialist agents
    print("🏃 Executing plan with specialist agents...")
    results = specialist_manager.execute_plan(plan, None)  # No tools system for this test
    print(f"✅ Plan executed. Results: {results}")
    
    print("🎉 Multi-agent system test completed successfully!")

if __name__ == "__main__":
    test_multi_agent_system()