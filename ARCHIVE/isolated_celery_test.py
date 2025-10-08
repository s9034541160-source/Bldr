#!/usr/bin/env python3
"""
Isolated test for the real Celery implementation without importing the full app
"""

import os
import sys
import importlib.util

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_isolated_celery():
    """Test the Celery implementation in isolation"""
    print("🚀 Testing isolated Celery implementation...")
    
    # Test 1: Check if Celery app can be imported directly
    try:
        # Import only the Celery app without the full FastAPI app
        spec = importlib.util.spec_from_file_location("celery_app", "core/celery_app.py")
        if spec is None:
            print("❌ Failed to create spec for celery_app.py")
            return False
            
        celery_app_module = importlib.util.module_from_spec(spec)
        if spec.loader is not None:
            spec.loader.exec_module(celery_app_module)
        celery_app = celery_app_module.celery_app
        print("✅ Celery app imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Celery app: {e}")
        return False
    
    # Test 2: Check if Celery tasks are registered
    try:
        # Import the norms task module directly
        spec = importlib.util.spec_from_file_location("celery_norms", "core/celery_norms.py")
        if spec is None:
            print("❌ Failed to create spec for celery_norms.py")
            return False
            
        celery_norms_module = importlib.util.module_from_spec(spec)
        if spec.loader is not None:
            spec.loader.exec_module(celery_norms_module)
        
        registered_tasks = list(celery_app.tasks.keys())
        expected_task = 'core.celery_norms.update_norms_task'
        if expected_task in registered_tasks:
            print("✅ Celery tasks are registered correctly")
        else:
            print(f"❌ Celery tasks not registered correctly.")
            print(f"   Expected: {expected_task}")
            print(f"   Registered tasks: {registered_tasks[:10]}...")  # Show first 10 tasks
            return False
    except Exception as e:
        print(f"❌ Failed to check Celery task registration: {e}")
        return False
    
    # Test 3: Check if Redis connection settings are correct
    try:
        broker_url = celery_app.conf.broker_url
        result_backend = celery_app.conf.result_backend
        print(f"✅ Celery broker URL: {broker_url}")
        print(f"✅ Celery result backend: {result_backend}")
        
        # Verify it's using Redis
        if broker_url.startswith('redis://') and result_backend.startswith('redis://'):
            print("✅ Celery is configured to use Redis")
        else:
            print("❌ Celery is not configured to use Redis")
            return False
    except Exception as e:
        print(f"❌ Failed to check Celery configuration: {e}")
        return False
    
    print("\n🎉 All isolated tests passed! The real Celery implementation is ready.")
    return True

if __name__ == "__main__":
    test_isolated_celery()