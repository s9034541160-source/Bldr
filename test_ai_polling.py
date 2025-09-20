#!/usr/bin/env python3
"""
Test script for AI intelligent polling system
"""

import requests
import json
import time
import os

# Configuration
API_BASE = 'http://localhost:8000'

def test_ai_request():
    """Test the AI request with intelligent polling"""
    print("🚀 Testing AI Request with Intelligent Polling")
    
    # Make AI request
    try:
        payload = {
            "prompt": "Explain the importance of construction norms in building safety.",
            "model": "llama3.1"
        }
        
        print("📤 Sending AI request...")
        response = requests.post(f"{API_BASE}/ai", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ AI Request Started: {result}")
            task_id = result.get("task_id")
            print(f"📝 Task ID: {task_id}")
            
            # Wait for completion (in a real scenario, we would monitor via WebSocket)
            print("⏳ Waiting for AI response (up to 2 hours with 5-minute polling)...")
            time.sleep(10)  # Wait a bit to see polling in action
            
            print("✅ Test completed. In a real scenario, you would monitor progress via WebSocket updates.")
        else:
            print(f"❌ Failed to start AI request: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")

if __name__ == "__main__":
    test_ai_request()