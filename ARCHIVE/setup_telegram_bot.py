#!/usr/bin/env python3
"""
Script to set up Telegram bot token for Bldr Empire v2
"""

import os
import sys

def setup_telegram_bot_token():
    """Setup Telegram bot token in environment variables"""
    print("Telegram Bot Setup for Bldr Empire v2")
    print("=" * 40)
    
    # Check if token is already set
    current_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if current_token and current_token != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print(f"Current token is already set: {current_token[:10]}...")
        response = input("Do you want to change it? (y/N): ")
        if response.lower() != 'y':
            print("Keeping current token.")
            return
    
    # Get token from user
    print("\nTo set up the Telegram bot, you need to provide your bot token.")
    print("You can get this from @BotFather on Telegram:")
    print("1. Start a chat with @BotFather")
    print("2. Send /newbot command")
    print("3. Follow the instructions to create your bot")
    print("4. Copy the token provided by BotFather")
    
    token = input("\nEnter your Telegram bot token: ").strip()
    
    if not token:
        print("No token provided. Exiting.")
        return
    
    # Validate token format (should be numbers:letters)
    if ':' not in token or not token.split(':')[0].isdigit():
        print("Warning: Token format doesn't look correct. It should be in the format '123456789:ABCDEF...'")
    
    # Set the token in environment
    os.environ['TELEGRAM_BOT_TOKEN'] = token
    
    # Also write to .env file for persistence
    try:
        with open('.env', 'a+') as f:
            # Read current content
            f.seek(0)
            lines = f.readlines()
            
            # Check if TELEGRAM_BOT_TOKEN already exists
            token_line_exists = False
            for i, line in enumerate(lines):
                if line.startswith('TELEGRAM_BOT_TOKEN='):
                    lines[i] = f'TELEGRAM_BOT_TOKEN={token}\n'
                    token_line_exists = True
                    break
            
            # If not exists, add it
            if not token_line_exists:
                lines.append(f'TELEGRAM_BOT_TOKEN={token}\n')
            
            # Write back
            f.seek(0)
            f.truncate()
            f.writelines(lines)
        
        print(f"\n✅ Telegram bot token has been set and saved to .env file")
        print(f"Token: {token[:10]}...")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not save token to .env file: {e}")
        print("The token is set in environment for this session only.")
    
    # Also set API token for authentication
    api_token = input("\nDo you want to set an API token for authentication? (Enter token or leave blank): ").strip()
    if api_token:
        os.environ['API_TOKEN'] = api_token
        try:
            with open('.env', 'a+') as f:
                # Read current content
                f.seek(0)
                lines = f.readlines()
                
                # Check if API_TOKEN already exists
                api_line_exists = False
                for i, line in enumerate(lines):
                    if line.startswith('API_TOKEN='):
                        lines[i] = f'API_TOKEN={api_token}\n'
                        api_line_exists = True
                        break
                
                # If not exists, add it
                if not api_line_exists:
                    lines.append(f'API_TOKEN={api_token}\n')
                
                # Write back
                f.seek(0)
                f.truncate()
                f.writelines(lines)
            
            print(f"✅ API token has been set and saved to .env file")
        except Exception as e:
            print(f"⚠️  Warning: Could not save API token to .env file: {e}")
    
    print("\n✅ Setup complete!")
    print("To start the Telegram bot, run: python integrations/telegram_bot.py")
    print("To start the main API server, run: python core/main.py")

if __name__ == "__main__":
    setup_telegram_bot_token()