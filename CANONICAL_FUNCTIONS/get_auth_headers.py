# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: get_auth_headers
# Основной источник: C:\Bldr\integrations\telegram_bot_fixed.py
# Дубликаты (для справки):
#   - C:\Bldr\monitor_training.py
#   - C:\Bldr\integrations\telegram_bot.py
#   - C:\Bldr\integrations\telegram_bot_improved.py
#================================================================================
def get_auth_headers():
    """Get authentication headers for API calls"""
    headers = {
        "Content-Type": "application/json"
    }
    if API_TOKEN:
        headers['Authorization'] = f'Bearer {API_TOKEN}'
    return headers