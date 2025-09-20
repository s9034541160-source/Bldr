#!/usr/bin/env python3
"""
Test script for the role-based agents system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Set environment variable for OpenAI API key (not actually needed for LM Studio)
os.environ["OPENAI_API_KEY"] = "not-needed"

from core.agents.roles_agents import RoleAgent, RolesAgentsManager

def test_roles_agents():
    """Test the role-based agents system"""
    print("Testing role-based agents system...")
    
    # Test creating a role agent
    try:
        coordinator_agent = RoleAgent("coordinator")
        print("✅ Coordinator role agent created successfully")
        print(f"   System prompt length: {len(coordinator_agent.system_prompt)} characters")
    except Exception as e:
        print(f"❌ Error creating coordinator agent: {e}")
        return
    
    # Test creating roles agents manager
    try:
        roles_manager = RolesAgentsManager()
        print("✅ Roles agents manager created successfully")
    except Exception as e:
        print(f"❌ Error creating roles manager: {e}")
        return
    
    # Test getting an agent from the manager
    try:
        chief_agent = roles_manager.get_agent("chief_engineer")
        print("✅ Chief engineer agent retrieved from manager successfully")
    except Exception as e:
        print(f"❌ Error getting chief engineer agent: {e}")
        return
    
    # Test role tools
    print(f"   Coordinator tools: {len(coordinator_agent.tools)}")
    print(f"   Chief engineer tools: {len(chief_agent.tools)}")
    
    print("🎉 Role-based agents system test completed successfully!")

if __name__ == "__main__":
    test_roles_agents()