# 🔧 MCP Server for Yandex Browser + Cursor IDE

**Полноценная интеграция мониторинга ошибок Yandex Browser с Cursor IDE через MCP протокол**

## 🚀 Возможности

- ✅ **Мониторинг ошибок** - Захват всех типов ошибок в Yandex Browser
- ✅ **Интеграция с Cursor** - Прямая передача данных в Cursor IDE
- ✅ **Анализ производительности** - Отслеживание производительности веб-приложений
- ✅ **Автоматические отчеты** - Генерация отчетов об ошибках
- ✅ **Real-time мониторинг** - Мониторинг в реальном времени
- ✅ **Безопасность** - Защищенная передача данных

## 📦 Установка

### 1. Установка зависимостей

```bash
# Установка Node.js зависимостей
npm install --save @modelcontextprotocol/server express ws fs-extra chalk moment

# Или используйте готовый package.json
cp package-mcp-yandex.json package.json
npm install
```

### 2. Настройка конфигурации

```bash
# Создание директорий
mkdir -p logs config reports

# Копирование конфигурации
cp config/mcp-config.json config/
```

### 3. Запуск сервера

```bash
# Запуск MCP сервера
node mcp-yandex-browser-server.js

# Или в режиме разработки
npm run dev
```

## 🔧 Конфигурация

### Основные настройки (`config/mcp-config.json`)

```json
{
  "server": {
    "name": "Yandex Browser MCP Server",
    "version": "1.0.0",
    "port": 3000,
    "browserType": "yandex"
  },
  "errorCapture": {
    "enabled": true,
    "logLevel": "error",
    "maxLogSize": "10MB",
    "retentionDays": 30
  },
  "cursor": {
    "integration": true,
    "autoReport": true,
    "reportInterval": 5000
  }
}
```

### Переменные окружения

```bash
# Порт сервера
export MCP_SERVER_PORT=3000

# Тип браузера
export BROWSER_TYPE=yandex

# API ключ
export MCP_API_KEY=your-secret-key
```

## 🌐 Интеграция с веб-страницами

### 1. Подключение клиента

```html
<!-- Подключение MCP клиента -->
<script src="yandex-browser-client.js"></script>

<script>
// Автоматическая инициализация
// window.YandexBrowserMCP уже доступен
</script>
```

### 2. Ручная инициализация

```javascript
// Создание клиента с настройками
const mcpClient = new YandexBrowserMCPClient({
  serverUrl: 'http://localhost:3000',
  apiKey: 'your-api-key'
});

// Получение информации о сессии
const sessionInfo = mcpClient.getSessionInfo();
console.log('Session ID:', sessionInfo.sessionId);
console.log('Connected:', sessionInfo.isConnected);
```

## 🧪 Тестирование

### 1. Запуск тестовой страницы

```bash
# Откройте в Yandex Browser
open test-yandex-browser.html
```

### 2. Тестирование ошибок

Тестовая страница включает:

- **JavaScript ошибки** - ReferenceError, TypeError, SyntaxError
- **Сетевые ошибки** - Fetch, XHR, Timeout, CORS
- **Ошибки ресурсов** - Images, Scripts, CSS, iframes
- **Ошибки производительности** - Memory leaks, Long tasks

### 3. Мониторинг в реальном времени

```javascript
// Просмотр статуса подключения
setInterval(() => {
  const status = window.YandexBrowserMCP.getSessionInfo();
  console.log('MCP Status:', status);
}, 5000);
```

## 📊 API Endpoints

### Подключение к серверу

```http
POST /api/connect
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "sessionId": "session_1234567890_abc123",
  "browserInfo": {
    "userAgent": "Mozilla/5.0...",
    "url": "https://example.com",
    "timestamp": "2024-01-01T00:00:00.000Z"
  }
}
```

### Отправка ошибки

```http
POST /api/error
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "type": "JavaScript Error",
  "message": "ReferenceError: undefinedVariable is not defined",
  "stack": "at testFunction (script.js:10:5)",
  "url": "https://example.com",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "severity": "high"
}
```

### Пакетная отправка ошибок

