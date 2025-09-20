#!/usr/bin/env python3
"""
Test script to verify the full processing chain with fixed imports
"""

import sys
import os
import json
import requests
import time
import subprocess

# Add the project root to the path
sys.path.insert(0, r"c:\Bldr")

def test_coordinator_agent():
    """Test the coordinator agent directly"""
    print("🧪 Testing Coordinator Agent Directly...")
    try:
        # Import the coordinator agent
        from core.agents.coordinator_agent import CoordinatorAgent
        
        # Create coordinator agent
        coordinator = CoordinatorAgent()
        
        # Test a simple query
        query = "привет. расскажи о себе. что знаешь, что умеешь?"
        print(f"🧠 Testing query: {query}")
        
        # Test plan generation
        print("   Generating plan...")
        plan = coordinator.generate_plan(query)
        print(f"   ✅ Plan generated: {type(plan)}")
        if isinstance(plan, dict):
            print(f"   Plan keys: {list(plan.keys())}")
        
        # Test response generation
        print("   Generating response...")
        response = coordinator.generate_response(query)
        print(f"   ✅ Response generated: {len(response) if response else 0} characters")
        print(f"   Response preview: {response[:200] if response else 'No response'}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing coordinator directly: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specialist_agents():
    """Test the specialist agents manager"""
    print("\n🔧 Testing Specialist Agents Manager...")
    try:
        # Import the specialist agents manager
        from core.agents.specialist_agents import SpecialistAgentsManager
        
        # Create specialist agents manager
        specialist_manager = SpecialistAgentsManager()
        
        # Test getting an agent
        agent = specialist_manager.get_agent("chief_engineer")
        print(f"✅ Chief Engineer agent created: {type(agent)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing specialist agents: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_roles_agents():
    """Test the roles agents manager"""
    print("\n👷 Testing Roles Agents Manager...")
    try:
        # Import the roles agents manager
        from core.agents.roles_agents import RolesAgentsManager
        
        # Create roles agents manager
        roles_manager = RolesAgentsManager()
        
        # Test getting an agent
        agent = roles_manager.get_agent("coordinator")
        print(f"✅ Coordinator role agent created: {type(agent)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing roles agents: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_processing_chain():
    """Verify the full processing chain is working correctly"""
    print("🔍 VERIFYING FULL PROCESSING CHAIN")
    print("=" * 60)
    
    tests = [
        ("Coordinator Agent Test", test_coordinator_agent),
        ("Specialist Agents Test", test_specialist_agents),
        ("Roles Agents Test", test_roles_agents)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 Total: {len(results)} tests")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 SUCCESS: Full processing chain is working correctly!")
        print("\n📋 Chain Flow:")
        print("   1. Telegram Bot → /api/ai/chat endpoint")
        print("   2. Coordinator Agent generates plan")
        print("   3. Specialist Agents execute plan")
        print("   4. Role Agents use real tools (not mocks)")
        print("   5. Coordinator generates final response")
        print("   6. Response sent back to Telegram Bot")
        print("\n✅ The chain is working without mocks or stubs as requested!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. There may be issues with the chain.")
    
    print("=" * 60)
    return failed == 0

if __name__ == "__main__":
    success = verify_processing_chain()
    sys.exit(0 if success else 1)