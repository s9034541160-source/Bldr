import os
import sys
import time
from dotenv import load_dotenv

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()

from core.celery_app import celery_app
from core.celery_norms import update_norms_task

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
        else:
            print("⚠️  No Celery workers found")
            
        # Test a simple task
        # Type ignore to avoid linting error
        result = update_norms_task.delay(['construction'], True)  # type: ignore
        print(f"✅ Test task queued with ID: {result.id}")
        
        # Wait a moment and check status
        time.sleep(2)
        print(f"   Task status: {result.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Celery connection...")
    test_celery_connection()