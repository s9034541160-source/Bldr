"""
Обработчик для анализа тендеров
"""
import os
import tempfile
from typing import Dict, Any
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from pathlib import Path

from services.tools.tender_analyzer.pipeline import TenderAnalyzerPipeline

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Создание основной клавиатуры с кнопками"""
    keyboard = [
        [KeyboardButton("📄 Смета"), KeyboardButton("📊 График")],
        [KeyboardButton("💰 Финансы"), KeyboardButton("❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def handle_tender(update: Update, manifest: Dict[str, Any], data: Dict[str, Any], user_id: int, chat_id: int) -> Dict[str, Any]:
    """
    Обработчик анализа тендера
    
    Args:
        update: Telegram Update
        manifest: Манифест диалога
        data: Данные пользователя
        user_id: ID пользователя
        chat_id: ID чата
        
    Returns:
        Dict: Результат обработки
    """
    try:
        # Получаем параметры из данных пользователя
        region = data.get("region", "Москва")
        shift_pattern = data.get("shift_pattern", "30/15")
        pdf_data = data.get("pdf")
        
        if not pdf_data:
            await update.message.reply_text("❌ PDF файл не найден в данных")
            return {"ok": False, "error": "PDF file not found"}
        
        # Скачиваем PDF файл
        file_id = pdf_data.get("file_id")
        if not file_id:
            await update.message.reply_text("❌ ID файла не найден")
            return {"ok": False, "error": "File ID not found"}
        
        # Получаем бота из update
        bot = update.effective_user.bot if hasattr(update.effective_user, 'bot') else None
        if not bot:
            await update.message.reply_text("❌ Бот недоступен")
            return {"ok": False, "error": "Bot not available"}
        
        # Скачиваем файл
        file = await bot.get_file(file_id)
        temp_pdf_path = f"/tmp/tender_{user_id}_{file_id}.pdf"
        await file.download_to_drive(temp_pdf_path)
        
        # Запускаем анализ
        await update.message.reply_text("⏳ Анализирую тендер... Это займет несколько секунд.")
        
        pipeline = TenderAnalyzerPipeline()
        zip_path = pipeline.analyze_tender(
            pdf_path=temp_pdf_path,
            user_region=region,
            shift_pattern=shift_pattern,
            north_coeff=1.2
        )
        
        # Отправляем ZIP файл
        with open(zip_path, 'rb') as zip_file:
            await update.message.reply_document(
                document=zip_file,
                caption=f"✅ **Анализ тендера завершен!**\n\n"
                       f"🏢 **Регион:** {region}\n"
                       f"⏰ **График вахты:** {shift_pattern}\n\n"
                       f"📦 **В архиве:**\n"
                       f"• 📄 Смета с маржой %\n"
                       f"• 📊 Календарный план\n"
                       f"• 💰 Финансовый отчет\n"
                       f"• 📋 Отчет по тендеру",
                parse_mode="Markdown"
            )
        
        # Показываем кнопки после анализа
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [InlineKeyboardButton("📄 Скачать смету", callback_data="download_estimate")],
            [InlineKeyboardButton("📊 График работ", callback_data="view_schedule")],
            [InlineKeyboardButton("💰 Финансы", callback_data="view_finance")],
            [InlineKeyboardButton("🔄 Новый анализ", callback_data="new_analysis")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем сообщение с inline кнопками
        await update.message.reply_text(
            "🎉 **Анализ завершен успешно!**\n\n"
            "Выберите дальнейшее действие:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Отправляем основную клавиатуру
        main_keyboard = get_main_keyboard()
        await update.message.reply_text(
            "💡 **Используйте кнопки внизу для быстрого доступа к функциям:**",
            reply_markup=main_keyboard,
            parse_mode="Markdown"
        )
        
        # Очищаем временный файл
        try:
            os.unlink(temp_pdf_path)
        except:
            pass
        
        return {"ok": True, "message": "Tender analysis completed successfully"}
        
    except Exception as e:
        await update.message.reply_text(f"❌ **Ошибка анализа тендера:**\n\n{str(e)}")
        return {"ok": False, "error": str(e)}


async def handle_download_estimate(update: Update, user_id: int, chat_id: int) -> Dict[str, Any]:
    """Обработка скачивания сметы"""
    try:
        await update.callback_query.answer("📄 Смета уже включена в ZIP файл выше")
        return {"ok": True, "message": "Estimate download info sent"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def handle_view_schedule(update: Update, user_id: int, chat_id: int) -> Dict[str, Any]:
    """Обработка просмотра графика работ"""
    try:
        await update.callback_query.answer("📊 График работ включен в ZIP файл как gantt.xlsx")
        return {"ok": True, "message": "Schedule view info sent"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def handle_view_finance(update: Update, user_id: int, chat_id: int) -> Dict[str, Any]:
    """Обработка просмотра финансовых показателей"""
    try:
        await update.callback_query.answer("💰 Финансовые показатели включены в ZIP файл как finance.json")
        return {"ok": True, "message": "Finance view info sent"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def handle_new_analysis(update: Update, user_id: int, chat_id: int) -> Dict[str, Any]:
    """Обработка нового анализа"""
    try:
        from services.bot.state_manager import StateManager
        
        # Очищаем состояние пользователя
        state_manager = StateManager()
        await state_manager.clear_user_state(user_id)
        
        # Отправляем сообщение о начале нового анализа
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [InlineKeyboardButton("📄 Начать анализ", callback_data="tender_analysis")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "🔄 **Новый анализ тендера**\n\n"
            "Для начала нового анализа нажмите кнопку ниже:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return {"ok": True, "message": "New analysis started"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def handle_main_menu(update: Update, user_id: int, chat_id: int) -> Dict[str, Any]:
    """Обработка возврата в главное меню"""
    try:
        from services.bot.state_manager import StateManager
        
        # Очищаем состояние пользователя
        state_manager = StateManager()
        await state_manager.clear_user_state(user_id)
        
        # Отправляем главное меню
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [InlineKeyboardButton("📄 Смета", callback_data="tender_analysis")],
            [InlineKeyboardButton("📊 График", callback_data="schedule")],
            [InlineKeyboardButton("💰 Финансы", callback_data="finance")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "🏠 **Главное меню**\n\n"
            "Выберите действие:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return {"ok": True, "message": "Main menu shown"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
