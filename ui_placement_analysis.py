#!/usr/bin/env python3
"""
UI Placement Analysis for Bldr Empire v2 Tools
Этап 4: Определение UI placement для инструментов
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tools_system import ToolsSystem

def analyze_ui_placement():
    """Analyze and optimize UI placement for all tools"""
    print("🎨 BLDR EMPIRE v2 - UI PLACEMENT ANALYSIS")
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
    
    print(f"📊 Analyzing UI placement for {len(tools)} tools")
    print()
    
    # Define UI placement criteria
    placement_criteria = {
        "dashboard": {
            "description": "High-impact daily workflow tools",
            "criteria": [
                "Used daily by construction professionals",
                "Generate immediate business value", 
                "Simple, focused functionality",
                "Quick execution (< 30 seconds)",
                "Visual/document output"
            ],
            "max_tools": 12,  # Limit dashboard to avoid clutter
            "icon": "🎯"
        },
        "tools": {
            "description": "Professional tools for specialists",
            "criteria": [
                "Used weekly by specialists",
                "Complex functionality requiring expertise",
                "Longer execution time acceptable",
                "Professional/technical output",
                "Configurable parameters"
            ],
            "max_tools": 20,
            "icon": "🔧"
        },
        "service": {
            "description": "Hidden service tools for internal use",
            "criteria": [
                "Internal system functions",
                "Called by other tools/systems",
                "Technical/infrastructure tools",
                "No direct user interaction needed",
                "Supporting functionality"
            ],
            "max_tools": None,  # No limit
            "icon": "⚙️"
        }
    }
    
    # Analyze current placement
    current_placement = {}
    for tool_name, tool_info in tools.items():
        placement = tool_info["ui_placement"]
        if placement not in current_placement:
            current_placement[placement] = []
        current_placement[placement].append((tool_name, tool_info))
    
    print("📋 CURRENT PLACEMENT ANALYSIS")
    print("-" * 40)
    
    for placement, criteria in placement_criteria.items():
        tool_list = current_placement.get(placement, [])
        count = len(tool_list)
        max_tools = criteria["max_tools"]
        
        print(f"\n{criteria['icon']} {placement.upper()}: {count} tools" + 
              (f" (max: {max_tools})" if max_tools else ""))
        print(f"   {criteria['description']}")
        
        if max_tools and count > max_tools:
            print(f"   ⚠️  OVER LIMIT: {count - max_tools} tools need relocation")
        
        # Show tools in this category
        for tool_name, tool_info in sorted(tool_list)[:8]:  # Show first 8
            category = tool_info["category"]
            source = tool_info.get("source", "tools_system")
            print(f"   • {tool_name} ({category}) [{source}]")
        
        if len(tool_list) > 8:
            print(f"   ... and {len(tool_list) - 8} more")
    
    print("\n" + "=" * 60)
    
    # Recommend optimal placement
    print("\n🎯 OPTIMAL PLACEMENT RECOMMENDATIONS")
    print("-" * 40)
    
    # High-priority dashboard tools (daily use)
    dashboard_recommendations = [
        # Document Generation (daily)
        ("generate_letter", "Daily letter generation for compliance/communication"),
        ("improve_letter", "Daily letter editing and enhancement"),
        
        # Financial Analysis (daily)
        ("calculate_estimate", "Daily cost calculations for projects"),
        ("auto_budget", "Daily budget generation from estimates"),
        ("parse_estimate_unified", "Daily estimate processing (unified)"),
        
        # Project Analysis (daily)
        ("analyze_tender", "Daily tender analysis for bid decisions"),
        ("comprehensive_analysis", "Daily project evaluation"),
        
        # Core Analysis (daily)
        ("analyze_image", "Daily photo analysis of construction progress"),
        ("search_rag_database", "Daily knowledge base searches"),
        
        # Quick Tools (daily)
        ("generate_construction_schedule", "Daily schedule generation"),
        ("calculate_financial_metrics", "Daily ROI/NPV calculations"),
        ("check_normative", "Daily compliance checking")
    ]
    
    # Professional tools (weekly use)
    tools_recommendations = [
        # Advanced Project Management
        ("create_gantt_chart", "Weekly project planning"),
        ("calculate_critical_path", "Weekly schedule optimization"),
        ("monte_carlo_sim", "Weekly risk analysis"),
        ("generate_ppr", "Weekly PPR document generation"),
        ("create_gpp", "Weekly GPP planning"),
        
        # Advanced Analysis
        ("analyze_bentley_model", "Weekly BIM model analysis"),
        ("autocad_export", "Weekly CAD export operations"),
        
        # Financial Tools
        ("export_budget_to_excel", "Weekly budget exports"),
        ("get_regional_coefficients", "Weekly coefficient lookups"),
        
        # Project Management
        ("scan_project_files", "Weekly project file organization"),
        ("scan_directory_for_project", "Weekly directory scanning"),
        ("generate_timeline", "Weekly timeline generation"),
        ("generate_gantt_tasks", "Weekly Gantt task creation"),
        ("generate_milestones", "Weekly milestone planning"),
        
        # Document Tools
        ("generate_official_letter", "Weekly official document generation"),
        ("create_document", "Weekly document creation"),
        
        # Data Processing
        ("extract_text_from_pdf", "Weekly PDF processing"),
        ("find_normatives", "Weekly normative searches")
    ]
    
    # Service tools (internal use)
    service_recommendations = [
        # Internal Processing
        ("semantic_parse", "Internal NLP processing"),
        ("parse_intent_and_entities", "Internal intent parsing"),
        ("parse_request_with_sbert", "Internal request parsing"),
        
        # Data Extraction
        ("extract_works_nlp", "Internal work extraction"),
        ("extract_construction_data", "Internal data extraction"),
        ("extract_financial_data", "Internal financial extraction"),
        ("extract_resources", "Internal resource extraction"),
        ("extract_gpp_resources", "Internal GPP resource extraction"),
        ("extract_gesn_rates_from_text", "Internal GESN extraction"),
        ("extract_document_structure", "Internal structure extraction"),
        
        # System Tools
        ("enterprise_rag_trainer", "Internal training system"),
        ("create_hierarchical_chunks", "Internal chunking system"),
        ("process_document_api_compatible", "Internal document processing"),
        
        # Legacy/Batch Tools
        ("parse_batch_estimates", "Internal batch processing"),
        ("parse_gesn_estimate", "Internal GESN processing (legacy)"),
        
        # Utility Tools
        ("get_available_templates", "Internal template management"),
        ("export_letter_to_docx", "Internal export utility"),
        ("create_default_templates", "Internal template creation"),
        ("generate_task_links", "Internal task linking"),
        ("get_work_sequence", "Internal sequence retrieval"),
        ("create_construction_schedule", "Internal schedule creation"),
        
        # Chart Generation (internal)
        ("generate_mermaid_diagram", "Internal diagram generation"),
        ("create_pie_chart", "Internal chart creation"),
        ("create_bar_chart", "Internal chart creation")
    ]
    
    # Print recommendations
    print(f"\n🎯 DASHBOARD RECOMMENDATIONS ({len(dashboard_recommendations)} tools)")
    print("   High-impact daily workflow tools:")
    for i, (tool_name, reason) in enumerate(dashboard_recommendations, 1):
        print(f"   {i:2d}. {tool_name}")
        print(f"       → {reason}")
    
    print(f"\n🔧 TOOLS TAB RECOMMENDATIONS ({len(tools_recommendations)} tools)")
    print("   Professional tools for specialists:")
    for i, (tool_name, reason) in enumerate(tools_recommendations, 1):
        print(f"   {i:2d}. {tool_name}")
        print(f"       → {reason}")
    
    print(f"\n⚙️  SERVICE TOOLS ({len(service_recommendations)} tools)")
    print("   Hidden internal tools:")
    for i, (tool_name, reason) in enumerate(service_recommendations[:10], 1):  # Show first 10
        print(f"   {i:2d}. {tool_name}")
        print(f"       → {reason}")
    if len(service_recommendations) > 10:
        print(f"   ... and {len(service_recommendations) - 10} more internal tools")
    
    # Generate placement changes
    print(f"\n🔄 PLACEMENT CHANGES NEEDED")
    print("-" * 30)
    
    # Tools that should move to dashboard
    current_dashboard = {name for name, _ in current_placement.get("dashboard", [])}
    recommended_dashboard = {name for name, _ in dashboard_recommendations}
    
    move_to_dashboard = recommended_dashboard - current_dashboard
    move_from_dashboard = current_dashboard - recommended_dashboard
    
    if move_to_dashboard:
        print(f"\n📈 PROMOTE TO DASHBOARD ({len(move_to_dashboard)} tools):")
        for tool in sorted(move_to_dashboard):
            current_loc = next((p for p, tools_list in current_placement.items() 
                              if tool in [t[0] for t in tools_list]), "unknown")
            print(f"   • {tool} (from {current_loc})")
    
    if move_from_dashboard:
        print(f"\n📉 DEMOTE FROM DASHBOARD ({len(move_from_dashboard)} tools):")
        for tool in sorted(move_from_dashboard):
            print(f"   • {tool} (to tools tab)")
    
    # Tools that should move to tools tab
    current_tools = {name for name, _ in current_placement.get("tools", [])}
    recommended_tools = {name for name, _ in tools_recommendations}
    
    move_to_tools = recommended_tools - current_tools - recommended_dashboard
    
    if move_to_tools:
        print(f"\n🔧 PROMOTE TO TOOLS TAB ({len(move_to_tools)} tools):")
        for tool in sorted(move_to_tools):
            current_loc = next((p for p, tools_list in current_placement.items() 
                              if tool in [t[0] for t in tools_list]), "unknown")
            print(f"   • {tool} (from {current_loc})")
    
    print(f"\n📊 SUMMARY")
    print("-" * 20)
    print(f"Dashboard: {len(recommended_dashboard)} tools (limit: 12)")
    print(f"Tools Tab: {len(recommended_tools)} tools (limit: 20)")
    print(f"Service: {len(service_recommendations)} tools (no limit)")
    print(f"Total: {len(recommended_dashboard) + len(recommended_tools) + len(service_recommendations)} tools")
    
    return {
        "dashboard": dashboard_recommendations,
        "tools": tools_recommendations, 
        "service": service_recommendations,
        "changes": {
            "move_to_dashboard": move_to_dashboard,
            "move_from_dashboard": move_from_dashboard,
            "move_to_tools": move_to_tools
        }
    }

if __name__ == "__main__":
    analyze_ui_placement()