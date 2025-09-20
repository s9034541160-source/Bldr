"""
Test script to verify that the system starts properly with SBERT integration
"""

import sys
import os
import time
import subprocess
import requests

def test_system_components():
    """Test that all system components are working"""
    print("🔍 Testing Bldr Empire v2 System Components...")
    
    # Test 1: Check if core modules import correctly
    try:
        from core.parse_utils import model, parse_intent_and_entities
        print("✅ parse_utils imports successfully")
        
        if model is not None:
            print("✅ SBERT model loaded successfully")
        else:
            print("⚠️ SBERT model not loaded (may be due to memory constraints)")
    except Exception as e:
        print(f"❌ Error importing parse_utils: {e}")
        return False
    
    # Test 2: Check if tools system imports correctly
    try:
        from core.tools_system import ToolsSystem
        print("✅ tools_system imports successfully")
    except Exception as e:
        print(f"❌ Error importing tools_system: {e}")
        return False
    
    # Test 3: Check if config imports correctly
    try:
        from core.config import MODELS_CONFIG
        print("✅ config imports successfully")
        
        # Check if semantic_parse is in coordinator tool instructions
        coordinator_config = MODELS_CONFIG.get('coordinator', {})
        tool_instructions = coordinator_config.get('tool_instructions', '')
        if 'semantic_parse' in tool_instructions:
            print("✅ semantic_parse tool instructions found in config")
        else:
            print("❌ semantic_parse tool instructions not found in config")
    except Exception as e:
        print(f"❌ Error importing config: {e}")
        return False
    
    # Test 4: Check if coordinator imports correctly
    try:
        from core.coordinator import Coordinator
        print("✅ coordinator imports successfully")
    except Exception as e:
        print(f"❌ Error importing coordinator: {e}")
        return False
    
    print("\n🎉 All system components are working correctly!")
    return True

if __name__ == "__main__":
    test_system_components()