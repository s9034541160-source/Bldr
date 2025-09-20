import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_health_check_logic():
    """Test the health check logic"""
    try:
        # Import the same way as in bldr_api.py
        from core.celery_app import celery_app
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            celery_ok = True
            print("✅ Celery workers detected")
        else:
            celery_ok = False
            print("❌ No Celery workers detected")
            
        print(f"Celery status: {'running' if celery_ok else 'stopped'}")
        
    except Exception as e:
        print(f"❌ Error in health check logic: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing health check logic...")
    test_health_check_logic()