```http
POST /api/errors/batch
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "errors": [
    { "type": "Error 1", "message": "..." },
    { "type": "Error 2", "message": "..." }
  ]
}
```

## 🔗 Интеграция с Cursor IDE

### 1. Настройка Cursor

```json
// settings.json в Cursor
{
  "mcp.servers": {
    "yandex-browser": {
      "command": "node",
      "args": ["mcp-yandex-browser-server.js"],
      "env": {
        "MCP_SERVER_PORT": "3000",
        "BROWSER_TYPE": "yandex"
      }
    }
  }
}
```

### 2. Команды Cursor

```javascript
// Получение ошибок
const errors = await cursor.mcp.getErrors();

// Очистка логов
await cursor.mcp.clearLogs();

// Получение конфигурации
const config = await cursor.mcp.getConfig();

// Обновление конфигурации
await cursor.mcp.updateConfig({
  errorCapture: { enabled: false }
});
```

## 📈 Мониторинг и отчеты

### 1. Логи ошибок

```bash
# Просмотр логов
tail -f logs/yandex-browser-errors.json

# Анализ ошибок
cat logs/yandex-browser-errors.json | jq '.[] | select(.severity == "high")'
```

### 2. Отчеты

```bash
# Генерация отчета
node generate-report.js

# Отправка отчета в Cursor
curl -X POST http://localhost:3000/api/report \
  -H "Authorization: Bearer your-api-key"
```

## 🛠️ Разработка

### Структура проекта

```
mcp-yandex-browser/
├── mcp-yandex-browser-server.js    # Основной сервер
├── yandex-browser-client.js        # Клиент для браузера
├── test-yandex-browser.html        # Тестовая страница
├── config/
│   └── mcp-config.json            # Конфигурация
├── logs/
│   └── yandex-browser-errors.json # Логи ошибок
├── reports/                        # Отчеты
└── package.json                   # Зависимости
```

### Добавление новых типов ошибок

```javascript
// В yandex-browser-client.js
setupCustomErrorHandlers() {
  // Ваш кастомный обработчик
  window.addEventListener('customError', (event) => {
    this.captureError({
      type: 'Custom Error',
      message: event.detail.message,
      data: event.detail.data
    });
  });
}
```

### Расширение API

```javascript
// В mcp-yandex-browser-server.js
this.server.on('customCommand', (command) => {
  switch (command.type) {
    case 'custom_action':
      this.handleCustomAction(command.data);
      break;
  }
});
```

## 🔒 Безопасность

### 1. API ключи

```javascript
// Генерация API ключа
const crypto = require('crypto');
const apiKey = crypto.randomBytes(32).toString('hex');
```

### 2. CORS настройки

```javascript
// В конфигурации
"security": {
  "allowedOrigins": [
    "http://localhost:3000",
    "https://yourdomain.com"
  ],
  "rateLimit": {
    "windowMs": 60000,
    "max": 100
  }
}
```

## 🚨 Устранение неполадок

### 1. Проблемы с подключением

```bash
# Проверка порта
netstat -an | grep 3000

# Проверка логов
tail -f logs/mcp-server.log
```

### 2. Проблемы с Cursor

```bash
# Перезапуск Cursor
cursor --restart

# Проверка MCP серверов
cursor.mcp.listServers()
```

### 3. Проблемы с браузером

```javascript
// Проверка клиента
console.log('MCP Client:', window.YandexBrowserMCP);
console.log('Session Info:', window.YandexBrowserMCP.getSessionInfo());
```

## 📚 Дополнительные ресурсы

- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [Cursor IDE Documentation](https://cursor.sh/docs)
- [Yandex Browser Developer Tools](https://browser.yandex.ru/help/)

## 🤝 Поддержка

Если у вас возникли проблемы:

1. Проверьте логи: `logs/mcp-server.log`
2. Убедитесь, что порт 3000 свободен
3. Проверьте конфигурацию: `config/mcp-config.json`
4. Перезапустите сервер: `npm start`

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.

---

**🎉 Готово! Теперь у вас есть полноценная интеграция мониторинга ошибок Yandex Browser с Cursor IDE!**
