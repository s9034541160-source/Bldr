#!/usr/bin/env python3
"""Debug tool registry to see what's loaded"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tools.base_tool import tool_registry

print("=== TOOL REGISTRY DEBUG ===")
print(f"Total tools loaded: {len(tool_registry.tools)}")
print(f"Total tool methods: {len(tool_registry.tool_methods)}")

print("\n=== LOADED TOOLS ===")
for name, manifest in tool_registry.tools.items():
    print(f"- {name}: {manifest.title}")

print("\n=== LOADED METHODS ===")
for name, method in tool_registry.tool_methods.items():
    print(f"- {name}: {method}")

print("\n=== SEARCHING FOR search_rag_database ===")
if 'search_rag_database' in tool_registry.tool_methods:
    print("✅ search_rag_database found in tool_methods")
else:
    print("❌ search_rag_database NOT found in tool_methods")
    print("Available methods:", list(tool_registry.tool_methods.keys()))

print("\n=== TESTING EXECUTION ===")
try:
    result = tool_registry.execute_tool('search_rag_database', query='test', k=5)
    print(f"Execution result: {result}")
except Exception as e:
    print(f"Execution error: {e}")
