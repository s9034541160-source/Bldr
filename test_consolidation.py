#!/usr/bin/env python3
"""
Test consolidated tools functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tools_system import ToolsSystem

def test_consolidation():
    """Test consolidated tools"""
    print("🧪 TESTING TOOLS CONSOLIDATION")
    print("=" * 50)
    
    # Create mock systems
    class MockRAGSystem:
        def query(self, query, k=5):
            return {"results": [], "ndcg": 0.95}
    
    class MockModelManager:
        pass
    
    # Initialize tools system
    tools_system = ToolsSystem(MockRAGSystem(), MockModelManager())
    
    # Test 1: Check tool count after consolidation
    print("📊 Test 1: Tool Discovery After Consolidation")
    discovery_result = tools_system.discover_tools()
    tools = discovery_result["data"]["tools"]
    
    print(f"Total tools: {len(tools)}")
    print(f"Categories: {list(discovery_result['data']['categories'].keys())}")
    
    # Check for removed duplicates
    removed_tools = [
        "get_letter_templates",  # Should be removed (duplicate)
        "parse_excel_estimate",  # Should be consolidated
        "parse_csv_estimate",    # Should be consolidated
        "parse_text_estimate"    # Should be consolidated
    ]
    
    for tool in removed_tools:
        if tool in tools:
            print(f"❌ {tool} still present (should be removed/consolidated)")
        else:
            print(f"✅ {tool} successfully removed/consolidated")
    
    # Check for new unified tools
    unified_tools = [
        "parse_estimate_unified"
    ]
    
    for tool in unified_tools:
        if tool in tools:
            print(f"✅ {tool} successfully added")
        else:
            print(f"❌ {tool} missing (should be added)")
    
    print()
    
    # Test 2: Test unified estimate parser
    print("🔧 Test 2: Unified Estimate Parser")
    try:
        # Test with text content
        result = tools_system.execute_tool(
            "parse_estimate_unified",
            input_data="ГЭСН 8-6-1.1 Устройство фундамента 100 м3 15000 руб/м3"
        )
        print(f"Status: {result['status']}")
        print(f"Parser used: {result.get('parser_used', 'unknown')}")
        if 'consolidates' in result:
            print(f"Consolidates: {result['consolidates']}")
        print()
    except Exception as e:
        print(f"❌ Error testing unified parser: {e}")
        print()
    
    # Test 3: Backward compatibility
    print("🔄 Test 3: Backward Compatibility")
    try:
        # Test old parse_gesn_estimate (should still work)
        result = tools_system.execute_tool(
            "parse_gesn_estimate",
            estimate_file="test_estimate.xlsx",
            region="moscow"
        )
        print(f"Legacy parser status: {result['status']}")
        print(f"Parser used: {result.get('parser_used', 'legacy')}")
        print()
    except Exception as e:
        print(f"❌ Error testing backward compatibility: {e}")
        print()
    
    # Test 4: Template consolidation
    print("📋 Test 4: Template Consolidation")
    
    # Check that get_available_templates exists but get_letter_templates doesn't
    if "get_available_templates" in tools:
        print("✅ get_available_templates present")
    else:
        print("❌ get_available_templates missing")
    
    if "get_letter_templates" not in tools:
        print("✅ get_letter_templates successfully removed (duplicate)")
    else:
        print("❌ get_letter_templates still present (should be removed)")
    
    print()
    
    # Summary
    print("📊 CONSOLIDATION SUMMARY:")
    print(f"   Tools after consolidation: {len(tools)}")
    
    # Count by source
    sources = {}
    for tool_info in tools.values():
        source = tool_info.get('source', 'tools_system')
        sources[source] = sources.get(source, 0) + 1
    
    print("   Tools by source:")
    for source, count in sorted(sources.items()):
        print(f"     {source}: {count}")
    
    # Check for unified tools
    unified_count = sum(1 for tool_info in tools.values() 
                       if 'unified' in tool_info.get('source', '') or 'unified' in tool_info['name'])
    print(f"   Unified tools: {unified_count}")
    
    print("\n🎉 Consolidation test completed!")

if __name__ == "__main__":
    test_consolidation()