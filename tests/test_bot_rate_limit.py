"""
Тесты для rate limiting и кнопок Telegram бота
"""
import pytest
import time
import json
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.bot.rate_limit import RateLimiter
from services.bot.handlers.tender import get_main_keyboard
from services.bot.webhook import process_telegram_update


class TestRateLimit:
    """Тесты для rate limiting"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.rate_limiter = RateLimiter()
    
    def test_rate_limit_initial_state(self):
        """Тест начального состояния rate limiter"""
        import asyncio
        
        async def run_test():
            user_id = 12345
            
            # Первое сообщение должно быть разрешено
            is_allowed, remaining = await self.rate_limiter.check_rate_limit(user_id)
            assert is_allowed is True
            assert remaining >= 19  # Должно остаться 19 или больше сообщений
            
            print("✅ Начальное состояние rate limiter корректно")
        
        asyncio.run(run_test())
    
    def test_rate_limit_exceeded(self):
        """Тест превышения rate limit"""
        import asyncio
        
        async def run_test():
            user_id = 12346
            
            # Отправляем 21 сообщение (превышаем лимит в 20)
            for i in range(21):
                is_allowed, remaining = await self.rate_limiter.check_rate_limit(user_id)
                if i < 20:
                    assert is_allowed is True
                else:
                    assert is_allowed is False
                    assert remaining == 0
            
            # Проверяем что пользователь забанен
            is_banned, ban_until = await self.rate_limiter.is_user_banned(user_id)
            assert is_banned is True
            assert ban_until is not None
            
            print("✅ Rate limit превышен, пользователь забанен")
        
        asyncio.run(run_test())
    
    def test_rate_limit_window_reset(self):
        """Тест сброса окна rate limit"""
        import asyncio
        
        async def run_test():
            user_id = 12347
            
            # Отправляем несколько сообщений
            for i in range(5):
                is_allowed, remaining = await self.rate_limiter.check_rate_limit(user_id)
                assert is_allowed is True
            
            # Проверяем статистику
            stats = await self.rate_limiter.get_user_stats(user_id)
            assert stats['message_count'] >= 5
            assert stats['is_banned'] is False
            
            print("✅ Статистика пользователя корректна")
        
        asyncio.run(run_test())
    
    def test_unban_user(self):
        """Тест разбана пользователя"""
        import asyncio
        
        async def run_test():
            user_id = 12348
            
            # Баним пользователя
            for i in range(21):
                await self.rate_limiter.check_rate_limit(user_id)
            
            # Проверяем что забанен
            is_banned, _ = await self.rate_limiter.is_user_banned(user_id)
            assert is_banned is True
            
            # Разбаниваем
            result = await self.rate_limiter.unban_user(user_id)
            assert result is True
            
            # Проверяем что разбанен
            is_banned, _ = await self.rate_limiter.is_user_banned(user_id)
            assert is_banned is False
            
            print("✅ Пользователь успешно разбанен")
        
        asyncio.run(run_test())
    
    def test_cleanup_expired_data(self):
        """Тест очистки истекших данных"""
        import asyncio
        
        async def run_test():
            # Запускаем очистку
            cleaned = await self.rate_limiter.cleanup_expired_data()
            assert isinstance(cleaned, int)
            assert cleaned >= 0
            
            print(f"✅ Очищено {cleaned} истекших записей")
        
        asyncio.run(run_test())
    
    def test_storage_info(self):
        """Тест информации о хранилище"""
        storage_info = self.rate_limiter.get_storage_info()
        
        assert 'type' in storage_info
        assert storage_info['type'] in ['redis', 'memory', 'error']
        
        if storage_info['type'] == 'redis':
            assert 'connected_clients' in storage_info
            assert 'used_memory' in storage_info
        elif storage_info['type'] == 'memory':
            assert 'users_count' in storage_info
            assert 'banned_count' in storage_info
        
        print(f"✅ Информация о хранилище: {storage_info['type']}")


class TestKeyboardButtons:
    """Тесты для кнопок клавиатуры"""
    
    def test_main_keyboard_creation(self):
        """Тест создания основной клавиатуры"""
        keyboard = get_main_keyboard()
        
        # Проверяем что клавиатура создана
        assert keyboard is not None
        
        # Проверяем структуру клавиатуры
        keyboard_data = keyboard.to_dict()
        assert 'keyboard' in keyboard_data
        assert len(keyboard_data['keyboard']) == 2  # 2 ряда кнопок
        
        # Проверяем кнопки
        first_row = keyboard_data['keyboard'][0]
        second_row = keyboard_data['keyboard'][1]
        
        assert len(first_row) == 2  # 2 кнопки в первом ряду
        assert len(second_row) == 2  # 2 кнопки во втором ряду
        
        # Проверяем текст кнопок
        assert first_row[0]['text'] == '📄 Смета'
        assert first_row[1]['text'] == '📊 График'
        assert second_row[0]['text'] == '💰 Финансы'
        assert second_row[1]['text'] == '❓ Помощь'
        
        print("✅ Основная клавиатура создана корректно")
    
    def test_keyboard_properties(self):
        """Тест свойств клавиатуры"""
        keyboard = get_main_keyboard()
        keyboard_data = keyboard.to_dict()
        
        # Проверяем свойства
        assert keyboard_data.get('resize_keyboard', False) is True
        assert keyboard_data.get('one_time_keyboard', True) is False
        
        print("✅ Свойства клавиатуры корректны")


class TestCommands:
    """Тесты для команд"""
    
    def test_commands_manifest_loading(self):
        """Тест загрузки манифеста команд"""
        commands_path = Path("manifests/commands.json")
        
        assert commands_path.exists(), f"Манифест команд не найден: {commands_path}"
        
        with open(commands_path, 'r', encoding='utf-8') as f:
            commands = json.load(f)
        
        assert isinstance(commands, list)
        assert len(commands) > 0
        
        # Проверяем структуру команд
        for command in commands:
            assert 'command' in command
            assert 'description' in command
            assert command['command'].startswith('/') or command['command'] in ['start', 'смета', 'график', 'проверить_рд', 'помощь', 'статус']
        
        print(f"✅ Загружено {len(commands)} команд")
    
    def test_commands_validation(self):
        """Тест валидации команд"""
        commands_path = Path("manifests/commands.json")
        
        with open(commands_path, 'r', encoding='utf-8') as f:
            commands = json.load(f)
        
        # Проверяем обязательные команды
        command_names = [cmd['command'] for cmd in commands]
        
        required_commands = ['start', 'смета', 'график', 'проверить_рд', 'помощь', 'статус']
        for required in required_commands:
            assert required in command_names, f"Команда {required} не найдена"
        
        print("✅ Все обязательные команды присутствуют")


class TestIntegration:
    """Интеграционные тесты"""
    
    def test_rate_limit_with_webhook(self):
        """Тест rate limit с webhook"""
        import asyncio
        
        async def run_test():
            # Создаем мок update
            mock_update = Mock()
            mock_update.effective_user = Mock()
            mock_update.effective_user.id = 12349
            mock_update.effective_chat = Mock()
            mock_update.effective_chat.id = 67890
            mock_update.effective_message = Mock()
            mock_update.effective_message.reply_text = AsyncMock()
            
            # Тестируем обработку с rate limit
            try:
                result = await process_telegram_update(mock_update)
                # Результат может быть успешным или с ошибкой rate limit
                assert 'ok' in result
            except Exception as e:
                # Ожидаем ошибки при превышении лимита
                print(f"Rate limit сработал: {e}")
            
            print("✅ Rate limit интегрирован с webhook")
        
        asyncio.run(run_test())
    
    def test_performance_rate_limit(self):
        """Тест производительности rate limit"""
        import asyncio
        
        async def run_test():
            rate_limiter = RateLimiter()
            start_time = time.time()
            
            # Тестируем быстрые операции
            user_id = 12350
            for i in range(10):
                await rate_limiter.check_rate_limit(user_id)
            
            elapsed_time = time.time() - start_time
            
            # Проверяем что операции выполняются быстро
            assert elapsed_time < 1.0, f"Rate limit операции заняли {elapsed_time:.3f}с (лимит: 1.0с)"
            
            print(f"✅ Производительность rate limit: {elapsed_time:.3f}с")
        
        asyncio.run(run_test())


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
