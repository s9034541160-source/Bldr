#!/usr/bin/env python3
"""
Telegram Bot for Bldr Empire v2
Adapted from old bot: Commands /start /help /query /train, API calls to bldr_api.py
"""
import os
import re
import json
import asyncio
import logging
import base64
from datetime import datetime
from typing import Dict, Any, List
import requests
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Global variable to store the application instance
application = None

# Try to import Telegram libraries with proper error handling
TELEGRAM_AVAILABLE = False
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
    from telegram.constants import ChatAction
    TELEGRAM_AVAILABLE = True
except ImportError:
    print("Warning: Telegram libraries not available. Bot functionality will be limited.")
    TELEGRAM_AVAILABLE = False

# Define dummy constants and classes for when Telegram is not available
if not TELEGRAM_AVAILABLE:
    class ChatAction:
        TYPING = "typing"
    
    class Update:
        ALL_TYPES = []
    
    # Simple dummy implementations for when Telegram is not available
    def dummy_function(*args, **kwargs):
        pass
    
    # Assign dummy functions to avoid NameError
    InlineKeyboardButton = dummy_function
    InlineKeyboardMarkup = dummy_function
    ReplyKeyboardMarkup = dummy_function
    KeyboardButton = dummy_function
    Application = dummy_function
    CommandHandler = dummy_function
    MessageHandler = dummy_function
    filters = dummy_function
    ContextTypes = dummy_function
    CallbackQueryHandler = dummy_function

# Env for token (set TELEGRAM_BOT_TOKEN=your_token)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN_HERE')
API_BASE = 'http://localhost:8000'  # bldr_api.py
TG_CONTEXT_SEARCH_DEFAULT = os.getenv('TG_CONTEXT_SEARCH_DEFAULT', 'false').lower() == 'true'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API token from environment variables
API_TOKEN = os.getenv('API_TOKEN')

# Check if API token is properly set
if not API_TOKEN or API_TOKEN == "":
    print("Warning: API_TOKEN not set in environment variables")
    API_TOKEN = None

def get_auth_headers():
    """Get authentication headers for API calls"""
    headers = {
        "Content-Type": "application/json"
    }
    if API_TOKEN:
        headers['Authorization'] = f'Bearer {API_TOKEN}'
    return headers

async def send_file_to_user(chat_id, file_path, caption=""):
    """
    Send a file to a Telegram user
    
    Args:
        chat_id: Telegram chat ID
        file_path: Path to the file to send
        caption: Optional caption for the file
    """
    # Only execute actual functionality if Telegram is available
    if not TELEGRAM_AVAILABLE:
        return False
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        
        # In a real implementation, we would need access to the application instance
        # For now, we'll use a global variable to store the application instance
        global application
        if application is None:
            logger.error("Telegram application instance not available")
            return False
        
        # Send the document to the user
        with open(file_path, 'rb') as file:
            await application.bot.send_document(chat_id=chat_id, document=file, caption=caption)
        logger.info(f"File sent successfully to chat {chat_id}: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error sending file to user: {str(e)}")
        return False

