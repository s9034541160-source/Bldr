import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the core tools system
from core.tools_system import ToolsSystem
from core.model_manager import ModelManager

# Create a mock RAG system
class MockRAGSystem:
    def query(self, query, k=5):
        return {
            "results": [
                {
                    "chunk": f"Mock result for query: {query}",
                    "meta": {"conf": 0.99},
                    "score": 0.99
                }
            ],
            "ndcg": 0.95
        }

def test_tools_system():
    print("Testing ToolsSystem...")
    
    # Create mock systems
    mock_rag = MockRAGSystem()
    model_manager = ModelManager()
    
    # Create ToolsSystem
    tools_system = ToolsSystem(mock_rag, model_manager)
    
    # Check what tools are available
    print("Available tools:")
    for tool_name in tools_system.tool_methods.keys():
        print(f"  - {tool_name}")
    
    # Test generate_letter tool
    print("\nTesting generate_letter...")
    try:
        result = tools_system.execute_tool("generate_letter", {
            "description": "Test letter",
            "template_id": "compliance_sp31"
        })
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test with a non-existent tool
    print("\nTesting non-existent tool...")
    try:
        result = tools_system.execute_tool("non_existent_tool", {})
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_tools_system()