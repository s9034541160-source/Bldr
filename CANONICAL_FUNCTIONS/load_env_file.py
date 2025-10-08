# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: load_env_file
# Основной источник: C:\Bldr\integrations\telegram_bot_fixed.py
# Дубликаты (для справки):
#   - C:\Bldr\integrations\telegram_bot.py
#================================================================================
def load_env_file():
    """Load environment variables from .env file"""
    env_file_path = '.env'
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    # Remove any surrounding quotes from the value
                    value = value.strip().strip('"\'')
                    os.environ[key] = value