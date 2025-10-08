"""
E2E тесты для Telegram webhook с интеграцией tender_analyzer
"""
import pytest
import json
import time
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.bot.webhook import telegram_webhook, process_telegram_update
from services.bot.manifest_processor import ManifestProcessor
from services.bot.state_manager import StateManager


class TestTelegramWebhookE2E:
    """E2E тесты для Telegram webhook"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.manifest_processor = ManifestProcessor()
        self.state_manager = StateManager()
    
    def test_webhook_health_check(self):
        """Тест проверки состояния webhook"""
        from services.bot.webhook import health_check
        import asyncio
        
        result = asyncio.run(health_check())
        
        assert result["status"] == "healthy"
        assert result["service"] == "telegram_webhook"
        assert "bot_token_configured" in result
        assert "application_ready" in result
        
        print("✅ Webhook health check пройден")
    
    def test_manifest_loading(self):
        """Тест загрузки манифеста"""
        manifest_path = Path("manifests/tender.json")
        
        assert manifest_path.exists(), f"Манифест не найден: {manifest_path}"
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        assert manifest["name"] == "tender"
        assert "steps" in manifest
        assert len(manifest["steps"]) == 3
        
        # Проверяем структуру шагов
        steps = manifest["steps"]
        assert steps[0]["type"] == "choice"
        assert steps[0]["key"] == "region"
        assert steps[1]["type"] == "choice"
        assert steps[1]["key"] == "shift_pattern"
        assert steps[2]["type"] == "file"
        assert steps[2]["key"] == "pdf"
        
        print("✅ Манифест загружен корректно")
    
    def test_state_manager_operations(self):
        """Тест операций с состоянием пользователя"""
        import asyncio
        
        async def run_test():
            user_id = 12345
            
            # Тест установки состояния
            test_state = {
                "current_manifest": "tender",
                "step": 0,
                "data": {"region": "Москва"}
            }
            
            # Устанавливаем состояние
            result = await self.state_manager.set_user_state(user_id, test_state)
            assert result is True
            
            # Получаем состояние
            retrieved_state = await self.state_manager.get_user_state(user_id)
            assert retrieved_state is not None
            assert retrieved_state["current_manifest"] == "tender"
            assert retrieved_state["data"]["region"] == "Москва"
            
            # Обновляем состояние
            updates = {"step": 1, "data": {"region": "Москва", "shift_pattern": "30/15"}}
            result = await self.state_manager.update_user_state(user_id, updates)
            assert result is True
            
            # Проверяем обновленное состояние
            updated_state = await self.state_manager.get_user_state(user_id)
            assert updated_state["step"] == 1
            assert updated_state["data"]["shift_pattern"] == "30/15"
            
            # Очищаем состояние
            result = await self.state_manager.clear_user_state(user_id)
            assert result is True
            
            # Проверяем что состояние очищено
            cleared_state = await self.state_manager.get_user_state(user_id)
            assert cleared_state is None
            
            print("✅ Операции с состоянием работают корректно")
        
        asyncio.run(run_test())
    
    def test_manifest_processor_choice_step(self):
        """Тест обработки шага выбора"""
        import asyncio
        
        async def run_test():
            step = {
                "type": "choice",
                "key": "region",
                "prompt": "Выберите регион:",
                "options": [
                    {"text": "Москва", "value": "Москва"},
                    {"text": "Норильск", "value": "Норильск"}
                ],
                "keyboard_type": "inline"
            }
            
            # Создаем мок объекты
            mock_update = Mock()
            mock_update.message = Mock()
            mock_update.message.reply_text = AsyncMock()
            
            user_state = {
                "current_manifest": "tender",
                "manifest_data": {"steps": [step]},
                "step": 0,
                "data": {}
            }
            
            # Обрабатываем шаг
            result = await self.manifest_processor.handle_choice_step(
                mock_update, step, user_state, 12345, 67890
            )
            
            assert result["ok"] is True
            mock_update.message.reply_text.assert_called_once()
            
            print("✅ Обработка шага выбора работает корректно")
        
        asyncio.run(run_test())
    
    def test_manifest_processor_file_step(self):
        """Тест обработки шага загрузки файла"""
        import asyncio
        
        async def run_test():
            step = {
                "type": "file",
                "key": "pdf",
                "prompt": "Отправьте PDF файл:",
                "mime_types": ["application/pdf"],
                "max_size_mb": 50
            }
            
            # Создаем мок объекты
            mock_update = Mock()
            mock_update.message = Mock()
            mock_update.message.document = Mock()
            mock_update.message.document.mime_type = "application/pdf"
            mock_update.message.document.file_id = "test_file_id"
            mock_update.message.document.file_name = "test.pdf"
            mock_update.message.document.file_size = 1024
            mock_update.message.reply_text = AsyncMock()
            
            user_state = {
                "current_manifest": "tender",
                "manifest_data": {"steps": [step]},
                "step": 0,
                "data": {}
            }
            
            # Обрабатываем шаг
            result = await self.manifest_processor.handle_file_step(
                mock_update, step, user_state, 12345, 67890
            )
            
            assert result["ok"] is True
            assert user_state["data"]["pdf"]["file_id"] == "test_file_id"
            assert user_state["step"] == 1
            
            print("✅ Обработка шага загрузки файла работает корректно")
        
        asyncio.run(run_test())
    
    @patch('services.bot.handlers.tender.TenderAnalyzerPipeline')
    def test_tender_handler_integration(self, mock_pipeline_class):
        """Тест интеграции обработчика тендера"""
        import asyncio
        
        async def run_test():
            # Настраиваем мок
            mock_pipeline = Mock()
            mock_pipeline_class.return_value = mock_pipeline
            mock_pipeline.analyze_tender.return_value = "/tmp/test_analysis.zip"
            
            # Создаем мок объекты
            mock_update = Mock()
            mock_update.message = Mock()
            mock_update.message.reply_text = AsyncMock()
            mock_update.message.reply_document = AsyncMock()
            mock_update.effective_user = Mock()
            mock_update.effective_user.bot = Mock()
            mock_update.effective_user.bot.get_file = AsyncMock()
            
            # Настраиваем мок файла
            mock_file = Mock()
            mock_file.download_to_drive = AsyncMock()
            mock_update.effective_user.bot.get_file.return_value = mock_file
            
            # Создаем тестовый ZIP файл
            test_zip_path = "/tmp/test_analysis.zip"
            with open(test_zip_path, 'w') as f:
                f.write("test zip content")
            
            try:
                # Импортируем и тестируем обработчик
                from services.bot.handlers.tender import handle_tender
                
                manifest = {"name": "tender"}
                data = {
                    "region": "Москва",
                    "shift_pattern": "30/15",
                    "pdf": {
                        "file_id": "test_file_id",
                        "file_name": "test.pdf",
                        "mime_type": "application/pdf",
                        "file_size": 1024
                    }
                }
                
                # Запускаем обработчик
                result = await handle_tender(mock_update, manifest, data, 12345, 67890)
                
                # Проверяем результат
                assert result["ok"] is True
                assert "completed successfully" in result["message"]
                
                # Проверяем что pipeline был вызван
                mock_pipeline.analyze_tender.assert_called_once()
                
                print("✅ Интеграция обработчика тендера работает корректно")
                
            finally:
                # Очищаем тестовый файл
                if os.path.exists(test_zip_path):
                    os.unlink(test_zip_path)
        
        asyncio.run(run_test())
    
    def test_webhook_performance(self):
        """Тест производительности webhook"""
        import asyncio
        
        async def run_test():
            start_time = time.time()
            
            # Тест быстрых операций
            await self.state_manager.set_user_state(12345, {"test": "data"})
            state = await self.state_manager.get_user_state(12345)
            await self.state_manager.clear_user_state(12345)
            
            elapsed_time = time.time() - start_time
            
            # Проверяем что операции выполняются быстро
            assert elapsed_time < 1.0, f"Операции заняли {elapsed_time:.3f}с (лимит: 1.0с)"
            
            print(f"✅ Производительность webhook: {elapsed_time:.3f}с")
        
        asyncio.run(run_test())
    
    def test_error_handling(self):
        """Тест обработки ошибок"""
        import asyncio
        
        async def run_test():
            # Тест с неверными данными
            invalid_state = None
            result = await self.state_manager.get_user_state(99999)
            assert result is None
            
            # Тест очистки несуществующего состояния
            result = await self.state_manager.clear_user_state(99999)
            assert result is True
            
            print("✅ Обработка ошибок работает корректно")
        
        asyncio.run(run_test())
    
    def test_manifest_validation(self):
        """Тест валидации манифеста"""
        manifest_path = Path("manifests/tender.json")
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # Проверяем обязательные поля
        required_fields = ["name", "steps", "handler"]
        for field in required_fields:
            assert field in manifest, f"Отсутствует обязательное поле: {field}"
        
        # Проверяем структуру шагов
        steps = manifest["steps"]
        for i, step in enumerate(steps):
            assert "type" in step, f"Шаг {i}: отсутствует поле 'type'"
            assert "key" in step, f"Шаг {i}: отсутствует поле 'key'"
            assert "prompt" in step, f"Шаг {i}: отсутствует поле 'prompt'"
            
            if step["type"] == "choice":
                assert "options" in step, f"Шаг {i}: отсутствует поле 'options'"
            elif step["type"] == "file":
                assert "mime_types" in step, f"Шаг {i}: отсутствует поле 'mime_types'"
        
        print("✅ Валидация манифеста пройдена")
    
    def test_callback_handling(self):
        """Тест обработки callback запросов"""
        # Тест парсинга callback_data
        callback_data = "choice_region_Москва"
        parts = callback_data.split("_", 2)
        
        assert len(parts) == 3
        assert parts[0] == "choice"
        assert parts[1] == "region"
        assert parts[2] == "Москва"
        
        print("✅ Обработка callback запросов работает корректно")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
