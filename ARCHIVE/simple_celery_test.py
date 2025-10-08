#!/usr/bin/env python3
"""
Simple test for the real Celery implementation
"""

import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_celery_basics():
    """Test the basic Celery implementation"""
    print("🚀 Testing basic Celery implementation...")
    
    # Test 1: Check if Celery app can be imported
    try:
        from core.celery_app import celery_app
        print("✅ Celery app imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Celery app: {e}")
        return False
    
    # Test 2: Check if Celery tasks are registered
    try:
        from core.celery_norms import update_norms_task
        registered_tasks = list(celery_app.tasks.keys())
        if 'core.celery_norms.update_norms_task' in registered_tasks:
            print("✅ Celery tasks are registered correctly")
        else:
            print(f"❌ Celery tasks not registered correctly. Registered tasks: {registered_tasks}")
            return False
    except Exception as e:
        print(f"❌ Failed to check Celery task registration: {e}")
        return False
    
    # Test 3: Check if Redis is accessible
    try:
        import redis
        redis_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        # Parse the Redis URL to get host and port
        if redis_url.startswith('redis://'):
            host_port = redis_url[8:].split('/')[0]
            if ':' in host_port:
                host, port = host_port.split(':')
                port = int(port)
            else:
                host = host_port
                port = 6379
                
            r = redis.Redis(host=host, port=port)
            r.ping()
            print("✅ Redis is accessible")
        else:
            print("⚠️  Could not parse Redis URL, skipping Redis test")
    except Exception as e:
        print(f"❌ Redis is not accessible: {e}")
        return False
    
    print("\n🎉 All basic tests passed! The real Celery implementation is ready.")
    return True

if __name__ == "__main__":
    test_celery_basics()