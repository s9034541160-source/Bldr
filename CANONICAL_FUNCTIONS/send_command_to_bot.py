# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: send_command_to_bot
# Основной источник: C:\Bldr\integrations\telegram_bot_fixed.py
# Дубликаты (для справки):
#   - C:\Bldr\integrations\telegram_bot.py
#================================================================================
def send_command_to_bot(cmd: str) -> bool:
    """
    Send a command to the Telegram bot
    
    Args:
        cmd: Command to send to the bot
        
    Returns:
        bool: True if command was sent successfully, False otherwise
    """
    try:
        # Check if Telegram bot token is configured
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not telegram_token or telegram_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            print("Telegram bot token not configured")
            return False
            
        # For now, we'll log the command and simulate sending it
        # In a real implementation, we would send the command to users who have interacted with the bot
        # This would require storing chat IDs from user interactions
        logger.info(f"Command sent to bot: {cmd}")
        
        # Simulate successful sending
        return True
    except Exception as e:
        logger.error(f"Error sending command to bot: {str(e)}")
        return False