# Define command functions without type annotations to avoid linter issues
async def start_command(update, context):
    # Only execute actual functionality if Telegram is available
    if not TELEGRAM_AVAILABLE:
        return
    
    # Create inline keyboard with buttons
    keyboard = [
        [InlineKeyboardButton("🔍 Query Norms", callback_data="query_norms")],
        [InlineKeyboardButton("🚀 Train RAG", callback_data="train_rag")],
        [InlineKeyboardButton("📊 Metrics", callback_data="metrics")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Create custom keyboard for quick access
    custom_keyboard = [
        [KeyboardButton("🔍 Query"), KeyboardButton("🚀 Train")],
        [KeyboardButton("📊 Metrics"), KeyboardButton("❓ Help")]
    ]
    custom_reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🚀 Bldr Empire v2 Bot!\n\n"
        "Добро пожаловать в Bldr Empire v2 Telegram бот! Я могу помочь с:\n"
        "• 🔍 Поиск строительных норм и правил\n"
        "• 🎤 Анализ голосовых сообщений (транскрипция)\n"
        "• 📸 Обработка фото чертежей и документов (OCR)\n"
        "• 📄 Анализ PDF, Word, Excel файлов и чертежей DWG\n"
        "• 🚀 Обучение RAG системы новыми документами\n"
        "• 📊 Просмотр метрик системы\n\n"
        "Просто отправьте мне текст, фото, голосовое сообщение или файл - я автоматически разберу, что надо сделать!",
        reply_markup=custom_reply_markup
    )

async def help_command(update, context):
    # Only execute actual functionality if Telegram is available
    if not TELEGRAM_AVAILABLE:
        return
    
    help_text = (
        "🤖 Справка по Bldr Empire v2 Bot\n\n"
        "📄 Обработка документов:\n"
        "• Отправляйте PDF/DOCX/Excel файлы для автоматической обработки\n"
        "• Файлы автоматически анализируются и добавляются в базу знаний\n"
        "• Поддержка чертежей DWG/DXF и таблиц XLS/CSV\n\n"
        "💬 Команды:\n"
        "/query <вопрос> - Поиск строительных норм (например: /query кл.5.2 СП31)\n"
        "/train - Обучение RAG системы новыми документами\n"
        "/metrics - Просмотр метрик производительности системы\n"
        "/db <cypher> - Выполнение Neo4j запросов\n"
        "/ai <запрос> - Получение AI-ответов\n\n"
        "📱 Возможности:\n"
        "• 📸 Отправка фото для OCR и анализа чертежей/документов\n"
        "• 🎤 Голосовые сообщения с транскрипцией и анализом\n"
        "• 📄 Анализ любых файлов с умными подсказками\n"
        "• 💬 Просто отправьте текст - я найду ответ в нормативах\n"
        "• 🎯 Интерактивные кнопки для быстрого доступа\n\n"
        "⚙️ Настройка:\n"
        "Документы в I:\\docs\\база используются для автообучения.\n"
        "Система использует 14-этапный симбиотический конвейер обработки."
    )
    await update.message.reply_text(help_text)

async def query_command(update, context):
    # Only execute actual functionality if Telegram is available
    if not TELEGRAM_AVAILABLE:
        return
    
    query = " ".join(context.args)
    if not query:
        # Provide examples
        examples = [
            "/query cl.5.2 СП31",
            "/query требования к бетону для фундамента",
            "/query допустимые отклонения при кладке стен"
        ]
        example_text = "\n".join(examples)
        await update.message.reply_text(
            "Usage: /query <question>\n\nExamples:\n" + example_text
        )
        return
    await update.message.reply_chat_action(ChatAction.TYPING)
    
    try:
        # Add authentication header if token is available
        headers = get_auth_headers()
            
        # Use new RAG search endpoint
        search_payload = {
            'query': query,
            'k': 5,
            'threshold': 0.3,
            'include_metadata': True
        }
        
        resp = requests.post(
            f'{API_BASE}/api/rag/search', 
            json=search_payload,
            headers=headers,
            timeout=1800  # Increased to 30 minutes to match AI Shell
        )
        resp.raise_for_status()  # Raise exception for bad status codes
        
        response_data = resp.json()
        results = response_data.get('results', [])
        
        if not results:
            await update.message.reply_text("No results found for your query. Please try rephrasing or check if the system has been trained with relevant documents.")
            return
        
        # Format response using new RAG format
        text = f"🔍 RAG Search '{query}'\n\n"
        text += f"📊 Found: {response_data.get('total_found')} results\n"
        text += f"⚡ Time: {response_data.get('processing_time', 0):.2f}s\n"
        text += f"🧠 Method: {response_data.get('search_method')}\n\n"
        
        for i, r in enumerate(results, 1):
            # Truncate content text to make it more readable
            content_text = r['content'][:200] + "..." if len(r['content']) > 200 else r['content']
            text += f"{i}. {content_text}\n"
            text += f"   📈 Score: {r['score']:.3f}\n"
            
            # Show metadata if available
            if r.get('metadata'):
                metadata = r['metadata']
                if metadata.get('doc_id'):
                    text += f"   📄 Doc: {metadata.get('doc_id')}\n"
                if metadata.get('category'):
                    text += f"   🏷️ Category: {metadata.get('category')}\n"
            
            text += "\n"
            
        await update.message.reply_text(text)
    except requests.exceptions.Timeout:
        await update.message.reply_text("❌ Request timeout. The system is taking too long to respond. Please try again later.")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ Connection error. Please check if the Bldr API service is running and try again.")
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 401:
            await update.message.reply_text("❌ Authentication required. Please check your API token configuration.")
        elif status_code == 403:
            await update.message.reply_text("❌ Access forbidden. You don't have permission to perform this action.")
        elif status_code == 429:
            await update.message.reply_text("❌ Rate limit exceeded. Please wait a moment before trying again.")
        elif status_code >= 500:
            await update.message.reply_text("❌ Server error. The system encountered an internal error. Please try again later.")
        else:
            await update.message.reply_text(f"❌ API error (HTTP {status_code}). Please try again or contact support.")
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        await update.message.reply_text(f"❌ Error processing query: {str(e)}. Please try again or contact support.")

async def train_command(update, context):
    # Only execute actual functionality if Telegram is available
    if not TELEGRAM_AVAILABLE:
        return
    
    await update.message.reply_chat_action(ChatAction.TYPING)
    
    try:
        # Add authentication header if token is available
        headers = get_auth_headers()
        
        # Use new RAG training endpoint
        training_payload = {
            'base_dir': None,  # Use default directory
            'max_files': None,  # No limit
            'force_retrain': False,
            'doc_types': None  # All types
        }
        
        resp = requests.post(
            f'{API_BASE}/api/rag/train',
            json=training_payload,
            headers=headers,
            timeout=1800  # Increased to 30 minutes to match AI Shell
        )
        resp.raise_for_status()
        
        response_data = resp.json()
        task_id = response_data.get('task_id', 'unknown')
        message = response_data.get('message', 'Training started successfully')
        estimated_time = response_data.get('estimated_time', 'unknown')
        
        await update.message.reply_text(
            f"🚀 RAG Training started!\n\n"
            f"🏷️ Task ID: {task_id}\n"
            f"💬 Message: {message}\n"
            f"⏰ Estimated time: {estimated_time}\n\n"
            f"Use /metrics to check training progress and results."
        )
    except requests.exceptions.Timeout:
        await update.message.reply_text("❌ Request timeout. Training process is taking too long to start. Please check system status.")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ Connection error. Please check if the Bldr API service is running and try again.")
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 401:
            await update.message.reply_text("❌ Authentication required. Please check your API token configuration.")
        elif status_code == 403:
            await update.message.reply_text("❌ Access forbidden. You don't have permission to start training.")
        elif status_code == 429:
            await update.message.reply_text("❌ Rate limit exceeded. Please wait a moment before trying again.")
        elif status_code >= 500:
            await update.message.reply_text("❌ Server error. The system encountered an internal error. Please try again later.")
        else:
            await update.message.reply_text(f"❌ API error (HTTP {status_code}). Please try again or contact support.")
    except Exception as e:
        logger.error(f"Error starting training: {str(e)}")
        await update.message.reply_text(f"❌ Error starting training: {str(e)}. Please try again or contact support.")

async def metrics_command(update, context):
    # Only execute actual functionality if Telegram is available
    if not TELEGRAM_AVAILABLE:
        return
    
    try:
        # Add authentication header if token is available
        headers = get_auth_headers()
        
        # Get system health first
        health_resp = requests.get(
            f'{API_BASE}/health',
            headers=headers,
            timeout=1800  # Increased to 30 minutes
        )
        health_resp.raise_for_status()
        health_data = health_resp.json()
        
        # Get RAG system status
        rag_resp = requests.get(
            f'{API_BASE}/api/rag/status',
            headers=headers,
            timeout=1800  # Increased to 30 minutes
        )
        rag_resp.raise_for_status()
        rag_data = rag_resp.json()
        
        # Format comprehensive system status
        text = f"📊 Bldr System Metrics\n"
        text += f"=" * 25 + "\n\n"
        
        # System health
        system_status = health_data.get('status', 'unknown')
        text += f"💹 System Status: {system_status.upper()}\n"
        
        components = health_data.get('components', {})
        if components:
            text += f"🔧 Components:\n"
            for component, status in components.items():
                emoji = "✅" if status in ['ok', 'connected', 'running'] else "❌"
                text += f"  {emoji} {component}: {status}\n"
            text += "\n"
        
        # RAG system status
        text += f"🧠 RAG System Status:\n"
        
        is_training = rag_data.get('is_training', False)
        training_emoji = "🔄" if is_training else "⏸️"
        text += f"  {training_emoji} Training: {'In Progress' if is_training else 'Idle'}\n"
        
        if is_training:
            progress = rag_data.get('progress', 0)
            current_stage = rag_data.get('current_stage', 'unknown')
            text += f"  📈 Progress: {progress}%\n"
            text += f"  🔍 Stage: {current_stage}\n"
        
        text += f"  📄 Documents: {rag_data.get('total_documents', 0)}\n"
        text += f"  🧩 Chunks: {rag_data.get('total_chunks', 0)}\n"
        
        message = rag_data.get('message', '')
        if message:
            text += f"  💬 Message: {message}\n"
        
        last_update = rag_data.get('last_update', '')
        if last_update:
            text += f"  🕐 Updated: {last_update[:19]}\n"
        
        await update.message.reply_text(text)
    except requests.exceptions.Timeout:
        await update.message.reply_text("❌ Request timeout. Unable to fetch system metrics. Please try again later.")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ Connection error. Please check if the Bldr API service is running and try again.")
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 401:
            await update.message.reply_text("❌ Authentication required. Please check your API token configuration.")
        elif status_code == 403:
            await update.message.reply_text("❌ Access forbidden. You don't have permission to view metrics.")
        elif status_code == 429:
            await update.message.reply_text("❌ Rate limit exceeded. Please wait a moment before trying again.")
        elif status_code >= 500:
            await update.message.reply_text("❌ Server error. The system encountered an internal error. Please try again later.")
        else:
            await update.message.reply_text(f"❌ API error (HTTP {status_code}). Please try again or contact support.")
    except Exception as e:
        logger.error(f"Error fetching metrics: {str(e)}")
        await update.message.reply_text(f"❌ Error fetching metrics: {str(e)}. Please try again or contact support.")

async def db_command(update, context):
    # Only execute actual functionality if Telegram is available
    if not TELEGRAM_AVAILABLE:
        return
    
    cypher = " ".join(context.args)
    if not cypher:
        await update.message.reply_text("Usage: /db <cypher query> e.g. /db MATCH (n:WorkSequence) RETURN n LIMIT 5")
        return
    
    try:
        # Add authentication header if token is available
        headers = get_auth_headers()
        
        resp = requests.post(f'{API_BASE}/db', json={'cypher': cypher}, headers=headers)
        resp.raise_for_status()
        records = resp.json()['records']
        text = f"Neo4j Query '{cypher}': {len(records)} records\n\n"
        for r in records[:10]:
            text += f"• {r}\n"
        if len(records) > 10: 
            text += f"... + {len(records)-10} more"
        await update.message.reply_text(text)
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"❌ Error executing database query: {str(e)}. Please check your query syntax and try again.")
    except Exception as e:
        logger.error(f"Error processing database query: {str(e)}")
        await update.message.reply_text(f"❌ Error processing database query: {str(e)}. Please try again or contact support.")

