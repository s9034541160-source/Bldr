#!/usr/bin/env python3
"""
Test script to verify the full processing chain is working correctly
"""

import requests
import json
import os
import time

def test_processing_chain():
    """Test the full processing chain from Telegram bot to coordinator agent"""
    print("🔍 Testing full processing chain...")
    
    # Get API token
    try:
        token_response = requests.post("http://localhost:8000/token")
        if token_response.status_code != 200:
            print(f"❌ Failed to get access token: {token_response.status_code}")
            return False
            
        token_data = token_response.json()
        token = token_data["access_token"]
        print("✅ Got access token")
        
    except Exception as e:
        print(f"❌ Error getting access token: {e}")
        return False
    
    # Test payload similar to what Telegram bot sends
    chat_payload = {
        'message': 'привет. расскажи о себе. что знаешь, что умеешь?',
        'context_search': True,
        'max_context': 3,
        'agent_role': 'coordinator',
        'request_context': {
            'channel': 'telegram',
            'chat_id': 123456789,  # Test chat ID
            'user_id': 987654321   # Test user ID
        }
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("📤 Sending request to /api/ai/chat endpoint...")
        response = requests.post(
            "http://localhost:8000/api/ai/chat",
            json=chat_payload,
            headers=headers,
            timeout=1800
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AI chat successful")
            print(f"   🤖 Agent used: {result.get('agent_used')}")
            print(f"   📁 Context documents: {len(result.get('context_used', []))}")
            print(f"   ⚡ Processing time: {result.get('processing_time', 0):.2f}s")
            print(f"   💬 Response preview: {result.get('response', '')[:200]}...")
            
            # Check that the coordinator agent was used
            if result.get('agent_used') == 'coordinator':
                print("✅ Correctly used coordinator agent")
            else:
                print(f"⚠️  Expected coordinator agent, but got: {result.get('agent_used')}")
            
            return True
        else:
            print(f"❌ AI chat failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing processing chain: {e}")
        return False

if __name__ == "__main__":
    test_processing_chain()