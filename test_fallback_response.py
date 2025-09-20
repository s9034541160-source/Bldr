#!/usr/bin/env python3
"""
Test script to verify coordinator agent fallback natural language response
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.agents.coordinator_agent import CoordinatorAgent

def test_fallback_response():
    """Test the coordinator agent fallback natural language response"""
    print("Testing coordinator agent fallback natural language response...")
    
    # Initialize coordinator agent
    coordinator = CoordinatorAgent()
    
    # Test with a simple plan
    plan = {
        "complexity": "medium",
        "time_est": 5,
        "roles": ["analyst", "chief_engineer"],
        "tasks": [
            {
                "id": 1,
                "agent": "analyst",
                "input": "Search for estimates related to foundation work",
                "tool": "search_rag_database"
            },
            {
                "id": 2,
                "agent": "chief_engineer",
                "input": "Analyze technical requirements for foundation",
                "tool": "search_rag_database"
            }
        ]
    }
    
    # Test with a Russian query
    russian_query = "привет. расскажи о себе. что знаешь, что умеешь?"
    print(f"Russian query: {russian_query}")
    
    try:
        response = coordinator._generate_fallback_natural_language_response(plan, russian_query)
        print(f"Russian response: {response}")
        print("✅ Russian fallback response test passed")
    except Exception as e:
        print(f"❌ Russian fallback response test failed: {e}")
        return False
    
    # Test with an English query
    english_query = "Hello. Tell me about yourself. What do you know, what can you do?"
    print(f"English query: {english_query}")
    
    try:
        response = coordinator._generate_fallback_natural_language_response(plan, english_query)
        print(f"English response: {response}")
        print("✅ English fallback response test passed")
        return True
    except Exception as e:
        print(f"❌ English fallback response test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_fallback_response()
    if not success:
        sys.exit(1)