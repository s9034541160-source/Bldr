#!/usr/bin/env python3
"""
Test script for Telegram bot multimedia processing fixes
"""

import json
import requests
import base64
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_api_chat_endpoint():
    """Test the /api/ai/chat endpoint with different message types"""
    
    api_base = "http://localhost:8000"
    api_token = os.getenv('API_TOKEN', 'test-token-123')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_token}'
    }
    
    print("🧪 Testing Telegram Bot API Fixes")
    print("=" * 50)
    
    # Test 1: Simple text message
    print("\n📝 Test 1: Simple text message")
    test_data = {
        "message": "Hello, this is a test message",
        "context_search": False,
        "max_context": 1,
        "agent_role": "coordinator"
    }
    
    try:
        response = requests.post(f"{api_base}/api/ai/chat", json=test_data, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('response', 'No response')[:100]}...")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Voice message (empty base64 to test error handling)
    print("\n🎤 Test 2: Voice message processing")
    test_data = {
        "message": "Voice message",
        "context_search": False,
        "max_context": 1,
        "agent_role": "coordinator",
        "voice_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="  # Small test image as base64
    }
    
    try:
        response = requests.post(f"{api_base}/api/ai/chat", json=test_data, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Voice handling: {result.get('response', 'No response')[:100]}...")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Image message
    print("\n📸 Test 3: Image message processing")
    test_data = {
        "message": "Analyze this image",
        "context_search": False,
        "max_context": 1,
        "agent_role": "coordinator",
        "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="  # 1x1 pixel PNG in base64
    }
    
    try:
        response = requests.post(f"{api_base}/api/ai/chat", json=test_data, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Image handling: {result.get('response', 'No response')[:100]}...")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 4: Document message
    print("\n📄 Test 4: Document message processing")
    # Create a simple text file in base64
    test_text = "This is a test document for processing"
    doc_base64 = base64.b64encode(test_text.encode()).decode()
    
    test_data = {
        "message": "Analyze this document",
        "context_search": False,
        "max_context": 1,
        "agent_role": "coordinator",
        "document_data": doc_base64,
        "document_name": "test.txt"
    }
    
    try:
        response = requests.post(f"{api_base}/api/ai/chat", json=test_data, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Document handling: {result.get('response', 'No response')[:100]}...")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Testing completed!")
    print("\n💡 If you see responses instead of 'NoneType' errors,")
    print("   the fixes are working correctly!")

def check_backend_running():
    """Check if backend server is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🔍 Checking if backend is running...")
    if not check_backend_running():
        print("❌ Backend server is not running!")
        print("   Start it with: python backend/main.py")
        print("   Then run this test again.")
        sys.exit(1)
    
    print("✅ Backend server is running")
    test_api_chat_endpoint()