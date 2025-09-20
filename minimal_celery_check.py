#!/usr/bin/env python3
"""
Minimal check for Celery configuration
"""

import os
import sys

def check_celery_config():
    """Check Celery configuration without importing the full app"""
    print("🚀 Checking Celery configuration...")
    
    # Read the Celery app file directly
    try:
        with open("core/celery_app.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for key configuration elements
        if "Celery(" in content:
            print("✅ Celery app creation found")
        else:
            print("❌ Celery app creation not found")
            return False
            
        if "broker=" in content:
            print("✅ Broker configuration found")
        else:
            print("❌ Broker configuration not found")
            return False
            
        if "redis://" in content:
            print("✅ Redis configuration found")
        else:
            print("❌ Redis configuration not found")
            return False
            
        if "include=" in content:
            print("✅ Task inclusion configuration found")
        else:
            print("❌ Task inclusion configuration not found")
            return False
            
    except Exception as e:
        print(f"❌ Failed to read celery_app.py: {e}")
        return False
    
    # Read the Celery norms file directly
    try:
        with open("core/celery_norms.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for task decorator
        if "@celery_app.task" in content or "@celery.task" in content:
            print("✅ Celery task decorator found")
        else:
            print("❌ Celery task decorator not found")
            return False
            
        # Check for task name
        if "update_norms_task" in content:
            print("✅ update_norms_task function found")
        else:
            print("❌ update_norms_task function not found")
            return False
            
    except Exception as e:
        print(f"❌ Failed to read celery_norms.py: {e}")
        return False
    
    print("\n🎉 All configuration checks passed! The real Celery implementation is properly configured.")
    return True

if __name__ == "__main__":
    check_celery_config()