#!/usr/bin/env python3
"""
Test script for Bldr backend API endpoints
"""

import requests
import json
import sys
import subprocess
import time
import os

# Change to the project directory
os.chdir(r"c:\Bldr")

# Start the FastAPI backend
print("Starting FastAPI backend...")
backend_process = subprocess.Popen([
    "python", "-m", "uvicorn", "core.bldr_api:app", 
    "--host", "127.0.0.1", 
    "--port", "8000", 
    "--reload"
], shell=True)

print(f"Backend process started with PID: {backend_process.pid}")

# Wait a bit for the backend to start
time.sleep(10)

# Check if the process is still running
if backend_process.poll() is None:
    print("Backend process is still running")
else:
    print(f"Backend process exited with code: {backend_process.returncode}")

# Keep the script running to see the output
try:
    backend_process.wait()
except KeyboardInterrupt:
    print("Stopping backend process...")
    backend_process.terminate()

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print("✓ Health check passed")
        else:
            print(f"✗ Health check failed: {response.text}")
    except Exception as e:
        print(f"✗ Health check error: {e}")
    print()

def test_metrics():
    """Test metrics endpoint"""
    print("Testing metrics endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/metrics-json")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print("✓ Metrics check passed")
        else:
            print(f"✗ Metrics check failed: {response.text}")
    except Exception as e:
        print(f"✗ Metrics check error: {e}")
    print()

def test_query():
    """Test query endpoint"""
    print("Testing query endpoint...")
    try:
        query_data = {
            "query": "cl.5.2 СП31",
            "k": 5
        }
        response = requests.post(f"{BASE_URL}/query", json=query_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Results count: {len(data.get('results', []))}")
            print("✓ Query check passed")
        else:
            print(f"✗ Query check failed: {response.text}")
    except Exception as e:
        print(f"✗ Query check error: {e}")
    print()

def main():
    """Run all tests"""
    print("Bldr Backend API Test Suite")
    print("=" * 50)
    
    try:
        test_health()
        test_metrics()
        test_query()
        
        print("All tests completed!")
    except Exception as e:
        print(f"Test suite failed: {e}")

if __name__ == "__main__":
    main()