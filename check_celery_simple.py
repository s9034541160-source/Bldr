#!/usr/bin/env python3
"""
Simple Celery and Redis checker
"""

import os
import sys
import time
from pathlib import Path

def check_redis():
    """Check Redis connection"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("OK: Redis is available")
        return True
    except Exception as e:
        print(f"ERROR: Redis not available: {e}")
        return False

def check_celery_config():
    """Check Celery configuration"""
    try:
        sys.path.append(str(Path(__file__).parent))
        from core.celery_app import celery_app
        
        print(f"OK: Celery app: {celery_app.main}")
        print(f"OK: Broker: {celery_app.conf.broker_url}")
        print(f"OK: Backend: {celery_app.conf.result_backend}")
        
        # Test broker connection
        try:
            celery_app.control.inspect().stats()
            print("OK: Celery can connect to broker")
            return True
        except Exception as e:
            print(f"ERROR: Celery cannot connect to broker: {e}")
            return False
            
    except Exception as e:
        print(f"ERROR: Celery configuration error: {e}")
        return False

def main():
    print("Checking Celery and Redis status...")
    print("=" * 50)
    
    # Check Redis
    redis_ok = check_redis()
    print()
    
    # Check Celery
    celery_ok = check_celery_config()
    print()
    
    if redis_ok and celery_ok:
        print("SUCCESS: All checks passed!")
        print("TIP: Celery should work correctly")
    else:
        print("PROBLEMS FOUND:")
        if not redis_ok:
            print("   - Redis is not available")
        if not celery_ok:
            print("   - Celery cannot connect")
        
        print("\nRECOMMENDATIONS:")
        print("   1. Check if Redis is running: docker ps | grep redis")
        print("   2. Check environment variables CELERY_BROKER_URL")
        print("   3. Try starting Redis: docker start redis")

if __name__ == "__main__":
    main()
