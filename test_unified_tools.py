#!/usr/bin/env python3
"""
Test script for unified tools system with **kwargs support
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tools_system import ToolsSystem
from core.model_manager import ModelManager

def test_unified_tools():
    """Test the unified tools system"""
    print("🚀 Testing Unified Tools System with **kwargs support")
    
    # Create mock RAG system and model manager
    class MockRAGSystem:
        def query(self, query, k=5):
            return {
                "results": [
                    {"chunk": f"Mock result for: {query}", "meta": {"doc_type": "norms"}}
                ],
                "ndcg": 0.95
            }
    
    class MockModelManager:
        pass
    
    # Initialize tools system
    rag_system = MockRAGSystem()
    model_manager = MockModelManager()
    tools_system = ToolsSystem(rag_system, model_manager)
    
    print("✅ Tools system initialized")
    
    # Test 1: Tool discovery
    print("\n📋 Test 1: Tool Discovery")
    discovery_result = tools_system.discover_tools()
    print(f"Status: {discovery_result['status']}")
    print(f"Total tools: {discovery_result['data']['total_count']}")
    print(f"Categories: {list(discovery_result['data']['categories'].keys())}")
    
    # Test 2: Execute tool with **kwargs (new method)
    print("\n🔧 Test 2: Execute tool with **kwargs")
    try:
        result = tools_system.execute_tool(
            "search_rag_database",
            query="СП 48.13330",
            doc_types=["norms"],
            k=3
        )
        print(f"Status: {result['status']}")
        print(f"Tool: {result['tool_name']}")
        print(f"Execution time: {result['execution_time']:.3f}s")
        print(f"Results count: {len(result.get('results', []))}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Execute tool with legacy arguments dict
    print("\n🔄 Test 3: Execute tool with legacy arguments dict")
    try:
        result = tools_system.execute_tool(
            "search_rag_database",
            arguments={"query": "ГОСТ 123", "k": 2}
        )
        print(f"Status: {result['status']}")
        print(f"Tool: {result['tool_name']}")
        print(f"Execution time: {result['execution_time']:.3f}s")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Error handling
    print("\n❌ Test 4: Error handling")
    try:
        result = tools_system.execute_tool(
            "search_rag_database"
            # Missing required 'query' parameter
        )
        print(f"Status: {result['status']}")
        print(f"Error: {result['error']}")
        print(f"Category: {result['metadata']['error_category']}")
        print(f"Suggestions: {result['metadata']['suggestions']}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test 5: Tool categories
    print("\n📂 Test 5: Tool Categories")
    sample_tools = ["search_rag_database", "generate_letter", "calculate_estimate", "analyze_image"]
    for tool in sample_tools:
        category = tools_system._get_tool_category(tool)
        ui_placement = tools_system._get_ui_placement(tool)
        print(f"  {tool}: {category} -> {ui_placement}")
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    test_unified_tools()