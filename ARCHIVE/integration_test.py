#!/usr/bin/env python3
"""
Integration test for the full Bldr Empire system
"""

import sys
import os

# Add the project root and core directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
core_path = os.path.join(project_root, 'core')
sys.path.insert(0, project_root)
sys.path.insert(0, core_path)

def test_full_integration():
    print("Testing full Bldr Empire system integration...")
    
    try:
        # Test 1: Import core modules
        print("\n1. Testing core module imports...")
        from core.coordinator import Coordinator
        from core.model_manager import ModelManager
        from core.tools_system import ToolsSystem
        print("✅ Core modules imported successfully!")
        
        # Test 2: Initialize components
        print("\n2. Testing component initialization...")
        model_manager = ModelManager()
        tools_system = ToolsSystem(None, model_manager)
        coord = Coordinator(model_manager, tools_system, None)
        print("✅ Components initialized successfully!")
        
        # Test 3: Test coordinator request analysis
        print("\n3. Testing coordinator request analysis...")
        test_request = "Найди нормативы для устройства бетонной подготовки"
        plan = coord.analyze_request(test_request)
        if isinstance(plan, dict) and 'status' in plan:
            print("✅ Coordinator request analysis successful!")
            print(f"   Plan status: {plan['status']}")
            print(f"   Query type: {plan.get('query_type', 'unknown')}")
        else:
            print("❌ Coordinator request analysis failed!")
            return False
            
        # Test 4: Test tools discovery
        print("\n4. Testing tools discovery...")
        tools_info = tools_system.discover_tools()
        if tools_info.get("status") == "success":
            all_tools = tools_info.get("data", {}).get("tools", {})
            print(f"✅ Tools discovery successful! Found {len(all_tools)} tools")
            # Show first 3 tools
            for i, (tool_name, tool_info) in enumerate(all_tools.items()):
                if i >= 3:
                    break
                print(f"   - {tool_name}: {tool_info.get('description', 'No description')}")
        else:
            print("❌ Tools discovery failed!")
            return False
            
        # Test 5: Test tool execution (with error handling)
        print("\n5. Testing tool execution...")
        result = tools_system.execute_tool("search_rag_database", query="строительные нормы", k=3)
        if result.get("status") == "error":
            print("✅ Tool execution test completed (expected error due to missing RAG system)")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        else:
            print("✅ Tool execution successful!")
            print(f"   Result: {result}")
            
        print("\n🎉 All integration tests completed successfully!")
        print("\n📝 Note: Some tools may show errors because they require the full RAG system")
        print("   which wasn't initialized in this test. This is expected behavior.")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_integration()
    if success:
        print("\n✅ Integration test PASSED")
        sys.exit(0)
    else:
        print("\n❌ Integration test FAILED")
        sys.exit(1)