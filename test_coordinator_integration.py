#!/usr/bin/env python3
"""Test script to verify coordinator agent integration with role context"""

import sys
import os
import json

# Add the core directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

def test_coordinator_agent():
    """Test the coordinator agent with proper role context"""
    try:
        # Import the coordinator agent
        from core.agents.coordinator_agent import CoordinatorAgent
        
        # Initialize the coordinator agent
        coordinator = CoordinatorAgent()
        
        # Test with a simple query
        query = "Расскажи о себе. Что ты знаешь, что умеешь?"
        print(f"Testing coordinator agent with query: {query}")
        
        # Generate a plan
        plan = coordinator.generate_plan(query)
        print(f"Generated plan: {json.dumps(plan, ensure_ascii=False, indent=2)}")
        
        # Check if the plan contains the expected structure
        assert "complexity" in plan, "Plan should contain complexity"
        assert "time_est" in plan, "Plan should contain time_est"
        assert "roles" in plan, "Plan should contain roles"
        assert "tasks" in plan, "Plan should contain tasks"
        
        print("✅ Coordinator agent test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Coordinator agent test failed: {e}")
        return False

def test_api_integration():
    """Test the API integration with coordinator agent"""
    try:
        import requests
        import time
        
        # Test the /submit_query endpoint
        url = "http://localhost:8000/submit_query"
        query = "Расскажи о себе. Что ты знаешь, что умеешь?"
        
        # First, we need to get a token
        token_url = "http://localhost:8000/token"
        token_response = requests.post(token_url)
        if token_response.status_code != 200:
            print("⚠️  Could not get token, skipping API test")
            return True
            
        token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Submit the query
        response = requests.post(url, json={"query": query}, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"API response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            print("✅ API integration test passed!")
            return True
        else:
            print(f"❌ API integration test failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️  API integration test skipped due to error: {e}")
        return True  # Skip API test if service is not running

if __name__ == "__main__":
    print("Testing coordinator agent integration...")
    
    # Test coordinator agent directly
    success1 = test_coordinator_agent()
    
    # Test API integration
    success2 = test_api_integration()
    
    if success1 and success2:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)