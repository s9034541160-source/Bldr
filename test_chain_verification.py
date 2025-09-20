#!/usr/bin/env python3
"""
Test script to verify the full processing chain is working correctly
"""

import sys
import os
import json
import requests

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_full_chain():
    """Test the full processing chain from Telegram bot to coordinator"""
    print("🧪 Testing Full Processing Chain")
    print("=" * 50)
    
    # 1. Get authentication token
    print("1️⃣ Getting authentication token...")
    try:
        token_response = requests.post("http://localhost:8000/token")
        if token_response.status_code != 200:
            print(f"❌ Failed to get token: {token_response.status_code} - {token_response.text}")
            return False
            
        token = token_response.json()["access_token"]
        print(f"✅ Got token: {token[:20]}...")
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return False
    
    # 2. Test the AI chat endpoint with a simple query
    print("\n2️⃣ Testing AI chat endpoint...")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Test payload similar to what Telegram bot sends
        chat_payload = {
            'message': 'привет. расскажи о себе. что знаешь, что умеешь?',
            'context_search': True,
            'max_context': 3,
            'agent_role': 'coordinator',
            'request_context': {
                'channel': 'telegram',
                'chat_id': 123456789,  # Test chat ID
                'user_id': 987654321   # Test user ID
            }
        }
        
        response = requests.post(
            "http://localhost:8000/api/ai/chat",
            json=chat_payload,
            headers=headers,
            timeout=1800
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ AI chat successful")
            print(f"   🤖 Agent used: {result.get('agent_used')}")
            print(f"   📁 Context documents: {len(result.get('context_used', []))}")
            print(f"   ⚡ Processing time: {result.get('processing_time', 0):.2f}s")
            print(f"   💬 Response preview: {result.get('response', '')[:200]}...")
            return True
        else:
            print(f"❌ AI chat failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing AI chat: {e}")
        return False

def test_coordinator_directly():
    """Test the coordinator agent directly"""
    print("\n3️⃣ Testing Coordinator Agent Directly...")
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
        print(f"   Plan keys: {list(plan.keys()) if isinstance(plan, dict) else 'Not a dict'}")
        
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
    print("\n4️⃣ Testing Specialist Agents Manager...")
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

if __name__ == "__main__":
    print("🚀 STARTING FULL CHAIN VERIFICATION")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("Full Chain Test", test_full_chain),
        ("Coordinator Direct Test", test_coordinator_directly),
        ("Specialist Agents Test", test_specialist_agents)
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
        print("\n🎉 All tests passed! The full chain is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. There may be issues with the chain.")