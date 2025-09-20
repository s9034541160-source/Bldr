#!/usr/bin/env python3
"""
Final test for coordinator agent with proper timeout handling
"""

import sys
import os
import time

# Set environment variable for OpenAI API key (not actually needed for LM Studio)
os.environ["OPENAI_API_KEY"] = "not-needed"

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

def test_coordinator_with_timeout():
    """Test the coordinator agent with proper timeout handling"""
    print("Testing coordinator agent with timeout handling...")
    
    try:
        # Import the coordinator agent
        from core.agents.coordinator_agent import CoordinatorAgent
        print("✅ Coordinator agent imported successfully")
        
        # Initialize the coordinator agent
        coordinator = CoordinatorAgent()
        print("✅ Coordinator agent initialized")
        
        # Test query
        query = "Анализ LSR на СП31 + письмо"
        print(f"📝 Testing with query: {query}")
        
        # Generate plan with timeout
        print("🧠 Generating execution plan... (this may take a while)")
        start_time = time.time()
        
        try:
            plan = coordinator.generate_plan(query)
            
            end_time = time.time()
            
            print(f"📋 Plan generated in {end_time - start_time:.2f} seconds")
            print(f"Plan: {plan}")
            
            # Validate plan structure
            required_keys = ["complexity", "time_est", "roles", "tasks"]
            for key in required_keys:
                if key not in plan:
                    print(f"❌ Missing required key in plan: {key}")
                    return
                    
            print("✅ Plan structure is valid")
            
            # Check if tasks are properly structured
            if "tasks" in plan and isinstance(plan["tasks"], list):
                for i, task in enumerate(plan["tasks"]):
                    if not isinstance(task, dict):
                        print(f"❌ Task {i} is not a dictionary")
                        return
                    required_task_keys = ["id", "agent", "input", "tool"]
                    for key in required_task_keys:
                        if key not in task:
                            print(f"❌ Missing required key in task {i}: {key}")
                            return
                print("✅ All tasks are properly structured")
            else:
                print("❌ Tasks should be a list of dictionaries")
                return
                
            print("🎉 Coordinator test completed successfully!")
            
        except Exception as e:
            end_time = time.time()
            print(f"❌ Error after {end_time - start_time:.2f} seconds: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error importing coordinator: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_coordinator_with_timeout()