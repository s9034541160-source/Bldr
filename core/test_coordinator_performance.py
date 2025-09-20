"""Test script to verify coordinator performance optimizations"""

import time
from core.agents.coordinator_agent import CoordinatorAgent

def test_simple_queries():
    """Test simple queries to verify performance improvements"""
    coordinator = CoordinatorAgent()
    
    # Test greeting query
    print("Testing greeting query...")
    start_time = time.time()
    response = coordinator.process_query("привет")
    end_time = time.time()
    
    print(f"Greeting response: {response}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    
    # Test self-introduction query
    print("\nTesting self-introduction query...")
    start_time = time.time()
    response = coordinator.process_query("расскажи о себе")
    end_time = time.time()
    
    print(f"Self-introduction response: {response}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    
    # Test simple query
    print("\nTesting simple query...")
    start_time = time.time()
    response = coordinator.process_query("что ты умеешь")
    end_time = time.time()
    
    print(f"Simple query response: {response}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    test_simple_queries()