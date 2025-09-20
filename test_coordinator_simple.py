#!/usr/bin/env python3
"""Simple test script to verify coordinator agent structure"""

import sys
import os
import json

# Add the core directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

def test_coordinator_structure():
    """Test the coordinator agent structure without LM Studio connection"""
    try:
        # Import the coordinator agent
        from core.agents.coordinator_agent import CoordinatorAgent
        
        # Check if the class exists
        assert CoordinatorAgent is not None, "CoordinatorAgent class should exist"
        
        # Check if the class has the expected methods
        assert hasattr(CoordinatorAgent, 'generate_plan'), "CoordinatorAgent should have generate_plan method"
        assert hasattr(CoordinatorAgent, '_create_agent'), "CoordinatorAgent should have _create_agent method"
        assert hasattr(CoordinatorAgent, '_analyze_and_plan'), "CoordinatorAgent should have _analyze_and_plan method"
        
        print("✅ Coordinator agent structure test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Coordinator agent structure test failed: {e}")
        return False

def test_config_integration():
    """Test that the coordinator agent properly integrates with config"""
    try:
        # Import the config
        from core.config import MODELS_CONFIG, get_capabilities_prompt
        
        # Check if coordinator config exists
        assert 'coordinator' in MODELS_CONFIG, "Coordinator config should exist"
        coordinator_config = MODELS_CONFIG['coordinator']
        
        # Check required fields
        required_fields = ['name', 'description', 'tool_instructions', 'base_url', 'model', 'temperature', 'max_tokens', 'timeout']
        for field in required_fields:
            assert field in coordinator_config, f"Coordinator config should have {field} field"
        
        # Test get_capabilities_prompt function
        prompt = get_capabilities_prompt('coordinator')
        assert prompt is not None, "get_capabilities_prompt should return a prompt for coordinator"
        assert len(prompt) > 0, "get_capabilities_prompt should return a non-empty prompt"
        
        print("✅ Config integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Config integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing coordinator agent structure and config integration...")
    
    # Test coordinator agent structure
    success1 = test_coordinator_structure()
    
    # Test config integration
    success2 = test_config_integration()
    
    if success1 and success2:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)