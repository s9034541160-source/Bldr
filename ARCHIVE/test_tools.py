#!/usr/bin/env python3
"""
Test script for the Tools System
"""

import sys
import os

# Add the core directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from core.tools_system import ToolsSystem
from core.model_manager import ModelManager

def main():
    print("Testing Tools System initialization...")
    
    try:
        # Initialize the required components
        model_manager = ModelManager()
        rag_system = None  # We don't have a real RAG system for testing
        
        # Initialize the tools system
        ts = ToolsSystem(rag_system, model_manager)
        print("✅ Tools System initialized successfully!")
        
        # Discover tools
        tools_info = ts.discover_tools()
        if tools_info.get("status") == "success":
            all_tools = tools_info.get("data", {}).get("tools", {})
            print(f"✅ Tools discovery completed! Found {len(all_tools)} tools:")
            
            # Show first 5 tools
            for i, (tool_name, tool_info) in enumerate(all_tools.items()):
                if i >= 5:
                    print(f"  ... and {len(all_tools) - 5} more tools")
                    break
                print(f"  - {tool_name}: {tool_info.get('description', 'No description')}")
        else:
            print(f"❌ Tools discovery failed: {tools_info.get('error', 'Unknown error')}")
            
        # Test executing a simple tool
        print("\nTesting tool execution...")
        result = ts.execute_tool("search_rag_database", query="строительные нормы", k=3)
        print(f"✅ Tool execution completed!")
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"❌ Error testing tools system: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()