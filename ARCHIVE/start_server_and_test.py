#!/usr/bin/env python3
"""
Script to start the server and test the full processing chain
"""

import subprocess
import time
import requests
import json
import sys
import os

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI server...")
    
    # Change to the project directory
    os.chdir(r"c:\Bldr")
    
    # Start the server in the background
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "core.bldr_api:app", 
            "--host", "localhost", 
            "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"✅ Server started with PID {process.pid}")
        return process
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None

def wait_for_server(timeout=30):
    """Wait for the server to be ready"""
    print("⏳ Waiting for server to be ready...")
    
    for i in range(timeout):
        try:
            response = requests.get("http://localhost:8000/health", timeout=1)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except:
            pass
        
        print(f"⏳ Still waiting... ({i+1}/{timeout})")
        time.sleep(1)
    
    print("❌ Server failed to start in time")
    return False

def test_chain():
    """Test the full processing chain"""
    print("🧪 Testing full processing chain...")
    
    try:
        # Get authentication token
        print("1️⃣ Getting authentication token...")
        token_response = requests.post("http://localhost:8000/token")
        if token_response.status_code != 200:
            print(f"❌ Failed to get token: {token_response.status_code}")
            return False
            
        token = token_response.json()["access_token"]
        print(f"✅ Got token: {token[:20]}...")
        
        # Test the AI chat endpoint
        print("2️⃣ Testing AI chat endpoint...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        chat_payload = {
            'message': 'привет. расскажи о себе. что знаешь, что умеешь?',
            'context_search': True,
            'max_context': 3,
            'agent_role': 'coordinator',
            'request_context': {
                'channel': 'telegram',
                'chat_id': 123456789,
                'user_id': 987654321
            }
        }
        
        response = requests.post(
            "http://localhost:8000/api/ai/chat",
            json=chat_payload,
            headers=headers,
            timeout=1800
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Full chain test successful!")
            print(f"   🤖 Agent used: {result.get('agent_used')}")
            print(f"   📁 Context documents: {len(result.get('context_used', []))}")
            print(f"   ⚡ Processing time: {result.get('processing_time', 0):.2f}s")
            print(f"   💬 Response preview: {result.get('response', '')[:200]}...")
            return True
        else:
            print(f"❌ AI chat failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing chain: {e}")
        return False

def main():
    print("🚀 STARTING SERVER AND CHAIN VERIFICATION")
    print("=" * 60)
    
    # Start the server
    server_process = start_server()
    if not server_process:
        return
    
    # Wait for server to be ready
    if not wait_for_server():
        server_process.terminate()
        return
    
    # Wait a bit more for initialization
    time.sleep(5)
    
    # Test the chain
    success = test_chain()
    
    # Stop the server
    print("🛑 Stopping server...")
    server_process.terminate()
    
    # Print final result
    print("\n" + "=" * 60)
    if success:
        print("🎉 SUCCESS: Full processing chain is working correctly!")
        print("\n📋 Chain Flow:")
        print("   1. Telegram Bot → /api/ai/chat endpoint")
        print("   2. Coordinator Agent generates plan")
        print("   3. Specialist Agents execute plan")
        print("   4. Coordinator generates final response")
        print("   5. Response sent back to Telegram Bot")
    else:
        print("❌ FAILURE: There are issues with the processing chain")
    
    print("=" * 60)

if __name__ == "__main__":
    main()