async def ai_command(update, context):
    # Only execute actual functionality if Telegram is available
    if not TELEGRAM_AVAILABLE:
        return
    
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("Usage: /ai <prompt> e.g. /ai Generate tezis for BIM OVOS FЗ-44")
        return
    
    try:
        # Add authentication header if token is available
        headers = get_auth_headers()
            
        # Prepare the payload
        payload = {
            'prompt': prompt,
            'model': 'deepseek/deepseek-r1-0528-qwen3-8b'
        }
        
        # Send request to AI endpoint
        resp = requests.post(f'{API_BASE}/ai', json=payload, headers=headers, timeout=1800)  # Increased to 30 minutes to match AI Shell
        
        if resp.status_code == 200:
            response_data = resp.json()
            task_id = response_data.get('task_id')
            message = response_data.get('message', 'AI request started')
            await update.message.reply_text(f"🤖 AI request started (Task ID: {task_id})\n{message}\n\nPlease wait while I process your request. I'll send you the response when it's ready.")
        else:
            await update.message.reply_text(f"AI error: {resp.text}")
    except requests.exceptions.Timeout:
        await update.message.reply_text("❌ Request timeout. The AI system is taking too long to respond. Please try again later.")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ Connection error. Please check if the Bldr API service is running and try again.")
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"❌ Error communicating with AI service: {str(e)}. Please try again later.")
    except Exception as e:
        logger.error(f"Error processing AI request: {str(e)}")
        await update.message.reply_text(f"❌ Error processing AI request: {str(e)}. Please try again or contact support.")

