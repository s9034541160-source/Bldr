#!/usr/bin/env python3
"""
Improved Telegram Bot for Bldr Empire v2
Fixed version with better error handling and user feedback
"""

import os
import base64
import logging
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import Telegram libraries
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
    from telegram.constants import ChatAction
    TELEGRAM_AVAILABLE = True
except ImportError:
    print("Warning: Telegram libraries not available")
    TELEGRAM_AVAILABLE = False

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN_HERE')
API_BASE = 'http://localhost:8000'
API_TOKEN = os.getenv('API_TOKEN')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_auth_headers():
    """Get authentication headers for API calls"""
    headers = {"Content-Type": "application/json"}
    if API_TOKEN:
        headers['Authorization'] = f'Bearer {API_TOKEN}'
    return headers

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages with improved error handling"""
    if not TELEGRAM_AVAILABLE:
        return
    
    await update.message.reply_chat_action(ChatAction.TYPING)
    
    try:
        # Download voice file
        voice_file = await update.message.voice.get_file()
        voice_bytes = await voice_file.download_as_bytearray()
        voice_base64 = base64.b64encode(voice_bytes).decode('utf-8')
        
        await update.message.reply_text("🎤 Получил голосовое сообщение. Транскрибирую и анализирую...")
        
        # Send to API
        headers = get_auth_headers()
        chat_payload = {
            'message': 'Voice message',
            'context_search': False,
            'max_context': 1,
            'agent_role': 'coordinator',
            'voice_data': voice_base64,
            'request_context': {
                'channel': 'telegram',
                'chat_id': update.message.chat_id,
                'user_id': update.message.from_user.id if update.message.from_user else None
            }
        }
        
        resp = requests.post(f'{API_BASE}/api/ai/chat', json=chat_payload, headers=headers, timeout=1800)
        
        if resp.status_code == 200:
            response_data = resp.json()
            ai_response = response_data.get('response', '')
            
            # Check for specific error messages
            if "Whisper not available" in ai_response:
                final_response = "🎤 Голосовое сообщение получено, но система распознавания речи не установлена.\n\nДля работы с голосовыми сообщениями установите Whisper:\n```bash\npip install openai-whisper\n```"
            elif "Audio transcription failed" in ai_response:
                final_response = "🎤 Голосовое сообщение получено, но не удалось распознать речь.\n\nВозможные причины:\n• Низкое качество записи\n• Слишком много шума\n• Неподдерживаемый формат файла\n\nПопробуйте отправить текстовое сообщение."
            else:
                final_response = f"🎤 Голосовое сообщение обработано:\n\n{ai_response}"
            
            await update.message.reply_text(final_response, parse_mode="Markdown")
        else:
            error_msg = resp.text if resp.text else f"HTTP {resp.status_code}"
            await update.message.reply_text(f"❌ Ошибка обработки голосового сообщения: {error_msg}")
            
    except Exception as e:
        logger.error(f"Error processing voice message: {str(e)}")
        await update.message.reply_text(
            f"❌ Ошибка обработки голосового сообщения: {str(e)}\n\n"
            "Возможные решения:\n"
            "• Проверьте, запущен ли API сервис\n"
            "• Убедитесь, что установлены необходимые зависимости\n"
            "• Попробуйте отправить текстовое сообщение вместо голосового"
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages with improved error handling"""
    if not TELEGRAM_AVAILABLE:
        return
    
    await update.message.reply_chat_action(ChatAction.TYPING)
    
    try:
        # Download photo
        photo = update.message.photo[-1]
        file = await photo.get_file()
        photo_bytes = await file.download_as_bytearray()
        photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
        
        # Get caption
        caption = update.message.caption or ""
        await update.message.reply_text("📸 Получил фото. Анализирую содержимое...")
        
        # Prepare prompt
        if caption:
            prompt = f'Проанализируй это фото с учетом комментария: "{caption}". Извлеки ключевую информацию и найди соответствующие строительные нормы.'
        else:
            prompt = 'Проанализируй это фото. Определи конструктивные элементы, материалы, состояние. Проверь соответствие строительным нормам.'
        
        # Send to API
        headers = get_auth_headers()
        chat_payload = {
            'message': prompt,
            'context_search': True,
            'max_context': 3,
            'agent_role': 'coordinator',
            'image_data': photo_base64,
            'request_context': {
                'channel': 'telegram',
                'chat_id': update.message.chat_id,
                'user_id': update.message.from_user.id if update.message.from_user else None
            }
        }
        
        resp = requests.post(f'{API_BASE}/api/ai/chat', json=chat_payload, headers=headers, timeout=1800)
        
        if resp.status_code == 200:
            response_data = resp.json()
            ai_response = response_data.get('response', '')
            
            # Check for specific error messages
            if "обработка временно недоступна" in ai_response:
                final_response = "📸 Фото получено, но система анализа изображений не настроена.\n\nДля работы с изображениями установите необходимые библиотеки:\n```bash\npip install opencv-python pytesseract pillow\n```"
            elif "Ошибка анализа изображения" in ai_response:
                final_response = "📸 Фото получено, но не удалось проанализировать изображение.\n\nВозможные причины:\n• Неподдерживаемый формат файла\n• Поврежденное изображение\n• Отсутствуют необходимые библиотеки\n\nПопробуйте отправить другое изображение."
            else:
                final_response = f"📸 Фото обработано:\n\n{ai_response}"
            
            await update.message.reply_text(final_response, parse_mode="Markdown")
        else:
            error_msg = resp.text if resp.text else f"HTTP {resp.status_code}"
            await update.message.reply_text(f"❌ Ошибка обработки изображения: {error_msg}")
            
    except Exception as e:
        logger.error(f"Error processing photo: {str(e)}")
        await update.message.reply_text(
            f"❌ Ошибка обработки изображения: {str(e)}\n\n"
            "Возможные решения:\n"
            "• Проверьте, запущен ли API сервис\n"
            "• Убедитесь, что установлены необходимые зависимости\n"
            "• Попробуйте отправить другое изображение"
        )

# Rest of the bot implementation would go here...
# (Keeping it minimal for this example)

if __name__ == '__main__':
    if TELEGRAM_BOT_TOKEN == 'YOUR_TELEGRAM_BOT_TOKEN_HERE':
        print("Please set TELEGRAM_BOT_TOKEN environment variable")
        exit(1)
    
    print("Telegram bot improved version ready!")
    print("This is a fixed version with better error handling")