import os
import sys
import time
import redis
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_celery_basics():
    """Test the basic Celery implementation without mocks"""
    print("🚀 Testing Bldr Empire v2 Real Celery Implementation")
    print("=" * 50)
    
    # Test 1: Check if Redis is running
    print("📋 Test 1: Checking Redis connection...")
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running and accessible")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False
    
    # Test 2: Check Celery app configuration
    print("\n📋 Test 2: Checking Celery app configuration...")
    try:
        # Import Celery app directly
        from core.celery_app import celery_app
        print("✅ Celery app imported successfully")
        print(f"   Broker: {celery_app.conf.broker_url}")
        print(f"   Backend: {celery_app.conf.result_backend}")
        print(f"   Task serializer: {celery_app.conf.task_serializer}")
        print(f"   Result serializer: {celery_app.conf.result_serializer}")
    except Exception as e:
        print(f"❌ Celery app import failed: {e}")
        return False
    
    # Test 3: Check if the task is registered
    print("\n📋 Test 3: Checking registered tasks...")
    try:
        tasks = celery_app.tasks.keys()
        update_norms_task_found = False
        for task in tasks:
            if 'update_norms' in task:
                update_norms_task_found = True
                print(f"✅ Found task: {task}")
        
        if not update_norms_task_found:
            print("❌ update_norms task not found in registered tasks")
            return False
            
        print("✅ Task registration verified")
    except Exception as e:
        print(f"❌ Task registration check failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Basic Celery implementation tests completed!")
    print("💡 Next steps: Start Celery worker and test task execution")
    return True

if __name__ == "__main__":
    test_celery_basics()