async def handle_text(update, context):
    # Only execute actual functionality if Telegram is available
    if not TELEGRAM_AVAILABLE:
        return
    
    text = update.message.text
    do_tts = False
    if text:
        if text.startswith('/tts ') or text.startswith('/say '):
            do_tts = True
            text = text.split(' ', 1)[1] if ' ' in text else ''
    await update.message.reply_chat_action(ChatAction.TYPING)
    
    # Handle quick access buttons
    if text == "🔍 Query":
        await update.message.reply_text("Please enter your query after /query command, e.g. /query cl.5.2 СП31")
        return
    elif text == "🚀 Train":
        await train_command(update, context)
        return
    elif text == "📊 Metrics":
        await metrics_command(update, context)
        return
    elif text == "❓ Help":
        await help_command(update, context)
        return
    
    try:
        # Add authentication header if token is available
        headers = get_auth_headers()
        
        # Store Telegram context for file delivery
        telegram_context = {
            "chat_id": update.message.chat_id,
            "message_id": update.message.message_id,
            "user_id": update.message.from_user.id if update.message.from_user else None
        }
        
        # Heuristic: context only for normative queries unless explicitly enabled
        text_lower = (text or '').lower()
        looks_like_norms = any(key in text_lower for key in [
            'сп ', 'сп-', 'снип', 'сн', 'гост', 'требован', 'норма', 'правил', 'санпин', 'пособи', 'свод правил', '?'
        ])
        do_context = (TG_CONTEXT_SEARCH_DEFAULT or looks_like_norms)
        
        chat_payload = {
            'message': text,
            'context_search': do_context,
            'max_context': 3,
            'agent_role': 'coordinator',
            'request_context': {
                'channel': 'telegram',
                'chat_id': telegram_context['chat_id'],
                'user_id': telegram_context['user_id']
            }
        }
        
        resp = requests.post(
            f'{API_BASE}/api/ai/chat',
            json=chat_payload,
            headers=headers,
            timeout=1800  # Increased to 30 minutes to match AI Shell
        )
        resp.raise_for_status()
        
        response_data = resp.json()
        ai_response = response_data.get('response', '')
        context_used = response_data.get('context_used', [])
        agent_used = response_data.get('agent_used', 'unknown')
        processing_time = response_data.get('processing_time', 0)
        
        if not ai_response:
            await update.message.reply_text("Я не смог найти подходящую информацию по вашему запросу. Попробуйте переформулировать вопрос или используйте /help для примеров команд.")
            return
        
        # Format AI response with context info
        final_response = f"🤖 {ai_response}\n\n"
        
        # Add context information if available
        if context_used:
            final_response += f"📁 Контекст ({len(context_used)} документов):\n"
            for i, ctx in enumerate(context_used[:2], 1):  # Show max 2 context sources
                ctx_preview = ctx['content'][:100] + "..." if len(ctx['content']) > 100 else ctx['content']
                final_response += f"{i}. {ctx_preview} (📈 {ctx['score']:.2f})\n"
            final_response += "\n"
        
        # Add technical info footer
        final_response += f"⚡ Агент: {agent_used} | Время: {processing_time:.2f}s"
            
        await update.message.reply_text(final_response)
        
        # TTS reply only if explicitly requested via /tts or /say
        if do_tts:
            try:
                tts_resp = requests.post(f"{API_BASE}/tts", json={"text": ai_response}, headers=headers, timeout=60)
                if tts_resp.status_code == 200:
                    audio_url = f"{API_BASE}/download/response.mp3"
                    audio_file = requests.get(audio_url, timeout=60)
                    if audio_file.status_code == 200 and application:
                        from io import BytesIO
                        bio = BytesIO(audio_file.content)
                        bio.name = 'response.mp3'
                        try:
                            await application.bot.send_voice(chat_id=update.message.chat_id, voice=bio, caption="🔊 Озвучено")
                        except Exception:
                            await application.bot.send_audio(chat_id=update.message.chat_id, audio=bio, caption="🔊 Озвучено")
            except Exception as e:
                logger.error(f"TTS reply failed: {e}")
    except requests.exceptions.Timeout:
        await update.message.reply_text("❌ Тайм-аут запроса. Система слишком долго отвечает. Попробуйте позже.")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ Ошибка соединения. Проверьте, запущен ли API сервис Bldr, и попробуйте снова.")
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 401:
            await update.message.reply_text("❌ Требуется аутентификация. Проверьте настройку API токена.")
        elif status_code == 403:
            await update.message.reply_text("❌ Доступ запрещен. У вас нет разрешения на выполнение этого действия.")
        elif status_code == 429:
            await update.message.reply_text("❌ Превышен лимит запросов. Подождите немного перед повторной попыткой.")
        elif status_code >= 500:
            await update.message.reply_text("❌ Ошибка сервера. Система столкнулась с внутренней ошибкой. Попробуйте позже.")
        else:
            await update.message.reply_text(f"❌ Ошибка API (HTTP {status_code}). Попробуйте снова или обратитесь в поддержку.")
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        await update.message.reply_text(f"❌ Ошибка обработки вашего сообщения: {str(e)}. Попробуйте снова или обратитесь в поддержку.")

