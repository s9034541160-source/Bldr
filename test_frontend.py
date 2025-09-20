#!/usr/bin/env python3
"""
Test script to verify frontend component startup
"""

import sys
import os
from pathlib import Path

# Add system_launcher to path
system_launcher_path = Path(__file__).parent / 'system_launcher'
sys.path.insert(0, str(system_launcher_path))

from component_manager import SystemComponentManager, ComponentStatus
import time
import requests

def test_frontend_startup():
    """Test frontend component startup"""
    print("Testing frontend component startup...")
    
    # Create component manager
    manager = SystemComponentManager()
    
    # Start components in correct order (simulating what start_all_components would do)
    print("\nStarting Redis dependency first...")
    redis_success = manager.start_component('redis')
    if not redis_success:
        print("ERROR: Failed to start Redis dependency")
        redis_status = manager.get_component_status('redis')
        if redis_status and redis_status.last_error:
            print(f"  Redis error: {redis_status.last_error}")
        return False
    else:
        print("✓ Redis dependency started successfully")
        
    # Wait for Redis to stabilize
    time.sleep(3)
    
    print("\nStarting Celery Worker dependency...")
    celery_worker_success = manager.start_component('celery_worker')
    if not celery_worker_success:
        print("ERROR: Failed to start Celery Worker dependency")
        celery_worker_status = manager.get_component_status('celery_worker')
        if celery_worker_status and celery_worker_status.last_error:
            print(f"  Celery Worker error: {celery_worker_status.last_error}")
        return False
    else:
        print("✓ Celery Worker dependency started successfully")
        
    # Wait for Celery Worker to stabilize
    time.sleep(3)
    
    print("\nStarting backend dependency...")
    backend_success = manager.start_component('backend')
    if not backend_success:
        print("ERROR: Failed to start backend dependency")
        backend_status = manager.get_component_status('backend')
        if backend_status and backend_status.last_error:
            print(f"  Backend error: {backend_status.last_error}")
        return False
    else:
        print("✓ Backend dependency started successfully")
        
    # Wait for backend to stabilize
    time.sleep(5)
    
    # Get frontend component
    frontend_component = manager.get_component_status('frontend')
    if not frontend_component:
        print("ERROR: Frontend component not found")
        return False
        
    print(f"Frontend component config:")
    print(f"  Working dir: {frontend_component.config['working_dir']}")
    print(f"  Start command: {frontend_component.config['start_command']}")
    print(f"  Health URL: {frontend_component.config['health_url']}")
    
    # Check if package.json exists
    package_json = frontend_component.config['working_dir'] / 'package.json'
    if not package_json.exists():
        print(f"ERROR: package.json not found at {package_json}")
        return False
        
    print(f"✓ package.json found at {package_json}")
    
    # Check if node_modules exists
    node_modules = frontend_component.config['working_dir'] / 'node_modules'
    if not node_modules.exists():
        print(f"WARNING: node_modules not found at {node_modules}")
        print("  This is OK if npm install will be run during startup")
    else:
        print(f"✓ node_modules found at {node_modules}")
        
    # Try to start the frontend component
    print("\nAttempting to start frontend component...")
    success = manager.start_component('frontend')
    
    if success:
        print("✓ Frontend component started successfully")
        # Wait a bit to see if it stays running
        time.sleep(10)
        status = manager.get_component_status('frontend')
        if status and status.status == ComponentStatus.RUNNING:
            print("✓ Frontend component is still running")
            return True
        else:
            print(f"✗ Frontend component status: {status.status if status else 'Unknown'}")
            return False
    else:
        print("✗ Failed to start frontend component")
        status = manager.get_component_status('frontend')
        if status and status.last_error:
            print(f"  Error: {status.last_error}")
        return False

if __name__ == "__main__":
    test_frontend_startup()