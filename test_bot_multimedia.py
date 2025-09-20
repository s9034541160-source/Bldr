#!/usr/bin/env python3
"""
Test Telegram Bot Multimedia Features
Test voice, photo, and document handling capabilities
"""

import requests
import json
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE = 'http://localhost:8000'
API_TOKEN = os.getenv('API_TOKEN')

def get_auth_headers():
    """Get authentication headers for API calls"""
    headers = {
        "Content-Type": "application/json"
    }
    if API_TOKEN:
        headers['Authorization'] = f'Bearer {API_TOKEN}'
    return headers

def test_api_multimedia_support():
    """Test if API supports multimedia data"""
    print("🧪 Тестирование поддержки мультимедиа в API...")
    
    # Test 1: Check if AI endpoint accepts image_data
    test_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="  # 1x1 pixel PNG
    
    try:
        headers = get_auth_headers()
        payload = {
            'prompt': 'Тест обработки изображения',
            'image_data': test_image_data,
            'model': 'deepseek/deepseek-r1-0528-qwen3-8b'
        }
        
        response = requests.post(f'{API_BASE}/ai', json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ API поддерживает обработку изображений")
        elif response.status_code == 422:
            print("❌ API не поддерживает поле 'image_data' - нужно добавить в модель")
        else:
            print(f"⚠️ Неожиданный ответ: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования поддержки изображений: {str(e)}")
    
    # Test 2: Check if AI endpoint accepts voice_data
    try:
        headers = get_auth_headers()
        payload = {
            'prompt': 'Тест обработки голоса',
            'voice_data': test_image_data,  # Using same base64 data for test
            'model': 'deepseek/deepseek-r1-0528-qwen3-8b'
        }
        
        response = requests.post(f'{API_BASE}/ai', json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ API поддерживает обработку голосовых сообщений")
        elif response.status_code == 422:
            print("❌ API не поддерживает поле 'voice_data' - нужно добавить в модель")
        else:
            print(f"⚠️ Неожиданный ответ: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования поддержки голоса: {str(e)}")
    
    # Test 3: Check if AI endpoint accepts document_data
    try:
        headers = get_auth_headers()
        payload = {
            'prompt': 'Тест обработки документа',
            'document_data': test_image_data,  # Using same base64 data for test
            'document_name': 'test.pdf',
            'model': 'deepseek/deepseek-r1-0528-qwen3-8b'
        }
        
        response = requests.post(f'{API_BASE}/ai', json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ API поддерживает обработку документов")
        elif response.status_code == 422:
            print("❌ API не поддерживает поле 'document_data' - нужно добавить в модель")
        else:
            print(f"⚠️ Неожиданный ответ: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования поддержки документов: {str(e)}")

def check_bot_dependencies():
    """Check if bot dependencies are available"""
    print("\n🔍 Проверка зависимостей бота...")
    
    try:
        import telegram
        print("✅ Python-telegram-bot установлен")
    except ImportError:
        print("❌ Python-telegram-bot НЕ установлен - нужно: pip install python-telegram-bot")
    
    try:
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if telegram_token and telegram_token != 'YOUR_TELEGRAM_BOT_TOKEN_HERE':
            print("✅ TELEGRAM_BOT_TOKEN настроен")
        else:
            print("❌ TELEGRAM_BOT_TOKEN не настроен в .env файле")
    except Exception as e:
        print(f"❌ Ошибка проверки токена: {str(e)}")

def show_bot_features_summary():
    """Show summary of bot capabilities"""
    print("\n📋 Сводка возможностей Telegram бота:")
    print("━" * 60)
    
    features = [
        ("🎤 Голосовые сообщения", "Транскрипция + анализ строит. норм"),
        ("📸 Фото/Изображения", "OCR + анализ чертежей/документов"),
        ("📄 Документы", "PDF/Word/Excel/DWG - извлечение + анализ"),
        ("💬 Текстовые сообщения", "Прямой поиск в нормативах (без команд)"),
        ("🤖 AI-генерация", "Ответы на основе моделей DeepSeek"),
        ("📊 Системные метрики", "Просмотр статуса и производительности"),
        ("🚀 Обучение RAG", "Добавление новых документов в базу"),
        ("💾 Neo4j запросы", "Прямые Cypher запросы к графовой БД")
    ]
    
    for feature, description in features:
        print(f"  {feature:<20} - {description}")
    
    print("━" * 60)
    print("🔧 Автоматическая обработка:")
    print("  • Отправьте любой контент → бот определит тип и обработает")
    print("  • Поддержка подписей к файлам и фото для контекста")  
    print("  • Все сообщения об ошибках переведены на русский язык")
    print("  • Лимит файлов: 20MB для обработки")
    
def main():
    """Main test function"""
    print("🤖 Тестирование мультимедиа возможностей Telegram бота")
    print("=" * 60)
    
    # Test API multimedia support
    test_api_multimedia_support()
    
    # Check dependencies
    check_bot_dependencies()
    
    # Show features summary  
    show_bot_features_summary()
    
    print("\n✨ Тестирование завершено!")
    print("\nДля запуска бота используйте:")
    print("  python integrations/telegram_bot.py")
    
    print("\nПримеры использования:")
    print("  📝 'какие требования к бетону М300?' - текстовый запрос")
    print("  🎤 Голосовое сообщение с вопросом")
    print("  📸 Фото чертежа с подписью 'проанализируй'")
    print("  📄 PDF файл со СНиП или ГОСТ")

if __name__ == '__main__':
    main()