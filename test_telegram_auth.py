#!/usr/bin/env python3
"""
Test script to verify Telegram bot authentication
"""
import os
import requests

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_telegram_config():
    """Test Telegram configuration"""
    print("=== Telegram Bot Configuration Test ===")
    
    # Check Telegram bot token
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_token or telegram_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("❌ TELEGRAM_BOT_TOKEN not set or using default value")
        print("   Please set TELEGRAM_BOT_TOKEN in your .env file")
        return False
    else:
        print(f"✅ TELEGRAM_BOT_TOKEN is set: {telegram_token[:10]}...")
    
    # Check API token
    api_token = os.getenv("API_TOKEN")
    if not api_token:
        print("❌ API_TOKEN not set")
        print("   Please set API_TOKEN in your .env file")
        return False
    else:
        print(f"✅ API_TOKEN is set: {api_token[:10]}...")
    
    return True

def test_api_auth():
    """Test API authentication"""
    print("\n=== API Authentication Test ===")
    
    api_token = os.getenv("API_TOKEN")
    if not api_token:
        print("❌ Cannot test API auth without API_TOKEN")
        return False
    
    # Test health endpoint with token
    API_BASE = 'http://localhost:8000'
    try:
        headers = {
            "Authorization": f"Bearer {api_token}"
        }
        
        response = requests.get(f'{API_BASE}/health', headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API authentication successful: {data}")
            return True
        else:
            print(f"❌ API authentication failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ API authentication error: {e}")
        return False

def main():
    """Main test function"""
    telegram_ok = test_telegram_config()
    api_ok = test_api_auth()
    
    if telegram_ok and api_ok:
        print("\n🎉 All Telegram authentication tests passed!")
    else:
        print("\n❌ Some authentication tests failed!")

if __name__ == "__main__":
    main()