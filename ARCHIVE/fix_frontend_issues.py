#!/usr/bin/env python3
"""
Исправление основных проблем фронтенда
"""

import os
import json

# Исправление 1: История чата при переключении вкладок
def fix_chat_history():
    print("🔧 Исправляем сохранение истории чата...")
    
    # Создаём патч для App.tsx - добавляем инициализацию токена
    app_patch = '''
// В начале компонента App добавить:
useEffect(() => {
  // Инициализация токена из localStorage при загрузке
  const token = localStorage.getItem('token');
  if (token && !useStore.getState().user?.token) {
    const userData = {
      token: token,
      username: localStorage.getItem('username') || 'user',
      role: localStorage.getItem('role') || 'user'
    };
    useStore.getState().setUser(userData);
  }
}, []);
'''
    
    print("✅ Патч для App.tsx готов")
    return app_patch

# Исправление 2: ProTools аутентификация
def fix_protools_auth():
    print("🔧 Исправляем аутентификацию в ProTools...")
    
    auth_fix = '''
// В начале handleGenerateLetter добавить проверку токена:
const token = useStore.getState().user?.token || localStorage.getItem('token');
if (!token) {
  message.error('Нет токена аутентификации. Войдите в систему.');
  return;
}

// Убрать обязательность полей кроме description:
const letterData = {
  description: values.description, // ОБЯЗАТЕЛЬНОЕ
  template_id: values.template_id || 'compliance_sp31',
  project_id: values.project_id,
  recipient: values.recipient || '',
  sender: values.sender || 'АО БЛДР',
  // Остальные поля опциональны
};
'''
    
    print("✅ Исправление ProTools готово")
    return auth_fix

# Исправление 3: File Manager 422 ошибка
def fix_file_manager():
    print("🔧 Исправляем File Manager...")
    
    fm_fix = '''
// В FileManager.tsx исправить запрос на обучение:
const handleStartTraining = async () => {
  setLoading(true);
  try {
    const trainData = {
      custom_dir: selectedPath || "I:/docs/downloaded" // Добавить дефолтный путь
    };
    
    const response = await apiService.startTraining(trainData);
    message.success('Обучение запущено успешно!');
  } catch (error) {
    console.error('Training error:', error);
    message.error('Ошибка запуска обучения');
  } finally {
    setLoading(false);
  }
};
'''
    
    print("✅ Исправление File Manager готово")
    return fm_fix

# Исправление 4: Анализ тендера
def fix_tender_analysis():
    print("🔧 Исправляем анализ тендера...")
    
    tender_fix = '''
// В обработчике анализа тендера:
const handleTenderAnalysis = async (values) => {
  const tenderData = {
    tender_data: values.tender_file || values.tender_text || values.tender_url,
    analysis_type: values.analysis_type || 'full',
    budget_limit: values.budget_limit || 0
  };
  
  if (!tenderData.tender_data) {
    message.error('Загрузите файл тендера или укажите данные');
    return;
  }
  
  // ... rest of implementation
};
'''
    
    print("✅ Исправление анализа тендера готово")  
    return tender_fix

# Исправление 5: Telegram бот
def fix_telegram_bot():
    print("🔧 Проверяем Telegram бот...")
    
    # Проверим конфигурацию бота в .env
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.read()
            
        if "TELEGRAM_BOT_TOKEN" in env_content:
            print("✅ Telegram токен найден в .env")
        else:
            print("❌ Telegram токен не найден в .env")
    
    bot_fix = '''
# Исправление в core/bldr_api.py для Telegram:
# Убедиться что WebSocket правильно обрабатывает Telegram запросы

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook"""
    try:
        data = await request.json()
        
        # Обработка сообщения
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            
            # Переслать в RAG систему
            response = await process_telegram_query(text, chat_id)
            
            return {"status": "ok"}
            
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return {"status": "error"}
'''
    
    print("✅ Исправление Telegram бота готово")
    return bot_fix

def main():
    print("🚀 Исправление проблем фронтенда Bldr Empire v2")
    print("=" * 60)
    
    fixes = {
        "chat_history": fix_chat_history(),
        "protools_auth": fix_protools_auth(), 
        "file_manager": fix_file_manager(),
        "tender_analysis": fix_tender_analysis(),
        "telegram_bot": fix_telegram_bot()
    }
    
    # Сохраняем исправления в файл
    with open("frontend_fixes.json", 'w', encoding='utf-8') as f:
        json.dump(fixes, f, ensure_ascii=False, indent=2)
    
    print("\n💾 Исправления сохранены в frontend_fixes.json")
    print("\n📝 Следующие шаги:")
    print("1. Примените исправления к соответствующим файлам")
    print("2. Перезапустите фронтенд: npm run dev") 
    print("3. Проверьте Telegram бот конфигурацию")
    print("4. Убедитесь что токены сохраняются в localStorage")
    
    print("\n🔧 Приоритетные исправления:")
    print("- Добавить инициализацию токена в App.tsx")
    print("- Убрать обязательные поля в продвинутых письмах")
    print("- Исправить custom_dir в FileManager")
    print("- Добавить tender_data в анализ тендера")

if __name__ == "__main__":
    main()