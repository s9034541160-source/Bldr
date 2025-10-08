import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the Telegram bot token
telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
print(f"Telegram Token: {telegram_token[:20] if telegram_token else 'None'}...")
print(f"Token length: {len(telegram_token) if telegram_token else 0}")

# Check if API token is different
api_token = os.getenv('API_TOKEN')
print(f"API Token: {api_token[:20] if api_token else 'None'}...")
print(f"Tokens are different: {telegram_token != api_token if telegram_token and api_token else 'N/A'}")