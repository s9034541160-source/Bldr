#!/usr/bin/env python3
"""
Test script to verify Telegram bot configuration
"""

import os
import sys

def test_telegram_bot_config():
    """Test Telegram bot configuration"""
    print("Testing Telegram Bot Configuration...")
    print("=" * 40)
    
    # Load environment variables from .env file
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Check Telegram bot token
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not telegram_token:
        print("❌ TELEGRAM_BOT_TOKEN is not set")
        return False
    
    if telegram_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("❌ TELEGRAM_BOT_TOKEN is set to default placeholder value")
        return False
    
    print(f"✅ TELEGRAM_BOT_TOKEN is set: {telegram_token[:10]}...")
    
    # Check if token format looks correct
    if ':' not in telegram_token or not telegram_token.split(':')[0].isdigit():
        print("⚠️  Warning: Token format doesn't look correct. It should be in the format '123456789:ABCDEF...'")
    
    # Check API token
    api_token = os.getenv('API_TOKEN')
    if api_token:
        print(f"✅ API_TOKEN is set: {api_token[:10]}...")
    else:
        print("ℹ️  API_TOKEN is not set (optional)")
    
    # Try to import telegram libraries
    try:
        import telegram
        from telegram.ext import Application
        print("✅ Telegram libraries are available")
    except ImportError:
        print("❌ Telegram libraries are not installed")
        print("   Run: pip install python-telegram-bot")
        return False
    
    # Try to create application instance (without actually running it)
    try:
        app = Application.builder().token(telegram_token).build()
        print("✅ Telegram bot application can be created with the provided token")
    except Exception as e:
        print(f"❌ Error creating Telegram bot application: {e}")
        return False
    
    print("\n✅ All tests passed! Telegram bot should work correctly.")
    print("\nTo start the Telegram bot, run:")
    print("   python integrations/telegram_bot.py")
    
    return True

if __name__ == "__main__":
    test_telegram_bot_config()