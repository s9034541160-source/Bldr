import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_task_registration():
    """Verify that our task is properly registered with Celery"""
    print("🔍 Verifying task registration...")
    print("=" * 50)
    
    try:
        # Import the Celery app
        from core.celery_app import celery_app
        print("✅ Celery app imported")
        
        # Import the task module to trigger task registration
        print("🔄 Importing celery_norms module to register tasks...")
        import core.celery_norms
        print("✅ celery_norms module imported")
        
        # Check registered tasks
        print("\n📋 Registered tasks:")
        tasks = list(celery_app.tasks.keys())
        for task in sorted(tasks):
            print(f"   - {task}")
        
        # Check specifically for our task
        our_task_name = 'core.celery_norms.update_norms_task'
        if our_task_name in tasks:
            print(f"\n✅ Our task '{our_task_name}' is properly registered!")
            return True
        else:
            print(f"\n❌ Our task '{our_task_name}' is NOT registered!")
            print("   This might be because the task decorator name doesn't match.")
            return False
            
    except Exception as e:
        print(f"❌ Task registration verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verify_task_registration()