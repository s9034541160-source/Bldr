#!/usr/bin/env python3
"""
Direct test of authentication without network calls
"""
import os
import sys
import json
from dotenv import load_dotenv

# Add the core directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

def test_auth():
    # Load environment variables
    load_dotenv()
    
    api_token = os.getenv('API_TOKEN')
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    print("=== Environment Variables ===")
    print(f"API Token: {api_token[:20] if api_token else 'None'}...")
    print(f"Telegram Token: {telegram_token[:20] if telegram_token else 'None'}...")
    
    # Test JWT decoding
    if api_token:
        try:
            import jwt
            SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
            payload = jwt.decode(api_token, SECRET_KEY, algorithms=["HS256"])
            print("\n=== JWT Token Decoding ===")
            print(f"✅ Token is valid")
            print(f"Payload: {payload}")
        except Exception as e:
            print(f"\n❌ JWT decoding failed: {e}")
    else:
        print("\n❌ No API token found")
    
    # Test Telegram bot token
    if telegram_token:
        print("\n=== Telegram Bot Token ===")
        if telegram_token != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            print("✅ Telegram bot token is set")
        else:
            print("❌ Telegram bot token is not set (placeholder value)")
    else:
        print("\n❌ No Telegram bot token found")

if __name__ == '__main__':
    test_auth()