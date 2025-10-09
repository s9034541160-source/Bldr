"""
FastAPI webhook для Telegram бота с интеграцией tender_analyzer
"""
import os
import json
import hmac
import hashlib
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse
import asyncio
from pathlib import Path

# Импорты для обработки Telegram
from telegram import Update
from telegram.ext import Application

# Импорты для обработки манифестов
from services.bot.manifest_processor import ManifestProcessor
from services.bot.state_manager import StateManager
from services.bot.rate_limit import RateLimiter

# Создаем router
router = APIRouter(prefix="/tg", tags=["telegram"])

# Инициализация компонентов
manifest_processor = ManifestProcessor()
state_manager = StateManager()
rate_limiter = RateLimiter()

# Telegram Bot Token (из переменных окружения)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "default_secret")

# Инициализация бота
if BOT_TOKEN:
    application = Application.builder().token(BOT_TOKEN).build()
else:
    application = None


def verify_telegram_hash(data: bytes, secret: str, hash_header: str) -> bool:
    """
    Проверка подписи Telegram webhook
    
    Args:
        data: Тело запроса
        secret: Секретный ключ
        hash_header: Заголовок X-Telegram-Bot-Api-Secret-Token
        
    Returns:
        bool: True если подпись корректна
    """
    try:
        # Создаем HMAC SHA-256 подпись
        expected_hash = hmac.new(
            secret.encode('utf-8'),
            data,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_hash, hash_header)
    except Exception:
        return False


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None)
):
    """
    Webhook endpoint для Telegram бота
    
    Args:
        request: FastAPI Request объект
        x_telegram_bot_api_secret_token: Секретный токен Telegram
        
    Returns:
        JSONResponse: Результат обработки
    """
    try:
        # Получаем тело запроса
        body = await request.body()
        
        # Проверяем подпись (если настроена)
        if x_telegram_bot_api_secret_token:
            if not verify_telegram_hash(body, WEBHOOK_SECRET, x_telegram_bot_api_secret_token):
                raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Парсим JSON
        try:
            update_data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Создаем объект Update
        update = Update.de_json(update_data, application.bot if application else None)
        
        if not update:
            return JSONResponse(content={"ok": True, "message": "No update to process"})
        
        # Обрабатываем обновление
        result = await process_telegram_update(update)
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def process_telegram_update(update: Update) -> Dict[str, Any]:
    """
    Обработка обновления от Telegram
    
    Args:
        update: Telegram Update объект
        
    Returns:
        Dict: Результат обработки
    """
    try:
        # Получаем информацию о пользователе
        user_id = update.effective_user.id if update.effective_user else None
        chat_id = update.effective_chat.id if update.effective_chat else None
        
        if not user_id or not chat_id:
            return {"ok": False, "error": "No user or chat ID"}
        
        # Проверяем rate limit
        is_allowed, remaining = await rate_limiter.check_rate_limit(user_id)
        if not is_allowed:
            # Пользователь забанен
            is_banned, ban_until = await rate_limiter.is_user_banned(user_id)
            if is_banned:
                ban_time = ban_until - int(time.time()) if ban_until else 0
                await update.effective_message.reply_text(
                    f"🚫 **Вы заблокированы за спам!**\n\n"
                    f"⏰ Разблокировка через: {ban_time // 60} мин {ban_time % 60} сек\n"
                    f"📝 Лимит: 20 сообщений в минуту",
                    parse_mode="Markdown"
                )
                return {"ok": False, "error": "User banned for spam"}
        
        # Проверяем не забанен ли пользователь
        is_banned, ban_until = await rate_limiter.is_user_banned(user_id)
        if is_banned:
            ban_time = ban_until - int(time.time()) if ban_until else 0
            await update.effective_message.reply_text(
                f"🚫 **Вы заблокированы за спам!**\n\n"
                f"⏰ Разблокировка через: {ban_time // 60} мин {ban_time % 60} сек",
                parse_mode="Markdown"
            )
            return {"ok": False, "error": "User banned"}
        
        # Получаем текущее состояние пользователя
        user_state = await state_manager.get_user_state(user_id)
        
        # Определяем тип обновления
        if update.message:
            return await handle_message(update, user_state, user_id, chat_id)
        elif update.callback_query:
            return await handle_callback_query(update, user_state, user_id, chat_id)
        else:
            return {"ok": True, "message": "Unsupported update type"}
            
    except Exception as e:
        print(f"❌ Ошибка обработки обновления: {e}")
        return {"ok": False, "error": str(e)}


