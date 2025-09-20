#!/usr/bin/env python3
"""
Test script to verify component start functionality
"""

import sys
from pathlib import Path

# Add system_launcher to path
sys.path.append(str(Path(__file__).parent))

from system_launcher.component_manager import SystemComponentManager

def test_redis_start():
    """Test starting Redis component"""
    print("Testing Redis component start...")
    
    # Create component manager
    cm = SystemComponentManager()
    
    # Try to start Redis
    success = cm.start_component('redis')
    
    if success:
        print("Redis started successfully!")
        component = cm.get_component_status('redis')
        if component:
            print(f"Status: {component.status.value}")
            print(f"Health: {component.health.value}")
    else:
        print("Failed to start Redis")
        component = cm.get_component_status('redis')
        if component and component.last_error:
            print(f"Error: {component.last_error}")

if __name__ == "__main__":
    test_redis_start()