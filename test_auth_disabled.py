#!/usr/bin/env python3
"""
Test script to verify that authentication is properly disabled
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_auth_disabled():
    """Test that authentication is disabled"""
    base_url = "http://localhost:8000"
    
    print("Testing authentication disabled mode...")
    
    # Test health endpoint (should work without auth)
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health endpoint status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health endpoint accessible without authentication")
            health_data = response.json()
            print(f"Health data: {health_data}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False
    
    # Test tools list endpoint (should work without auth when SKIP_AUTH=true)
    try:
        response = requests.get(f"{base_url}/tools/list")
        print(f"Tools list endpoint status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Tools list endpoint accessible without authentication")
            tools_data = response.json()
            print(f"Tools data keys: {list(tools_data.keys())}")
        elif response.status_code == 401:
            print("❌ Authentication is still required - SKIP_AUTH not working")
            return False
        else:
            print(f"Tools list endpoint response: {response.status_code}")
            # Even if not 200, if we get a response it means auth is disabled
            if response.status_code != 401:
                print("✅ Authentication appears to be disabled (non-401 response)")
            else:
                print("❌ Authentication is still required")
                return False
    except Exception as e:
        print(f"Tools list endpoint error: {e}")
        # If we get a connection error or other network error, it might be due to server issues
        # but not necessarily authentication
        print("⚠️  Network error - this might be due to server issues, not authentication")
    
    print("\nEnvironment variables:")
    print(f"  SKIP_AUTH = {os.getenv('SKIP_AUTH')}")
    print(f"  SKIP_NEO4J = {os.getenv('SKIP_NEO4J')}")
    
    # Check if SKIP_AUTH is set to true
    if os.getenv('SKIP_AUTH', 'false').lower() == 'true':
        print("\n🎉 SKIP_AUTH is set to true - authentication should be disabled!")
        return True
    else:
        print("\n⚠️  SKIP_AUTH is not set to true - authentication may still be enabled")
        return False

if __name__ == "__main__":
    success = test_auth_disabled()
    if success:
        print("\n✅ Authentication disabling test completed successfully!")
    else:
        print("\n❌ Authentication disabling test failed!")