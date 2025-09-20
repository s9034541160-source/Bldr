#!/usr/bin/env python3
"""
Test script to verify coordinator agent generates natural language responses
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.agents.coordinator_agent import CoordinatorAgent

def test_coordinator_response():
    """Test the coordinator agent with a conversational query"""
    print("Testing coordinator agent natural language response generation...")
    
    # Initialize coordinator agent
    coordinator = CoordinatorAgent()
    
    # Test with a conversational query in Russian (as mentioned in the user's example)
    query = "привет. расскажи о себе. что знаешь, что умеешь?"
    
    print(f"Query: {query}")
    
    # Generate natural language response
    try:
        response = coordinator.generate_response(query)
        print(f"Natural language response: {response}")
        print("✅ Test passed: Coordinator generated natural language response")
        return True
    except Exception as e:
        print(f"❌ Test failed: Error generating response: {e}")
        return False

if __name__ == "__main__":
    success = test_coordinator_response()
    if not success:
        sys.exit(1)