async def handle_message(update: Update, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
    """
    Обработка текстовых сообщений
    
    Args:
        update: Telegram Update
        user_state: Состояние пользователя
        user_id: ID пользователя
        chat_id: ID чата
        
    Returns:
        Dict: Результат обработки
    """
    message = update.message
    
    # Проверяем команды
    if message.text:
        if message.text.startswith('/'):
            return await handle_command(update, user_state, user_id, chat_id)
        else:
            return await handle_text_message(update, user_state, user_id, chat_id)
    
    # Проверяем файлы
    elif message.document:
        return await handle_document(update, user_state, user_id, chat_id)
    
    else:
        return {"ok": True, "message": "Unsupported message type"}


async def handle_callback_query(update: Update, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
    """
    Обработка callback запросов (кнопки)
    
    Args:
        update: Telegram Update
        user_state: Состояние пользователя
        user_id: ID пользователя
        chat_id: ID чата
        
    Returns:
        Dict: Результат обработки
    """
    callback_query = update.callback_query
    
    # Отвечаем на callback
    await callback_query.answer()
    
    # Обрабатываем данные callback
    callback_data = callback_query.data
    
    if callback_data == "tender_analysis":
        # Запускаем анализ тендера
        return await start_tender_analysis(update, user_state, user_id, chat_id)
    elif callback_data == "schedule":
        # Показываем график работ
        return await show_schedule(update, user_state, user_id, chat_id)
    elif callback_data == "finance":
        # Показываем финансовые показатели
        return await show_finance(update, user_state, user_id, chat_id)
    else:
        return {"ok": True, "message": "Unknown callback"}


async def handle_command(update: Update, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
    """
    Обработка команд
    
    Args:
        update: Telegram Update
        user_state: Состояние пользователя
        user_id: ID пользователя
        chat_id: ID чата
        
    Returns:
        Dict: Результат обработки
    """
    command = update.message.text
    
    if command == "/start":
        return await send_welcome_message(update, user_id, chat_id)
    elif command == "/tender":
        return await start_tender_analysis(update, user_state, user_id, chat_id)
    elif command == "/schedule":
        return await show_schedule(update, user_state, user_id, chat_id)
    elif command == "/finance":
        return await show_finance(update, user_state, user_id, chat_id)
    elif command == "/help":
        return await send_help_message(update, user_id, chat_id)
    elif command == "/смета":
        return await start_tender_analysis(update, user_state, user_id, chat_id)
    elif command == "/график":
        return await show_schedule(update, user_state, user_id, chat_id)
    elif command == "/проверить_рд":
        return await check_project_docs(update, user_state, user_id, chat_id)
    elif command == "/статус":
        return await show_status(update, user_id, chat_id)
    else:
        return {"ok": True, "message": "Unknown command"}


async def handle_text_message(update: Update, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
    """
    Обработка текстовых сообщений
    
    Args:
        update: Telegram Update
        user_state: Состояние пользователя
        user_id: ID пользователя
        chat_id: ID чата
        
    Returns:
        Dict: Результат обработки
    """
    # Если пользователь в процессе диалога, обрабатываем по манифесту
    if user_state and user_state.get("current_manifest"):
        return await manifest_processor.process_step(update, user_state, user_id, chat_id)
    else:
        # Отправляем главное меню
        return await send_main_menu(update, user_id, chat_id)


async def handle_document(update: Update, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
    """
    Обработка документов
    
    Args:
        update: Telegram Update
        user_state: Состояние пользователя
        user_id: ID пользователя
        chat_id: ID чата
        
    Returns:
        Dict: Результат обработки
    """
    document = update.message.document
    
    # Проверяем тип файла
    if document.mime_type == "application/pdf":
        # Если пользователь в процессе анализа тендера
        if user_state and user_state.get("current_manifest") == "tender":
            return await process_tender_pdf(update, user_state, user_id, chat_id)
        else:
            # Предлагаем начать анализ
            return await suggest_tender_analysis(update, user_id, chat_id)
    else:
        await update.message.reply_text("❌ Пожалуйста, отправьте PDF файл.")
        return {"ok": True, "message": "Invalid file type"}


# Обработчики команд
async def send_welcome_message(update: Update, user_id: int, chat_id: int) -> Dict[str, Any]:
    """Отправка приветственного сообщения"""
    welcome_text = """
🏗️ **Добро пожаловать в Tender Analyzer!**

Я помогу вам:
• 📄 Создать смету с маржой %
• 📊 Построить календарный план
• 💰 Рассчитать финансовые показатели

Выберите действие:
    """
    
    keyboard = [
        [{"text": "📄 Смета", "callback_data": "tender_analysis"}],
        [{"text": "📊 График", "callback_data": "schedule"}],
        [{"text": "💰 Финансы", "callback_data": "finance"}]
    ]
    
    await update.message.reply_text(
        welcome_text,
        reply_markup={"inline_keyboard": keyboard},
        parse_mode="Markdown"
    )
    
    return {"ok": True, "message": "Welcome message sent"}


async def start_tender_analysis(update: Update, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
    """Запуск анализа тендера"""
    # Загружаем манифест
    manifest_path = Path("manifests/tender.json")
    if not manifest_path.exists():
        await update.message.reply_text("❌ Ошибка: манифест не найден")
        return {"ok": False, "error": "Manifest not found"}
    
    # Устанавливаем состояние пользователя
    await state_manager.set_user_state(user_id, {
        "current_manifest": "tender",
        "step": 0,
        "data": {}
    })
    
    # Запускаем первый шаг манифеста
    return await manifest_processor.start_manifest(update, manifest_path, user_id, chat_id)


async def process_tender_pdf(update: Update, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
    """Обработка PDF файла тендера"""
    try:
        # Скачиваем файл
        file = await application.bot.get_file(update.message.document.file_id)
        file_path = f"/tmp/tender_{user_id}_{update.message.document.file_id}.pdf"
        
        await file.download_to_drive(file_path)
        
        # Запускаем анализ через tender_analyzer
        from services.tools.tender_analyzer.pipeline import TenderAnalyzerPipeline
        
        pipeline = TenderAnalyzerPipeline()
        
        # Получаем параметры из состояния
        region = user_state.get("data", {}).get("region", "Москва")
        shift_pattern = user_state.get("data", {}).get("shift_pattern", "30/15")
        
        # Запускаем анализ
        await update.message.reply_text("⏳ Анализирую тендер... Это займет несколько секунд.")
        
        zip_path = pipeline.analyze_tender(
            pdf_path=file_path,
            user_region=region,
            shift_pattern=shift_pattern,
            north_coeff=1.2
        )
        
        # Отправляем ZIP файл
        with open(zip_path, 'rb') as zip_file:
            await update.message.reply_document(
                document=zip_file,
                caption="✅ Анализ тендера завершен!\n\n📦 В архиве:\n• Смета с маржой %\n• Календарный план\n• Финансовый отчет\n• Отчет по тендеру"
            )
        
        # Очищаем состояние
        await state_manager.clear_user_state(user_id)
        
        # Показываем главное меню
        await send_main_menu(update, user_id, chat_id)
        
        return {"ok": True, "message": "Tender analysis completed"}
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка анализа: {str(e)}")
        return {"ok": False, "error": str(e)}


async def show_schedule(update: Update, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
    """Показ графика работ"""
    await update.message.reply_text("📊 График работ будет доступен после анализа тендера.")
    return {"ok": True, "message": "Schedule shown"}


async def show_finance(update: Update, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
    """Показ финансовых показателей"""
    await update.message.reply_text("💰 Финансовые показатели будут доступны после анализа тендера.")
    return {"ok": True, "message": "Finance shown"}


async def send_help_message(update: Update, user_id: int, chat_id: int) -> Dict[str, Any]:
    """Отправка справки"""
    help_text = """
❓ **Справка по командам:**

/start - Главное меню
/tender - Анализ тендера
/schedule - График работ
/finance - Финансовые показатели
/help - Эта справка

**Как использовать:**
1. Нажмите "📄 Смета"
2. Выберите регион и график вахты
3. Отправьте PDF файл тендера
4. Получите ZIP с результатами анализа
    """
    
    await update.message.reply_text(help_text, parse_mode="Markdown")
    return {"ok": True, "message": "Help sent"}


async def send_main_menu(update: Update, user_id: int, chat_id: int) -> Dict[str, Any]:
    """Отправка главного меню"""
    keyboard = [
        [{"text": "📄 Смета", "callback_data": "tender_analysis"}],
        [{"text": "📊 График", "callback_data": "schedule"}],
        [{"text": "💰 Финансы", "callback_data": "finance"}]
    ]
    
    await update.message.reply_text(
        "🏠 **Главное меню**\n\nВыберите действие:",
        reply_markup={"inline_keyboard": keyboard},
        parse_mode="Markdown"
    )
    
    return {"ok": True, "message": "Main menu sent"}


async def suggest_tender_analysis(update: Update, user_id: int, chat_id: int) -> Dict[str, Any]:
    """Предложение начать анализ тендера"""
    await update.message.reply_text(
        "📄 Отлично! Вы отправили PDF файл.\n\nДля анализа тендера нажмите кнопку ниже:",
        reply_markup={"inline_keyboard": [[{"text": "📄 Начать анализ", "callback_data": "tender_analysis"}]]}
    )
    return {"ok": True, "message": "Tender analysis suggested"}


async def check_project_docs(update: Update, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
    """Проверка проектной документации"""
    await update.message.reply_text(
        "🔍 **Проверка проектной документации**\n\n"
        "Эта функция будет доступна в следующих версиях.\n"
        "Пока что используйте команду /смета для анализа тендеров.",
        parse_mode="Markdown"
    )
    return {"ok": True, "message": "Project docs check shown"}


async def show_status(update: Update, user_id: int, chat_id: int) -> Dict[str, Any]:
    """Показ статуса системы и лимитов"""
    try:
        # Получаем статистику пользователя
        stats = await rate_limiter.get_user_stats(user_id)
        
        # Получаем информацию о хранилище
        storage_info = rate_limiter.get_storage_info()
        
        status_text = f"""
📊 **Статус системы**

👤 **Ваша статистика:**
• Сообщений: {stats['message_count']}
• Статус: {'🚫 Заблокирован' if stats['is_banned'] else '✅ Активен'}
• Хранилище: {stats['storage_type']}

🔧 **Система:**
• Хранилище: {storage_info['type']}
• Лимит: 20 сообщений/минуту
• Бан: 5 минут при превышении

💡 **Советы:**
• Используйте кнопки внизу экрана
• Не отправляйте много сообщений подряд
• При бане ждите 5 минут
        """
        
        await update.message.reply_text(status_text, parse_mode="Markdown")
        return {"ok": True, "message": "Status shown"}
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения статуса: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/health")
async def health_check():
    """Проверка состояния webhook"""
    return {
        "status": "healthy",
        "service": "telegram_webhook",
        "bot_token_configured": bool(BOT_TOKEN),
        "application_ready": bool(application)
    }
