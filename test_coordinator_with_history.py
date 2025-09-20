#!/usr/bin/env python3
"""Test script to verify coordinator agent with conversation history"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from core.agents.coordinator_agent import CoordinatorAgent

def test_coordinator_with_history():
    """Test coordinator agent with conversation history"""
    # Create coordinator agent
    coordinator = CoordinatorAgent()
    
    # Set request context with user_id for conversation history
    coordinator.set_request_context({
        "user_id": "test_user_123",
        "source": "frontend"
    })
    
    # Test a simple greeting query
    print("Testing greeting query...")
    response = coordinator.process_query("Привет! Как дела?")
    print(f"Response: {response}")
    
    # Test a self-introduction query
    print("\nTesting self-introduction query...")
    response = coordinator.process_query("Расскажи о себе")
    print(f"Response: {response}")
    
    # Test a more complex query that would use RAG
    print("\nTesting complex query...")
    response = coordinator.process_query("Какие нормы применяются для бетонных работ?")
    print(f"Response: {response}")
    
    # Clear request context
    coordinator.clear_request_context()
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_coordinator_with_history()