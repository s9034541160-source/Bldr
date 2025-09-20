#!/usr/bin/env python3
"""
Verify that the Celery task is properly registered
"""

import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_celery_task():
    """Verify that the Celery task is properly registered"""
    print("🚀 Verifying Celery task registration...")
    
    try:
        # Import Celery app
        from core.celery_app import celery_app
        print("✅ Celery app imported successfully")
        
        # Import the Celery norms module to register the task
        # We need to do this in a way that avoids Neo4j connection issues
        import core.celery_norms
        print("✅ Celery norms module imported successfully")
        
        # Check if the task is registered
        registered_tasks = list(celery_app.tasks.keys())
        target_task = 'core.celery_norms.update_norms_task'
        
        if target_task in registered_tasks:
            print(f"✅ Task '{target_task}' is properly registered")
            return True
        else:
            print(f"❌ Task '{target_task}' is NOT registered")
            print(f"   Registered tasks: {registered_tasks[:10]}...")  # Show first 10 tasks
            return False
            
    except Exception as e:
        print(f"❌ Error verifying Celery task: {e}")
        return False

if __name__ == "__main__":
    success = verify_celery_task()
    if success:
        print("\n🎉 Celery task verification successful!")
    else:
        print("\n❌ Celery task verification failed!")
        sys.exit(1)