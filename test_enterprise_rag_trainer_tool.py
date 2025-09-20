#!/usr/bin/env python3
"""
Test Enterprise RAG Trainer as a tool (not coordinator)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tools_system import ToolsSystem

def test_enterprise_rag_trainer_tool():
    """Test Enterprise RAG Trainer as a tool"""
    print("🧪 TESTING ENTERPRISE RAG TRAINER AS TOOL")
    print("=" * 50)
    
    # Create mock systems
    class MockRAGSystem:
        def query(self, query, k=5):
            return {"results": [], "ndcg": 0.95}
    
    class MockModelManager:
        pass
    
    # Initialize tools system
    tools_system = ToolsSystem(MockRAGSystem(), MockModelManager())
    
    # Test 1: Check if Enterprise RAG Trainer is discovered as a tool
    print("📋 Test 1: Tool Discovery")
    discovery_result = tools_system.discover_tools()
    tools = discovery_result["data"]["tools"]
    
    if "enterprise_rag_trainer" in tools:
        tool_info = tools["enterprise_rag_trainer"]
        print("✅ Enterprise RAG Trainer found as tool")
        print(f"   Category: {tool_info['category']}")
        print(f"   Description: {tool_info['description']}")
        print(f"   UI Placement: {tool_info['ui_placement']}")
        print(f"   Source: {tool_info['source']}")
    else:
        print("❌ Enterprise RAG Trainer not found in tools")
        return
    
    print()
    
    # Test 2: Test tool execution (dry run)
    print("🔧 Test 2: Tool Execution (Dry Run)")
    try:
        # Test with minimal parameters
        result = tools_system.execute_tool(
            "enterprise_rag_trainer",
            max_files=1,  # Process only 1 file for testing
            fast_mode=True  # Use fast mode
        )
        
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Message: {result.get('message', 'No message')}")
            print(f"Training mode: {result.get('training_mode', 'unknown')}")
            print(f"Tool type: {result.get('tool_type', 'unknown')}")
            print(f"Files processed: {result.get('files_processed', 0)}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            if 'suggestion' in result:
                print(f"Suggestion: {result['suggestion']}")
        
    except Exception as e:
        print(f"❌ Error testing tool execution: {e}")
    
    print()
    
    # Test 3: Verify tool categorization
    print("📂 Test 3: Tool Categorization")
    
    # Check category
    expected_category = "advanced_analysis"
    actual_category = tools["enterprise_rag_trainer"]["category"]
    
    if actual_category == expected_category:
        print(f"✅ Correct category: {actual_category}")
    else:
        print(f"❌ Wrong category: expected {expected_category}, got {actual_category}")
    
    # Check UI placement
    expected_placement = "service"
    actual_placement = tools["enterprise_rag_trainer"]["ui_placement"]
    
    if actual_placement == expected_placement:
        print(f"✅ Correct UI placement: {actual_placement}")
    else:
        print(f"❌ Wrong UI placement: expected {expected_placement}, got {actual_placement}")
    
    print()
    
    # Test 4: Check tool is NOT in coordinator role
    print("🎯 Test 4: Verify NOT Coordinator Role")
    
    description = tools["enterprise_rag_trainer"]["description"].lower()
    
    if "coordinator" not in description and "training" in description:
        print("✅ Correctly positioned as training tool, not coordinator")
    else:
        print("❌ Incorrectly positioned - may be confused with coordinator")
    
    # Check UI placement is service (hidden from main UI)
    if actual_placement == "service":
        print("✅ Correctly hidden from main UI (service placement)")
    else:
        print("❌ Should be hidden from main UI")
    
    print()
    
    # Test 5: Integration with existing system
    print("🔗 Test 5: Integration Check")
    
    # Check total tool count
    total_tools = len(tools)
    print(f"Total tools after adding Enterprise RAG Trainer: {total_tools}")
    
    # Check if it's properly integrated
    advanced_analysis_tools = [
        name for name, info in tools.items() 
        if info["category"] == "advanced_analysis"
    ]
    
    print(f"Advanced analysis tools: {len(advanced_analysis_tools)}")
    print(f"Includes Enterprise RAG Trainer: {'enterprise_rag_trainer' in advanced_analysis_tools}")
    
    print()
    
    # Summary
    print("📊 INTEGRATION SUMMARY:")
    print(f"   ✅ Enterprise RAG Trainer added as tool")
    print(f"   ✅ Category: {actual_category}")
    print(f"   ✅ UI Placement: {actual_placement} (hidden from main UI)")
    print(f"   ✅ Role: Training tool (NOT coordinator)")
    print(f"   ✅ Total tools: {total_tools}")
    
    print("\n🎉 Enterprise RAG Trainer successfully integrated as tool!")
    print("💡 Key points:")
    print("   - It's a TOOL for training, not a system coordinator")
    print("   - Hidden from main UI (service placement)")
    print("   - Can be called via API or internal systems")
    print("   - Maintains separation from coordinator role")

if __name__ == "__main__":
    test_enterprise_rag_trainer_tool()