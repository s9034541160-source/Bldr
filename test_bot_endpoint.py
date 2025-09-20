#!/usr/bin/env python3
"""
Test script to verify /bot endpoint is working correctly with the Telegram bot
"""

import requests
import json
import os

def test_bot_endpoint():
    """Test the /bot endpoint"""
    print("Testing /bot endpoint with Telegram bot...")
    
    # First get a token
    token_url = "http://localhost:8000/token"
    try:
        token_response = requests.post(token_url)
        if token_response.status_code != 200:
            print(f"❌ Failed to get access token: {token_response.status_code}")
            return
            
        token_data = token_response.json()
        token = token_data.get("access_token")
        
        if not token:
            print("❌ Failed to get access token")
            return
            
        print("✅ Got access token")
        
        # Test the /bot endpoint
        bot_url = "http://localhost:8000/bot"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # Note: We're testing with form data, not JSON
        test_data = {
            "cmd": "test command"
        }
        
        print("📝 Testing /bot endpoint with cmd: 'test command'")
        
        response = requests.post(bot_url, headers=headers, data=test_data)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        # The /bot endpoint should return 200 if the command was sent successfully
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("status") == "sent":
                print("✅ /bot endpoint is working correctly!")
                print("   The command was successfully sent to the Telegram bot")
            else:
                print("⚠️  /bot endpoint responded but status is not 'sent'")
        elif response.status_code == 501:
            print("❌ Telegram bot is not configured properly")
        elif response.status_code == 500:
            print("❌ Error sending command to Telegram bot")
        elif response.status_code == 401:
            print("❌ Authentication failed")
        else:
            print(f"❓ /bot endpoint returned unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing /bot endpoint: {e}")

if __name__ == "__main__":
    test_bot_endpoint()