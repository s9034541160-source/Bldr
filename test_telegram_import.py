try:
    from telegram import Update
    print('Telegram libraries available')
except ImportError as e:
    print(f'Telegram libraries not available: {e}')