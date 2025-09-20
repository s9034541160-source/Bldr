import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from core.celery_app import celery_app

def test_celery_connection():
    """Test Celery connection to Redis broker"""
    try:
        # Test broker connection
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print("✅ Celery broker connection successful")
            print(f"   Connected workers: {len(stats)}")
            for worker, info in stats.items():
                print(f"   Worker: {worker}")
            return True
        else:
            print("⚠️  No Celery workers found")
            return False
            
    except Exception as e:
        print(f"❌ Celery connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Celery connection from API context...")
    test_celery_connection()