import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_minimal_celery():
    """Minimal test of Celery setup"""
    print("🚀 Testing Bldr Empire v2 Real Celery Implementation")
    print("=" * 50)
    
    # Test 1: Check Celery app configuration
    print("📋 Test 1: Checking Celery app configuration...")
    try:
        # Import only the Celery app, not the full module
        from core.celery_app import celery_app
        print("✅ Celery app imported successfully")
        print(f"   App name: {celery_app.main}")
        print(f"   Broker: {celery_app.conf.broker_url}")
        print(f"   Backend: {celery_app.conf.result_backend}")
        print(f"   Included modules: {celery_app.conf.include}")
    except Exception as e:
        print(f"❌ Celery app import failed: {e}")
        return False
    
    # Test 2: Check task module exists
    print("\n📋 Test 2: Checking task module exists...")
    try:
        # Check if the file exists
        task_file = os.path.join(os.path.dirname(__file__), 'core', 'celery_norms.py')
        if os.path.exists(task_file):
            print("✅ celery_norms.py file exists")
        else:
            print("❌ celery_norms.py file not found")
            return False
    except Exception as e:
        print(f"❌ Task module check failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Minimal Celery setup tests completed!")
    print("💡 Next steps: Verify task registration and execution")
    return True

if __name__ == "__main__":
    test_minimal_celery()