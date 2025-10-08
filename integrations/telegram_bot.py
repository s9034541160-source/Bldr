#!/usr/bin/env python3
"""
DEPRECATED: Legacy Telegram bot (python-telegram-bot). Do not use.
This file remains only to provide send_file_to_user for CoordinatorAgent.
Use integrations/telegram_bot_aiogram.py to run the bot server.
"""
import os

# Backward-compatible delivery helper
try:
    from integrations.telegram_delivery import send_file_to_user  # re-export for compatibility
except Exception:
    def send_file_to_user(chat_id: int, file_path: str, caption: str = "") -> bool:
        return False

if __name__ == '__main__':
    print("This legacy Telegram bot script has been archived. Use integrations/telegram_bot_aiogram.py instead.")
    if not TELEGRAM_AVAILABLE: return
    await update.message.reply_chat_action(ChatAction.TYPING)
    await update.message.reply_text("🎤 Получил голосовое сообщение. Транскрибирую и анализирую...")
    
    def _send_long(msg: str):
        MAX = 3900
        s = msg or ''
        out = []
        while len(s) > MAX:
            cut = s.rfind('\n', 0, MAX)
            if cut == -1:
                cut = MAX
            out.append(s[:cut])
            s = s[cut:]
        if s:
            out.append(s)
        return out
    try:
        vf = await update.message.voice.get_file()
        vb = await vf.download_as_bytearray()
        v64 = base64.b64encode(vb).decode('utf-8')
        headers = get_auth_headers()
        payload = {
            'message': 'Voice message',
            'context_search': False,
            'max_context': 1,
            'agent_role': 'coordinator',
            'voice_data': v64,
            'request_context': {
                'channel': 'telegram',
                'chat_id': update.message.chat_id,
                'message_id': update.message.message_id,
                'reply_to_message_id': (update.message.reply_to_message.message_id if update.message.reply_to_message else None),
                'user_id': update.message.from_user.id if update.message.from_user else None
            }
        }
        resp = requests.post(f"{API_BASE}/api/ai/chat", json=payload, headers=headers, timeout=1800)
        if resp.status_code in (401, 403):
            headers = get_auth_headers()
            resp = requests.post(f"{API_BASE}/api/ai/chat", json=payload, headers=headers, timeout=1800)
        if resp.status_code == 200:
            response_data = resp.json()
            ai_response = response_data.get('response', '')
            
            if "Whisper not available" in ai_response:
                final_response = "🎤 Голосовое сообщение получено, но система распознавания речи не установлена.\n\nДля работы с голосовыми сообщениями установите Whisper: pip install openai-whisper"
            elif "Audio transcription failed" in ai_response:
                final_response = "🎤 Голосовое сообщение получено, но не удалось распознать речь.\n\nВозможные причины:\n• Низкое качество записи\n• Слишком много шума\n• Неподдерживаемый формат файла\n\nПопробуйте отправить текстовое сообщение."
            else:
                final_response = f"🎤 Голосовое сообщение обработано:\n\n{ai_response}"
            
            for part in _send_long(final_response):
                await update.message.reply_text(part)
        else:
            error_msg = resp.text if resp.text else f"HTTP {resp.status_code}"
            for part in _send_long(f"❌ Ошибка обработки голосового сообщения: {error_msg}"):
                await update.message.reply_text(part)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def handle_photo(update, context):
    if not TELEGRAM_AVAILABLE: return
    await update.message.reply_chat_action(ChatAction.TYPING)
    await update.message.reply_text("📸 Получил фото. Анализирую содержимое...")
    
    def _send_long(msg: str):
        MAX = 3900
        s = msg or ''
        out = []
        while len(s) > MAX:
            cut = s.rfind('\n', 0, MAX)
            if cut == -1:
                cut = MAX
            out.append(s[:cut])
            s = s[cut:]
        if s:
            out.append(s)
        return out
    try:
        p = update.message.photo[-1]
        pf = await p.get_file()
        pb = await pf.download_as_bytearray()
        p64 = base64.b64encode(pb).decode('utf-8')
        caption = update.message.caption or ''
        headers = get_auth_headers()
        prompt = caption or 'Проанализируй это изображение. Выполни OCR и дай выводы по нормативам.'
        payload = {
            'message': prompt,
            'context_search': False,
            'max_context': 1,
            'agent_role': 'coordinator',
            'image_data': p64,
            'request_context': {
                'channel': 'telegram',
                'chat_id': update.message.chat_id,
                'message_id': update.message.message_id,
                'reply_to_message_id': (update.message.reply_to_message.message_id if update.message.reply_to_message else None),
                'user_id': update.message.from_user.id if update.message.from_user else None
            }
        }
        resp = requests.post(f"{API_BASE}/api/ai/chat", json=payload, headers=headers, timeout=1800)
        if resp.status_code in (401, 403):
            headers = get_auth_headers()
            resp = requests.post(f"{API_BASE}/api/ai/chat", json=payload, headers=headers, timeout=1800)
        if resp.status_code == 200:
            response_data = resp.json()
            ai_response = response_data.get('response', '')
            
            if "обработка временно недоступна" in ai_response:
                final_response = "📸 Фото получено, но система анализа изображений не настроена.\n\nДля работы с изображениями установите необходимые библиотеки: pip install opencv-python pytesseract pillow"
            elif "Ошибка анализа изображения" in ai_response:
                final_response = "📸 Фото получено, но не удалось проанализировать изображение.\n\nВозможные причины:\n• Неподдерживаемый формат файла\n• Поврежденное изображение\n• Отсутствуют необходимые библиотеки\n\nПопробуйте отправить другое изображение."
            else:
                final_response = f"📸 Фото обработано:\n\n{ai_response}"
            
            for part in _send_long(final_response):
                await update.message.reply_text(part)
        else:
            error_msg = resp.text if resp.text else f"HTTP {resp.status_code}"
            for part in _send_long(f"❌ Ошибка обработки изображения: {error_msg}"):
                await update.message.reply_text(part)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def handle_document(update, context):
    if not TELEGRAM_AVAILABLE: return
    await update.message.reply_chat_action(ChatAction.TYPING)
    
    def _send_long(msg: str):
        MAX = 3900
        s = msg or ''
        out = []
        while len(s) > MAX:
            cut = s.rfind('\n', 0, MAX)
            if cut == -1:
                cut = MAX
            out.append(s[:cut])
            s = s[cut:]
        if s:
            out.append(s)
        return out
    try:
        d = update.message.document
        fn = d.file_name
        fs = d.file_size
        if fs > 20 * 1024 * 1024:
            await update.message.reply_text("❌ Файл слишком большой. Максимальный размер 20MB.")
            return
        df = await d.get_file()
        db = await df.download_as_bytearray()
        d64 = base64.b64encode(db).decode('utf-8')
        headers = get_auth_headers()
        prompt = f'Проанализируй файл "{fn}". Извлеки ключевые сведения и соответствие нормам.'
        # If the document is actually an image, route as image_data to preserve original quality
        lower_fn = (fn or '').lower()
        is_image = any(lower_fn.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'])
        payload = {
            'message': prompt,
            'context_search': True,
            'max_context': 3,
            'agent_role': 'coordinator',
            ('image_data' if is_image else 'document_data'): d64,
            'document_name': fn,
            'request_context': {
                'channel': 'telegram',
                'chat_id': update.message.chat_id,
                'message_id': update.message.message_id,
                'reply_to_message_id': (update.message.reply_to_message.message_id if update.message.reply_to_message else None),
                'user_id': update.message.from_user.id if update.message.from_user else None
            }
        }
        resp = requests.post(f"{API_BASE}/api/ai/chat", json=payload, headers=headers, timeout=1800)
        if resp.status_code in (401, 403):
            headers = get_auth_headers()
            resp = requests.post(f"{API_BASE}/api/ai/chat", json=payload, headers=headers, timeout=1800)
        if resp.status_code == 200:
            text = resp.json().get('response') or 'Нет ответа'
            for part in _send_long(text):
                await update.message.reply_text(part)
        else:
            for part in _send_long(f"Doc error: {resp.text}"):
                await update.message.reply_text(part)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

if __name__ == '__main__':
    if TELEGRAM_AVAILABLE and TELEGRAM_BOT_TOKEN != 'YOUR_TELEGRAM_BOT_TOKEN_HERE':
        logger.info(f"[TG] Starting bot with token: {TELEGRAM_BOT_TOKEN[:10]}...")
        logger.info(f"[TG] API_BASE: {API_BASE}")
        logger.info(f"[TG] API_USER: {API_USER}")
        
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).defaults(Defaults(quote=True)).build()
        application = app
        
        # Global debug logger for all updates (diagnostics) - highest priority
        app.add_handler(MessageHandler(filters.ALL, debug_log_update), group=1)
        
        # Command handlers
        app.add_handler(CommandHandler('start', start_command), group=0)
        app.add_handler(CommandHandler('metrics', metrics_command), group=0)
        
        # Message handlers - order matters!
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text), group=0)
        app.add_handler(MessageHandler(filters.VOICE, handle_voice), group=0)
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo), group=0)
        app.add_handler(MessageHandler(filters.Document.ALL, handle_document), group=0)
        
        logger.info("[TG] All handlers registered, starting polling...")
        logger.info(f"[TG] Debug handler registered in group 1")
        logger.info(f"[TG] Text handler registered in group 0")
        logger.info(f"[TG] Bot token: {TELEGRAM_BOT_TOKEN[:10]}...")
        logger.info(f"[TG] Starting polling with debug logging...")
        app.run_polling()
    else:
        print("Telegram bot token not configured or libraries missing.")
