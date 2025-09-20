#!/usr/bin/env python3
"""
Test script to verify Celery component start functionality
"""

import sys
from pathlib import Path

# Add system_launcher to path
sys.path.append(str(Path(__file__).parent))

from system_launcher.component_manager import SystemComponentManager

def test_celery_start():
    """Test starting Celery components"""
    print("Testing Celery Worker component start...")
    
    # Create component manager
    cm = SystemComponentManager()
    
    # Try to start Celery Worker
    success = cm.start_component('celery_worker')
    
    if success:
        print("Celery Worker started successfully!")
        component = cm.get_component_status('celery_worker')
        if component:
            print(f"Status: {component.status.value}")
            print(f"Health: {component.health.value}")
    else:
        print("Failed to start Celery Worker")
        component = cm.get_component_status('celery_worker')
        if component and component.last_error:
            print(f"Error: {component.last_error}")

if __name__ == "__main__":
    test_celery_start()