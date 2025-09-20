#!/usr/bin/env python3
"""
Comprehensive test for the real Celery implementation
"""

import os
import sys
import time
import requests
import json
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_end_to_end_celery():
    """Test the end-to-end Celery implementation"""
    print("🚀 Starting comprehensive Celery test...")
    
    # Test 1: Check if all services are running
    print("\n1. Checking service status...")
    
    # Check Redis
    try:
        import redis
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        redis_client.ping()
        print("✅ Redis is running")
    except Exception as e:
        print(f"❌ Redis is not running: {e}")
        return False
    
    # Check if FastAPI server is running
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
    
    # Test 2: Test Celery task registration
    print("\n2. Testing Celery task registration...")
    try:
        from core.celery_app import celery_app
        from core.celery_norms import update_norms_task
        
        registered_tasks = list(celery_app.tasks.keys())
        expected_task = 'core.celery_norms.update_norms_task'
        
        if expected_task in registered_tasks:
            print("✅ Celery task is properly registered")
        else:
            print(f"❌ Celery task '{expected_task}' is not registered")
            print(f"   Registered tasks: {registered_tasks}")
            return False
    except Exception as e:
        print(f"❌ Failed to check Celery task registration: {e}")
        return False
    
    # Test 3: Test queue endpoint
    print("\n3. Testing queue endpoint...")
    try:
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
        return False
    
    # Test 4: Test norms-update endpoint
    print("\n4. Testing norms-update endpoint...")
    try:
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
        return False
    
    # Test 5: Test actual task queuing (this would require authentication)
    print("\n5. Testing actual task queuing...")
    print("   Note: This test requires a valid authentication token")
    print("   To fully test this, you would need to:")
    print("   1. Obtain a valid JWT token from the /token endpoint")
    print("   2. Use that token to make authenticated requests")
    print("   3. Verify that tasks are properly queued and executed")
    
    # Test 6: Verify Celery worker can be started
    print("\n6. Verifying Celery worker can be started...")
    print("   To test this:")
    print("   1. Run: celery -A core.celery_app worker --loglevel=info")
    print("   2. Check that the worker starts without errors")
    print("   3. Verify that it connects to Redis successfully")
    
    # Test 7: Verify Celery beat can be started
    print("\n7. Verifying Celery beat can be started...")
    print("   To test this:")
    print("   1. Run: celery -A core.celery_app beat --loglevel=info")
    print("   2. Check that the beat scheduler starts without errors")
    print("   3. Verify that scheduled tasks are registered")
    
    print("\n🎉 Comprehensive test completed!")
    print("\n📝 Next steps to fully verify the implementation:")
    print("1. Start all services with: docker-compose up -d")
    print("2. Start Celery worker: celery -A core.celery_app worker --loglevel=info")
    print("3. Start Celery beat: celery -A core.celery_app beat --loglevel=info")
    print("4. Obtain a valid JWT token from the /token endpoint")
    print("5. Make an authenticated POST request to /norms-update")
    print("6. Check the worker logs to see the task being processed")
    print("7. Verify that Neo4j is updated with task information")
    print("8. Check that WebSocket updates are sent to connected clients")
    
    return True

if __name__ == "__main__":
    test_end_to_end_celery()