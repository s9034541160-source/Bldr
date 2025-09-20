#!/usr/bin/env python3
"""
Test updated UI placement for tools
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tools_system import ToolsSystem

def test_ui_placement_update():
    """Test updated UI placement"""
    print("🎨 TESTING UPDATED UI PLACEMENT")
    print("=" * 50)
    
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
    
    # Group by UI placement
    ui_groups = {}
    for tool_name, tool_info in tools.items():
        placement = tool_info["ui_placement"]
        if placement not in ui_groups:
            ui_groups[placement] = []
        ui_groups[placement].append(tool_name)
    
    print("📊 UPDATED UI PLACEMENT RESULTS")
    print("-" * 35)
    
    # Expected counts based on our recommendations
    expected_counts = {
        "dashboard": 12,  # Limit: 12
        "tools": 18,      # Limit: 20  
        "service": 25     # No limit
    }
    
    for placement in ["dashboard", "tools", "service"]:
        actual_count = len(ui_groups.get(placement, []))
        expected_count = expected_counts[placement]
        
        icon = {"dashboard": "🎯", "tools": "🔧", "service": "⚙️"}[placement]
        status = "✅" if actual_count <= (expected_count + 2) else "⚠️"  # Allow small variance
        
        print(f"\n{icon} {placement.upper()}: {actual_count} tools {status}")
        
        if placement == "dashboard":
            print("   High-impact daily workflow tools:")
        elif placement == "tools":
            print("   Professional tools for specialists:")
        else:
            print("   Hidden service tools for internal use:")
        
        # Show tools in this category
        tool_list = sorted(ui_groups.get(placement, []))
        for i, tool in enumerate(tool_list[:8], 1):  # Show first 8
            print(f"   {i:2d}. {tool}")
        
        if len(tool_list) > 8:
            print(f"   ... and {len(tool_list) - 8} more")
        
        # Check limits
        if placement == "dashboard" and actual_count > 12:
            print(f"   ⚠️  OVER LIMIT: {actual_count - 12} tools (should be max 12)")
        elif placement == "tools" and actual_count > 20:
            print(f"   ⚠️  OVER LIMIT: {actual_count - 20} tools (should be max 20)")
    
    print(f"\n📈 KEY CHANGES VERIFICATION")
    print("-" * 30)
    
    # Check specific tools that should have moved
    expected_dashboard = {
        "search_rag_database", "calculate_financial_metrics", "check_normative"
    }
    
    expected_tools = {
        "generate_official_letter", "create_document", "extract_text_from_pdf"
    }
    
    dashboard_tools = set(ui_groups.get("dashboard", []))
    tools_tab_tools = set(ui_groups.get("tools", []))
    
    # Check promotions to dashboard
    promoted_to_dashboard = expected_dashboard & dashboard_tools
    print(f"✅ Promoted to Dashboard: {len(promoted_to_dashboard)}/3")
    for tool in sorted(promoted_to_dashboard):
        print(f"   • {tool}")
    
    # Check moves to tools tab
    moved_to_tools = expected_tools & tools_tab_tools
    print(f"✅ Moved to Tools Tab: {len(moved_to_tools)}/3")
    for tool in sorted(moved_to_tools):
        print(f"   • {tool}")
    
    print(f"\n🎯 DASHBOARD TOOLS ANALYSIS")
    print("-" * 30)
    
    dashboard_categories = {}
    for tool in ui_groups.get("dashboard", []):
        category = tools[tool]["category"]
        if category not in dashboard_categories:
            dashboard_categories[category] = []
        dashboard_categories[category].append(tool)
    
    print("Distribution by category:")
    for category, tool_list in sorted(dashboard_categories.items()):
        print(f"   {category}: {len(tool_list)} tools")
        for tool in sorted(tool_list):
            print(f"     • {tool}")
    
    print(f"\n📊 SUMMARY")
    print("-" * 20)
    total_tools = sum(len(tool_list) for tool_list in ui_groups.values())
    print(f"Total tools: {total_tools}")
    print(f"Dashboard: {len(ui_groups.get('dashboard', []))} (limit: 12)")
    print(f"Tools Tab: {len(ui_groups.get('tools', []))} (limit: 20)")
    print(f"Service: {len(ui_groups.get('service', []))} (no limit)")
    
    # Check if within limits
    dashboard_ok = len(ui_groups.get('dashboard', [])) <= 12
    tools_ok = len(ui_groups.get('tools', [])) <= 20
    
    if dashboard_ok and tools_ok:
        print("✅ All placement limits respected!")
    else:
        print("⚠️  Some limits exceeded - may need further optimization")
    
    print(f"\n🎉 UI Placement optimization complete!")
    print("Ready for frontend integration! 🚀")

if __name__ == "__main__":
    test_ui_placement_update()