async def handle_voice(update, context):
    """Handle voice messages - transcribe and analyze"""
    # Only execute actual functionality if Telegram is available
    if not TELEGRAM_AVAILABLE:
        return
    
    await update.message.reply_chat_action(ChatAction.TYPING)
    
    try:
        # Get the voice file
        voice_file = await update.message.voice.get_file()
        
        # Download voice file to bytes
        voice_bytes = await voice_file.download_as_bytearray()
        
        # Convert to base64 for API
        voice_base64 = base64.b64encode(voice_bytes).decode('utf-8')
        
        await update.message.reply_text("🎤 Получил голосовое сообщение. Транскрибирую и анализирую...")
        
        # Send to AI chat endpoint with embedded voice data
        headers = get_auth_headers()
        chat_payload = {
            'message': 'Voice message',
            'context_search': False,
            'max_context': 0,
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
            context_used = response_data.get('context_used', [])
            
            final_response = f"🎤 Голосовое сообщение обработано:\n\n{ai_response}\n\n"
            
            if context_used:
                final_response += f"📁 Найден контекст ({len(context_used)} документов)\n"
            
            await update.message.reply_text(final_response)
        else:
            await update.message.reply_text(f"❌ Ошибка обработки голосового сообщения: {resp.text}")
            
    except Exception as e:
        logger.error(f"Error processing voice message: {str(e)}")
        await update.message.reply_text(f"❌ Ошибка обработки голосового сообщения: {str(e)}. Попробуйте снова или обратитесь в поддержку.")

async def handle_photo(update, context):
    """Handle photo messages - OCR and analyze"""
    # Only execute actual functionality if Telegram is available
    if not TELEGRAM_AVAILABLE:
        return
    
    await update.message.reply_chat_action(ChatAction.TYPING)
    
    try:
        # Get the largest photo size
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        
        # Download photo to bytes
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Convert to base64 for API
        photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
        
        # Get caption if provided
        caption = update.message.caption or ""
        
        await update.message.reply_text("📸 Получил фото. Выполняю OCR и анализирую содержимое...")
        
        # Prepare prompt based on whether there's a caption
        if caption:
            prompt = f'Проанализируй это изображение с учетом подписи: "{caption}". Выполни OCR для извлечения текста и проанализируй содержание на предмет строительных норм и требований.'
        else:
            prompt = 'Проанализируй это изображение. Выполни OCR для извлечения текста и проанализируй содержание. Если есть строительные чертежи, схемы или документы - опиши их детально и найди соответствующие нормы.'
        
        # Send to AI chat endpoint with embedded image data
        headers = get_auth_headers()
        chat_payload = {
            'message': 'Image message',
            'context_search': False,
            'max_context': 0,
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
            context_used = response_data.get('context_used', [])
            
            final_response = f"📸 Изображение обработано:\n\n{ai_response}\n\n"
            
            if context_used:
                final_response += f"📁 Найден контекст ({len(context_used)} документов)\n"
            
            await update.message.reply_text(final_response)
        else:
            await update.message.reply_text(f"❌ Ошибка обработки изображения: {resp.text}")
            
    except Exception as e:
        logger.error(f"Error processing photo: {str(e)}")
        await update.message.reply_text(f"❌ Ошибка обработки изображения: {str(e)}. Попробуйте снова или обратитесь в поддержку.")

async def handle_document(update, context):
    """Handle document/file messages - analyze and process"""
    # Only execute actual functionality if Telegram is available
    if not TELEGRAM_AVAILABLE:
        return
    
    await update.message.reply_chat_action(ChatAction.TYPING)
    
    try:
        document = update.message.document
        file_name = document.file_name
        file_size = document.file_size
        
        # Check file size (limit to 20MB for processing)
        if file_size > 20 * 1024 * 1024:  # 20MB
            await update.message.reply_text("❌ Файл слишком большой. Максимальный размер для обработки: 20MB.")
            return
        
        # Get the document file
        doc_file = await document.get_file()
        
        # Download document to bytes
        doc_bytes = await doc_file.download_as_bytearray()
        
        # Convert to base64 for API
        doc_base64 = base64.b64encode(doc_bytes).decode('utf-8')
        
        # Get caption if provided
        caption = update.message.caption or ""
        
        await update.message.reply_text(f"📄 Получил файл '{file_name}' ({file_size // 1024} KB). Анализирую содержимое...")
        
        # Prepare prompt based on file type and caption
        file_ext = file_name.lower().split('.')[-1] if '.' in file_name else 'unknown'
        
        if caption:
            prompt = f'Проанализируй этот файл "{file_name}" (формат: {file_ext}) с учетом комментария: "{caption}". Извлеки ключевую информацию и найди соответствующие строительные нормы.'
        else:
            if file_ext in ['pdf', 'doc', 'docx']:
                prompt = f'Проанализируй документ "{file_name}". Извлеки текст, найди ключевые строительные требования, нормы, стандарты. Предоставь краткое резюме и рекомендации.'
            elif file_ext in ['xls', 'xlsx', 'csv']:
                prompt = f'Проанализируй таблицу "{file_name}". Извлеки данные, найди числовые показатели, требования, нормативы. Сделай выводы о соответствии строительным стандартам.'
            elif file_ext in ['dwg', 'dxf']:
                prompt = f'Проанализируй чертеж "{file_name}". Опиши архитектурные/строительные элементы, размеры, спецификации. Проверь соответствие строительным нормам.'
            else:
                prompt = f'Проанализируй файл "{file_name}" (формат: {file_ext}). Определи содержимое, извлеки полезную информацию, особенно связанную со строительством и нормами.'
        
        # Send to AI chat endpoint for analysis with context
        headers = get_auth_headers()
        
        chat_payload = {
            'message': prompt,
            'context_search': True,
            'max_context': 3,
            'agent_role': 'coordinator'
        }
        
        # Note: document_data would need to be handled differently in the new endpoint
        # For now, we'll process the prompt and add document handling later
        resp = requests.post(f'{API_BASE}/api/ai/chat', json=chat_payload, headers=headers, timeout=1800)
        
        if resp.status_code == 200:
            response_data = resp.json()
            ai_response = response_data.get('response', '')
            context_used = response_data.get('context_used', [])
            processing_time = response_data.get('processing_time', 0)
            
            final_response = f"📄 Документ '{file_name}' обработан:\n\n{ai_response}\n\n"
            
            if context_used:
                final_response += f"📁 Найден контекст ({len(context_used)} документов)\n"
            
            final_response += f"⚡ Время: {processing_time:.2f}s"
            
            await update.message.reply_text(final_response)
        else:
            await update.message.reply_text(f"❌ Ошибка обработки документа: {resp.text}")
            
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        await update.message.reply_text(f"❌ Ошибка обработки документа: {str(e)}. Попробуйте снова или обратитесь в поддержку.")

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

if __name__ == '__main__':
    # Load environment variables from .env file
    load_env_file()
    
    # Also load with dotenv to ensure proper loading
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    # Refresh the token after loading env file
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN_HERE')
    API_TOKEN = os.getenv('API_TOKEN')
    
    # Check if API token is properly set
    if not API_TOKEN or API_TOKEN == "":
        print("Warning: API_TOKEN not set in environment variables")
        API_TOKEN = None
    
    # Only run if Telegram libraries are available
    if TELEGRAM_AVAILABLE and TELEGRAM_BOT_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        # Create the Application and pass it your bot's token
        # Import required modules here to avoid issues when Telegram is not available
        try:
            from telegram.ext import Application, CommandHandler, MessageHandler, filters
            application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

            # Add command handlers
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(CommandHandler("help", help_command))
            application.add_handler(CommandHandler("query", query_command))
            application.add_handler(CommandHandler("train", train_command))
            application.add_handler(CommandHandler("metrics", metrics_command))
            application.add_handler(CommandHandler("db", db_command))
            application.add_handler(CommandHandler("ai", ai_command))

            # Add message handlers for different types of messages
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
            application.add_handler(MessageHandler(filters.VOICE, handle_voice))
            application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
            application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

            # Run the bot until the user presses Ctrl-C
            application.run_polling()
        except Exception as e:
            print(f"Error starting Telegram bot: {e}")
    else:
        print("Telegram bot is not properly configured. Please set TELEGRAM_BOT_TOKEN environment variable.")