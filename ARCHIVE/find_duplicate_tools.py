#!/usr/bin/env python3
"""
Find duplicate and similar tools in Bldr Empire v2
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tools_system import ToolsSystem
from difflib import SequenceMatcher

def similarity(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a, b).ratio()

def find_duplicate_tools():
    """Find potential duplicate tools"""
    print("🔍 SEARCHING FOR DUPLICATE TOOLS")
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
    
    print(f"📊 Analyzing {len(tools)} tools for duplicates...")
    print()
    
    # Group by functionality keywords
    functionality_groups = {}
    
    for tool_name, tool_info in tools.items():
        description = tool_info["description"].lower()
        
        # Extract key functionality words
        key_words = []
        if "letter" in description:
            key_words.append("letter")
        if "generate" in description or "create" in description:
            key_words.append("generate")
        if "parse" in description or "extract" in description:
            key_words.append("parse")
        if "estimate" in description or "budget" in description or "financial" in description:
            key_words.append("financial")
        if "gantt" in description or "schedule" in description or "timeline" in description:
            key_words.append("schedule")
        if "template" in description:
            key_words.append("template")
        if "project" in description:
            key_words.append("project")
        if "export" in description:
            key_words.append("export")
        if "analyze" in description or "analysis" in description:
            key_words.append("analyze")
        
        # Group by functionality
        for word in key_words:
            if word not in functionality_groups:
                functionality_groups[word] = []
            functionality_groups[word].append((tool_name, tool_info))
    
    # Find potential duplicates
    duplicates_found = []
    
    print("🔍 POTENTIAL DUPLICATES BY FUNCTIONALITY:")
    print("-" * 40)
    
    for functionality, tool_list in functionality_groups.items():
        if len(tool_list) > 1:
            print(f"\n📂 {functionality.upper()} ({len(tool_list)} tools):")
            
            # Check for similar names and descriptions
            for i, (tool1_name, tool1_info) in enumerate(tool_list):
                for j, (tool2_name, tool2_info) in enumerate(tool_list[i+1:], i+1):
                    name_similarity = similarity(tool1_name, tool2_name)
                    desc_similarity = similarity(tool1_info["description"], tool2_info["description"])
                    
                    if name_similarity > 0.6 or desc_similarity > 0.7:
                        duplicates_found.append({
                            "tool1": tool1_name,
                            "tool2": tool2_name,
                            "name_similarity": name_similarity,
                            "desc_similarity": desc_similarity,
                            "functionality": functionality
                        })
                        
                        print(f"   ⚠️  POTENTIAL DUPLICATE:")
                        print(f"      {tool1_name} ({tool1_info.get('source', 'tools_system')})")
                        print(f"      {tool2_name} ({tool2_info.get('source', 'tools_system')})")
                        print(f"      Name similarity: {name_similarity:.2f}")
                        print(f"      Description similarity: {desc_similarity:.2f}")
                        print()
            
            # List all tools in this group
            print(f"   All {functionality} tools:")
            for tool_name, tool_info in tool_list:
                source = tool_info.get('source', 'tools_system')
                ui_placement = tool_info['ui_placement']
                print(f"   • {tool_name} ({source}) -> {ui_placement}")
            print()
    
    # Specific duplicate patterns to check
    print("\n🎯 SPECIFIC DUPLICATE PATTERNS:")
    print("-" * 35)
    
    # Letter generation duplicates
    letter_tools = [name for name in tools.keys() if "letter" in name.lower()]
    if len(letter_tools) > 1:
        print(f"📝 Letter tools: {letter_tools}")
        for tool in letter_tools:
            source = tools[tool].get('source', 'tools_system')
            print(f"   • {tool} ({source}): {tools[tool]['description']}")
        print()
    
    # Template duplicates
    template_tools = [name for name in tools.keys() if "template" in name.lower()]
    if len(template_tools) > 1:
        print(f"📋 Template tools: {template_tools}")
        for tool in template_tools:
            source = tools[tool].get('source', 'tools_system')
            print(f"   • {tool} ({source}): {tools[tool]['description']}")
        print()
    
    # Parse/Extract duplicates
    parse_tools = [name for name in tools.keys() if any(word in name.lower() for word in ["parse", "extract"])]
    if len(parse_tools) > 3:
        print(f"🔍 Parse/Extract tools ({len(parse_tools)}): {parse_tools[:5]}...")
        for tool in parse_tools[:8]:  # Show first 8
            source = tools[tool].get('source', 'tools_system')
            print(f"   • {tool} ({source}): {tools[tool]['description'][:60]}...")
        if len(parse_tools) > 8:
            print(f"   ... and {len(parse_tools) - 8} more")
        print()
    
    # Summary
    print("\n📊 DUPLICATE ANALYSIS SUMMARY:")
    print("-" * 30)
    print(f"Total tools analyzed: {len(tools)}")
    print(f"Potential duplicates found: {len(duplicates_found)}")
    print(f"Functionality groups: {len(functionality_groups)}")
    
    if duplicates_found:
        print("\n⚠️  HIGH PRIORITY DUPLICATES TO REVIEW:")
        for dup in sorted(duplicates_found, key=lambda x: x['desc_similarity'], reverse=True)[:5]:
            print(f"   • {dup['tool1']} ↔ {dup['tool2']} (similarity: {dup['desc_similarity']:.2f})")
    
    print("\n🎯 RECOMMENDATIONS:")
    print("1. Review letter generation tools for consolidation")
    print("2. Merge similar parse/extract functions")
    print("3. Consolidate template management tools")
    print("4. Create unified interfaces for similar functionality")
    
    return duplicates_found, functionality_groups

if __name__ == "__main__":
    find_duplicate_tools()