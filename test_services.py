#!/usr/bin/env python3
"""
Test script to verify all services are working correctly
"""

import requests
import time
import subprocess
import sys

def test_service(url, service_name):
    """Test if a service is responding"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"[OK] {service_name} is running")
            return True
        else:
            print(f"[ERROR] {service_name} returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] {service_name} is not responding: {e}")
        return False

def test_backend_health():
    """Test the backend health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                print(f"[OK] Backend health check passed")
                print(f"  - Database: {data.get('components', {}).get('db', 'unknown')}")
                print(f"  - Celery: {data.get('components', {}).get('celery', 'unknown')}")
                print(f"  - Endpoints: {data.get('components', {}).get('endpoints', 'unknown')}")
                return True
            else:
                print(f"[ERROR] Backend health check failed: {data}")
                return False
        else:
            print(f"[ERROR] Backend health check returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Backend is not responding: {e}")
        return False

def main():
    """Main test function"""
    print("==========================================")
    print("   Bldr Empire v2 - Service Test Script")
    print("==========================================")
    print()
    
    # Wait a bit for services to start
    print("[INFO] Waiting for services to initialize...")
    time.sleep(10)
    
    # Test services
    services_ok = 0
    total_services = 3
    
    # Test Redis (indirectly through backend)
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("components", {}).get("celery") == "running":
                print("[OK] Redis is accessible (via Celery)")
                services_ok += 1
            else:
                print("[ERROR] Redis is not accessible")
        else:
            print("[ERROR] Cannot verify Redis connectivity")
    except:
        print("[ERROR] Cannot verify Redis connectivity")
    
    # Test Neo4j (indirectly through backend)
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("components", {}).get("db") == "connected":
                print("[OK] Neo4j is connected")
                services_ok += 1
            else:
                print("[ERROR] Neo4j is not connected")
        else:
            print("[ERROR] Cannot verify Neo4j connectivity")
    except:
        print("[ERROR] Cannot verify Neo4j connectivity")
    
    # Test backend health
    if test_backend_health():
        services_ok += 1
    
    print()
    print("==========================================")
    print(f"Test Results: {services_ok}/{total_services} services OK")
    if services_ok == total_services:
        print("All services are running correctly!")
        return 0
    else:
        print("Some services are not running correctly.")
        return 1

if __name__ == "__main__":
    sys.exit(main())