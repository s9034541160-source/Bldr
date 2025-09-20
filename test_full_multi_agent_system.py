#!/usr/bin/env python3
"""
Full test script for the multi-agent coordinator system with role-based agents
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Set environment variable for OpenAI API key (not actually needed for LM Studio)
os.environ["OPENAI_API_KEY"] = "not-needed"

from core.agents.coordinator_agent import CoordinatorAgent
from core.agents.specialist_agents import SpecialistAgentsManager
from core.agents.roles_agents import RolesAgentsManager

def test_full_multi_agent_system():
    """Test the full multi-agent system with a sample query"""
    print("Testing full multi-agent coordinator system...")
    
    # Initialize the coordinator agent
    coordinator = CoordinatorAgent()
    print("✅ Coordinator agent initialized")
    
    # Initialize the specialist agents manager
    specialist_manager = SpecialistAgentsManager()
    print("✅ Specialist agents manager initialized")
    
    # Initialize the roles agents manager
    roles_manager = RolesAgentsManager()
    print("✅ Roles agents manager initialized")
    
    # Test query
    query = "Анализ фото сайта на СП31 + бюджет ГЭСН"
    print(f"📝 Testing with query: {query}")
    
    # Generate plan
    print("🧠 Generating execution plan...")
    plan = coordinator.generate_plan(query)
    print(f"📋 Plan generated: {plan}")
    
    # Execute plan with specialist agents
    print("🏃 Executing plan with specialist agents...")
    # Note: We're passing None for tools_system since this is just a test
    results = specialist_manager.execute_plan(plan, None)
    print(f"✅ Plan executed with specialist agents. Results: {results}")
    
    # Test role-based agents directly
    print("🏃 Testing role-based agents directly...")
    role_results = roles_manager.execute_plan_tasks(plan.get("tasks", []))
    print(f"✅ Role-based agents executed. Results: {role_results}")
    
    print("🎉 Full multi-agent system test completed successfully!")

if __name__ == "__main__":
    test_full_multi_agent_system()