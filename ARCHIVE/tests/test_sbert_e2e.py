"""
End-to-End Test for SBERT Integration in Bldr Empire v2
"""

import sys
import os

# Add the core directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.tools_system import ToolsSystem
from core.parse_utils import model

def test_sbert_e2e():
    """Test SBERT integration end-to-end"""
    if model is None:
        print("SBERT model not available - skipping E2E test")
        return
    
    # Create a mock tools system (we won't actually execute tools)
    tools_system = ToolsSystem(None, None)
    
    # Test semantic_parse tool
    test_cases = [
        {
            "name": "Intent Parsing Test",
            "tool_call": {
                "name": "semantic_parse",
                "arguments": {
                    "text": "Проверь СП31 на фото",
                    "task": "intent",
                    "labels": ["norm_check", "vl_analysis"]
                }
            }
        },
        {
            "name": "Entity Extraction Test",
            "tool_call": {
                "name": "semantic_parse",
                "arguments": {
                    "text": "Смета ГЭСН Москва",
                    "task": "entities"
                }
            }
        }
    ]
    
    print("Running SBERT E2E Tests...")
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        tool_call = test_case['tool_call']
        
        # Execute the tool call
        result = tools_system.execute_tool(
            tool_call["name"], 
            tool_call["arguments"]
        )
        
        print(f"Tool: {tool_call['name']}")
        print(f"Arguments: {tool_call['arguments']}")
        print(f"Result: {result}")
        
        # Verify success
        if result.get("status") == "success":
            print("✅ Test PASSED")
        else:
            print("❌ Test FAILED")
            print(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_sbert_e2e()