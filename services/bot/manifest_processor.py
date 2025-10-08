"""
Обработчик JSON манифестов для Telegram бота
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application

from services.bot.state_manager import StateManager

class ManifestProcessor:
    """Обработчик манифестов диалогов"""
    
    def __init__(self):
        self.state_manager = StateManager()
    
    async def start_manifest(self, update: Update, manifest_path: Path, user_id: int, chat_id: int) -> Dict[str, Any]:
        """
        Запуск диалога по манифесту
        
        Args:
            update: Telegram Update
            manifest_path: Путь к манифесту
            user_id: ID пользователя
            chat_id: ID чата
            
        Returns:
            Dict: Результат обработки
        """
        try:
            # Загружаем манифест
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Устанавливаем состояние
            await self.state_manager.set_user_state(user_id, {
                "current_manifest": manifest["name"],
                "manifest_data": manifest,
                "step": 0,
                "data": {}
            })
            
            # Запускаем первый шаг
            return await self.process_step(update, None, user_id, chat_id)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка загрузки манифеста: {str(e)}")
            return {"ok": False, "error": str(e)}
    
    async def process_step(self, update: Update, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
        """
        Обработка текущего шага диалога
        
        Args:
            update: Telegram Update
            user_state: Состояние пользователя
            user_id: ID пользователя
            chat_id: ID чата
            
        Returns:
            Dict: Результат обработки
        """
        try:
            # Получаем состояние пользователя
            if not user_state:
                user_state = await self.state_manager.get_user_state(user_id)
            
            if not user_state or not user_state.get("manifest_data"):
                return {"ok": False, "error": "No active manifest"}
            
            manifest = user_state["manifest_data"]
            current_step = user_state.get("step", 0)
            steps = manifest.get("steps", [])
            
            if current_step >= len(steps):
                # Диалог завершен
                return await self.complete_manifest(update, user_state, user_id, chat_id)
            
            step = steps[current_step]
            step_type = step.get("type")
            
            if step_type == "choice":
                return await self.handle_choice_step(update, step, user_state, user_id, chat_id)
            elif step_type == "file":
                return await self.handle_file_step(update, step, user_state, user_id, chat_id)
            elif step_type == "text":
                return await self.handle_text_step(update, step, user_state, user_id, chat_id)
            else:
                return {"ok": False, "error": f"Unknown step type: {step_type}"}
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка обработки шага: {str(e)}")
            return {"ok": False, "error": str(e)}
    
    async def handle_choice_step(self, update: Update, step: Dict, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
        """Обработка шага выбора"""
        try:
            prompt = step.get("prompt", "Выберите опцию:")
            options = step.get("options", [])
            key = step.get("key")
            keyboard_type = step.get("keyboard_type", "inline")
            
            # Создаем клавиатуру
            if keyboard_type == "inline":
                keyboard = []
                for option in options:
                    if isinstance(option, dict):
                        text = option.get("text", "")
                        value = option.get("value", "")
                        keyboard.append([InlineKeyboardButton(text, callback_data=f"choice_{key}_{value}")])
                    else:
                        keyboard.append([InlineKeyboardButton(str(option), callback_data=f"choice_{key}_{option}")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
            else:
                # Обычная клавиатура
                keyboard = []
                for option in options:
                    if isinstance(option, dict):
                        text = option.get("text", "")
                        keyboard.append([text])
                    else:
                        keyboard.append([str(option)])
                
                reply_markup = {"keyboard": keyboard, "resize_keyboard": True}
            
            # Отправляем сообщение
            await update.message.reply_text(prompt, reply_markup=reply_markup)
            
            return {"ok": True, "message": "Choice step sent"}
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка обработки выбора: {str(e)}")
            return {"ok": False, "error": str(e)}
    
    async def handle_file_step(self, update: Update, step: Dict, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
        """Обработка шага загрузки файла"""
        try:
            prompt = step.get("prompt", "Отправьте файл:")
            mime_types = step.get("mime_types", [])
            max_size_mb = step.get("max_size_mb", 50)
            
            # Проверяем тип сообщения
            if update.message and update.message.document:
                document = update.message.document
                
                # Проверяем тип файла
                if mime_types and document.mime_type not in mime_types:
                    await update.message.reply_text(f"❌ Неверный тип файла. Ожидается: {', '.join(mime_types)}")
                    return {"ok": False, "error": "Invalid file type"}
                
                # Проверяем размер файла
                if document.file_size and document.file_size > max_size_mb * 1024 * 1024:
                    await update.message.reply_text(f"❌ Файл слишком большой. Максимальный размер: {max_size_mb} МБ")
                    return {"ok": False, "error": "File too large"}
                
                # Сохраняем данные файла
                key = step.get("key")
                user_state["data"][key] = {
                    "file_id": document.file_id,
                    "file_name": document.file_name,
                    "mime_type": document.mime_type,
                    "file_size": document.file_size
                }
                
                # Переходим к следующему шагу
                user_state["step"] += 1
                await self.state_manager.set_user_state(user_id, user_state)
                
                # Обрабатываем следующий шаг
                return await self.process_step(update, user_state, user_id, chat_id)
            else:
                # Запрашиваем файл
                await update.message.reply_text(prompt)
                return {"ok": True, "message": "File step sent"}
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка обработки файла: {str(e)}")
            return {"ok": False, "error": str(e)}
    
    async def handle_text_step(self, update: Update, step: Dict, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
        """Обработка шага ввода текста"""
        try:
            prompt = step.get("prompt", "Введите текст:")
            key = step.get("key")
            
            if update.message and update.message.text:
                # Сохраняем введенный текст
                user_state["data"][key] = update.message.text
                
                # Переходим к следующему шагу
                user_state["step"] += 1
                await self.state_manager.set_user_state(user_id, user_state)
                
                # Обрабатываем следующий шаг
                return await self.process_step(update, user_state, user_id, chat_id)
            else:
                # Запрашиваем текст
                await update.message.reply_text(prompt)
                return {"ok": True, "message": "Text step sent"}
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка обработки текста: {str(e)}")
            return {"ok": False, "error": str(e)}
    
    async def handle_callback_choice(self, update: Update, callback_data: str, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
        """Обработка выбора из callback"""
        try:
            # Парсим callback_data: "choice_{key}_{value}"
            parts = callback_data.split("_", 2)
            if len(parts) != 3 or parts[0] != "choice":
                return {"ok": False, "error": "Invalid callback data"}
            
            key = parts[1]
            value = parts[2]
            
            # Сохраняем выбор
            user_state["data"][key] = value
            
            # Переходим к следующему шагу
            user_state["step"] += 1
            await self.state_manager.set_user_state(user_id, user_state)
            
            # Отвечаем на callback
            await update.callback_query.answer(f"Выбрано: {value}")
            
            # Обрабатываем следующий шаг
            return await self.process_step(update, user_state, user_id, chat_id)
            
        except Exception as e:
            await update.callback_query.answer(f"❌ Ошибка: {str(e)}")
            return {"ok": False, "error": str(e)}
    
    async def complete_manifest(self, update: Update, user_state: Dict, user_id: int, chat_id: int) -> Dict[str, Any]:
        """Завершение диалога по манифесту"""
        try:
            manifest = user_state["manifest_data"]
            data = user_state["data"]
            
            # Отправляем сообщение об успехе
            success_message = manifest.get("success_message", "✅ Диалог завершен!")
            await update.message.reply_text(success_message)
            
            # Вызываем обработчик манифеста
            handler_path = manifest.get("handler")
            if handler_path:
                # Импортируем и вызываем обработчик
                module_path, function_name = handler_path.rsplit(".", 1)
                module = __import__(module_path, fromlist=[function_name])
                handler_function = getattr(module, function_name)
                
                # Вызываем обработчик
                result = await handler_function(update, manifest, data, user_id, chat_id)
                
                return result
            
            # Очищаем состояние
            await self.state_manager.clear_user_state(user_id)
            
            return {"ok": True, "message": "Manifest completed"}
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка завершения диалога: {str(e)}")
            return {"ok": False, "error": str(e)}
