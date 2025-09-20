#!/usr/bin/env python3
"""
Test script to verify Backend component start functionality
"""

import sys
from pathlib import Path

# Add system_launcher to path
sys.path.append(str(Path(__file__).parent))

from system_launcher.component_manager import SystemComponentManager

def test_backend_start():
    """Test starting Backend component"""
    print("Testing Backend component start...")
    
    # Create component manager
    cm = SystemComponentManager()
    
    # Try to start Backend
    success = cm.start_component('backend')
    
    if success:
        print("Backend started successfully!")
        component = cm.get_component_status('backend')
        if component:
            print(f"Status: {component.status.value}")
            print(f"Health: {component.health.value}")
    else:
        print("Failed to start Backend")
        component = cm.get_component_status('backend')
        if component and component.last_error:
            print(f"Error: {component.last_error}")

if __name__ == "__main__":
    test_backend_start()