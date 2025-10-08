#!/usr/bin/env python3
"""
Detailed report of all discovered tools in Bldr Empire v2
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tools_system import ToolsSystem

def generate_tools_report():
    """Generate comprehensive tools report"""
    print("🔍 BLDR EMPIRE v2 - COMPLETE TOOLS DISCOVERY REPORT")
    print("=" * 60)
    
    # Create mock systems
    class MockRAGSystem:
        def query(self, query, k=5):
            return {"results": [], "ndcg": 0.95}
    
    class MockModelManager:
        pass
    
    # Initialize tools system
    tools_system = ToolsSystem(MockRAGSystem(), MockModelManager())
    
    # Get all tools
    discovery_result = tools_system.discover_tools()
    tools = discovery_result["data"]["tools"]
    categories = discovery_result["data"]["categories"]
    
    print(f"📊 SUMMARY:")
    print(f"   Total Tools Found: {len(tools)}")
    print(f"   Categories: {len(categories)}")
    print()
    
    # Report by category
    for category, count in sorted(categories.items()):
        print(f"📂 {category.upper().replace('_', ' ')} ({count} tools)")
        print("-" * 40)
        
        category_tools = [
            (name, info) for name, info in tools.items() 
            if info["category"] == category
        ]
        
        for tool_name, tool_info in sorted(category_tools):
            ui_icon = {
                "dashboard": "🎯",
                "tools": "🔧", 
                "service": "⚙️"
            }.get(tool_info["ui_placement"], "❓")
            
            source_icon = "🆕" if tool_info.get("source") != "tools_system" else "✅"
            
            print(f"   {ui_icon} {source_icon} {tool_name}")
            print(f"      {tool_info['description']}")
            if tool_info.get("source"):
                print(f"      Source: {tool_info['source']}")
            print()
        
        print()
    
    # UI Placement Summary
    print("🎨 UI PLACEMENT SUMMARY:")
    print("-" * 30)
    
    ui_groups = {}
    for tool_name, tool_info in tools.items():
        placement = tool_info["ui_placement"]
        if placement not in ui_groups:
            ui_groups[placement] = []
        ui_groups[placement].append(tool_name)
    
    for placement, tool_list in ui_groups.items():
        icon = {"dashboard": "🎯", "tools": "🔧", "service": "⚙️"}.get(placement, "❓")
        print(f"{icon} {placement.upper()}: {len(tool_list)} tools")
        
        # Show first few tools as examples
        examples = tool_list[:5]
        if len(tool_list) > 5:
            examples_str = ", ".join(examples) + f" ... (+{len(tool_list)-5} more)"
        else:
            examples_str = ", ".join(examples)
        print(f"   Examples: {examples_str}")
        print()
    
    # Hidden Tools Report
    print("🔍 HIDDEN TOOLS DISCOVERED:")
    print("-" * 30)
    
    hidden_tools = [
        (name, info) for name, info in tools.items()
        if info.get("source") != "tools_system"
    ]
    
    print(f"Found {len(hidden_tools)} hidden tools in external modules:")
    
    sources = {}
    for tool_name, tool_info in hidden_tools:
        source = tool_info.get("source", "unknown")
        if source not in sources:
            sources[source] = []
        sources[source].append(tool_name)
    
    for source, tool_list in sorted(sources.items()):
        print(f"\n📁 {source}: {len(tool_list)} tools")
        for tool in sorted(tool_list):
            print(f"   • {tool}")
    
    print("\n" + "=" * 60)
    print("🎉 DISCOVERY COMPLETE!")
    print(f"Total: {len(tools)} tools found across {len(categories)} categories")
    print("✅ System ready for unification and frontend integration")

if __name__ == "__main__":
    generate_tools_report()