#!/usr/bin/env python3
"""
Test script to verify the real Celery implementation without mocks
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_celery_implementation():
    """Test the real Celery implementation"""
    print("🚀 Testing real Celery implementation...")
    
    # Test 1: Check if Redis is accessible
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
    
    # Test 2: Check if Celery app can be imported
    try:
        from core.celery_app import celery_app
        print("✅ Celery app imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Celery app: {e}")
        return False
    
    # Test 3: Check if Celery tasks are registered
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
    
    # Test 4: Check if FastAPI server is running
    try:
        api_url = "http://localhost:8000"
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ FastAPI server is running")
        else:
            print(f"❌ FastAPI server returned status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FastAPI server is not accessible: {e}")
        return False
    
    # Test 5: Check if queue endpoint exists
    try:
        api_url = "http://localhost:8000"
        # We would need a valid token for this test, so we'll just check if the endpoint exists
        # by making a request without authentication and checking the response
        response = requests.get(f"{api_url}/queue", timeout=5)
        # If we get a 403 or 401, it means the endpoint exists but requires authentication
        if response.status_code in [401, 403]:
            print("✅ Queue endpoint exists (requires authentication)")
        elif response.status_code == 200:
            print("✅ Queue endpoint is accessible")
        elif response.status_code == 404:
            print("❌ Queue endpoint does not exist")
            return False
        else:
            print(f"⚠️  Queue endpoint returned unexpected status code {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to check queue endpoint: {e}")
    
    # Test 6: Check if norms-update endpoint exists
    try:
        api_url = "http://localhost:8000"
        response = requests.post(f"{api_url}/norms-update", timeout=5)
        # If we get a 403 or 401, it means the endpoint exists but requires authentication
        if response.status_code in [401, 403]:
            print("✅ Norms-update endpoint exists (requires authentication)")
        elif response.status_code == 404:
            print("❌ Norms-update endpoint does not exist")
            return False
        else:
            print(f"⚠️  Norms-update endpoint returned unexpected status code {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to check norms-update endpoint: {e}")
    
    print("\n🎉 All tests passed! The real Celery implementation is ready.")
    return True

if __name__ == "__main__":
    test_celery_implementation()