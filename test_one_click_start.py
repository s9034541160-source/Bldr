#!/usr/bin/env python3
"""
Test script to verify that the one-click start functionality works correctly
by checking if all required services are running.
"""

import requests
import time
import subprocess
import sys
from typing import List, Tuple, Callable

def check_port_open(port: int) -> bool:
    """Check if a port is open by trying to connect to it."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result == 0
    except Exception:
        return False

def check_api_health() -> bool:
    """Check if the API server is responding to health checks."""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def check_redis_connection() -> bool:
    """Check if Redis is accessible."""
    try:
        # Try to ping Redis using redis-cli
        result = subprocess.run(['redis-cli', 'ping'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0 and 'PONG' in result.stdout
    except Exception:
        return False

def check_celery_workers() -> bool:
    """Check if Celery workers are running."""
    try:
        # Try to inspect Celery workers
        result = subprocess.run([
            'python', '-m', 'celery', '-A', 'core.celery_app', 'inspect', 'stats'
        ], capture_output=True, text=True, timeout=10, cwd='c:\\Bldr')
        
        # If the command succeeds and returns stats, workers are running
        return result.returncode == 0 and 'stats' in result.stdout.lower()
    except Exception:
        return False

def main():
    """Main test function."""
    print("Testing Bldr Empire v2 One-Click Start Services...")
    print("=" * 50)
    
    # Wait a bit for services to start
    print("Waiting for services to start...")
    time.sleep(10)
    
    tests: List[Tuple[str, Callable[[], bool]]] = [
        ("API Server (Port 8000)", lambda: check_port_open(8000)),
        ("API Health Check", check_api_health),
        ("Redis Server (Port 6379)", lambda: check_port_open(6379)),
        ("Redis Connection", check_redis_connection),
        ("Celery Workers", check_celery_workers),
    ]
    
    results = []
    all_passed = True
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            status = "PASS" if result else "FAIL"
            print(f"{test_name:.<30} {status}")
            results.append((test_name, result))
            if not result:
                all_passed = False
        except Exception as e:
            print(f"{test_name:.<30} ERROR - {str(e)}")
            results.append((test_name, False))
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("All services are running correctly! ✓")
        return 0
    else:
        print("Some services are not running properly! ✗")
        return 1

if __name__ == "__main__":
    sys.exit(main())