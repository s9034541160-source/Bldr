# SuperBuilder Tools API 🏗️

REST API для инструментов анализа строительных проектов с поддержкой загрузки файлов, асинхронной обработки и real-time уведомлений.

## 📋 Возможности

### 🔧 Инструменты анализа
- **Анализ смет**: Загрузка и анализ сметной документации (XLS, XLSX, PDF, CSV)
- **Анализ изображений**: Обработка чертежей, планов и фотографий (JPG, PNG, TIFF, PDF) 
- **Анализ документов**: Обработка проектной документации (PDF, DOC, DOCX, TXT)

### ⚡ Технические возможности
- **Асинхронная обработка**: Задачи выполняются в фоновом режиме
- **Real-time уведомления**: WebSocket для мониторинга статуса задач
- **REST API**: Полноценный API с документацией Swagger/OpenAPI
- **Управление задачами**: Создание, отслеживание, отмена и скачивание результатов
- **Веб интерфейс**: React фронтенд для удобной работы с инструментами

## 🚀 Быстрый старт

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Запуск сервера
```bash
# Запуск в режиме разработки
python main.py --debug

# Запуск в продакшене
python main.py --host 0.0.0.0 --port 8000
```

### Доступ к API
- **Основной интерфейс**: http://localhost:8000/
- **Swagger документация**: http://localhost:8000/docs
- **ReDoc документация**: http://localhost:8000/redoc
- **WebSocket**: ws://localhost:8000/ws/

## 📖 API Endpoints

### Анализ файлов

#### POST /api/tools/analyze/estimate
Анализ сметной документации
```bash
curl -X POST "http://localhost:8000/api/tools/analyze/estimate" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@estimate.xlsx" \
  -F 'params={"analysisType":"full","region":"moscow","includeGESN":true}'
```

#### POST /api/tools/analyze/images  
Анализ изображений и чертежей
```bash
curl -X POST "http://localhost:8000/api/tools/analyze/images" \
  -H "Content-Type: multipart/form-data" \
  -F "images=@plan.jpg" \
  -F 'params={"analysisType":"comprehensive","detectObjects":true}'
```

#### POST /api/tools/analyze/documents
Анализ документов
```bash
curl -X POST "http://localhost:8000/api/tools/analyze/documents" \
  -H "Content-Type: multipart/form-data" \
  -F "documents=@project.pdf" \
  -F 'params={"analysisType":"full","extractData":true}'
```

### Управление задачами

#### GET /api/tools/jobs/{job_id}/status
Получить статус задачи
```bash
curl "http://localhost:8000/api/tools/jobs/12345/status"
```

#### GET /api/tools/jobs/active
Список активных задач
```bash
curl "http://localhost:8000/api/tools/jobs/active"
```

#### POST /api/tools/jobs/{job_id}/cancel
Отменить задачу
```bash
curl -X POST "http://localhost:8000/api/tools/jobs/12345/cancel"
```

#### GET /api/tools/jobs/{job_id}/download
Скачать результат задачи
```bash
curl "http://localhost:8000/api/tools/jobs/12345/download" -o result.json
```

### Системная информация

#### GET /api/tools/health
Проверка работоспособности
```bash
curl "http://localhost:8000/api/tools/health"
```

#### GET /api/tools/info
Информация о доступных инструментах
```bash
curl "http://localhost:8000/api/tools/info"
```

## 🔗 WebSocket API

### Подключение
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/');

ws.onopen = function() {
    console.log('WebSocket connected');
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log('Message received:', message);
};
```

### Подписка на события
```javascript
// Подписка на все задачи
ws.send(JSON.stringify({
    type: 'subscribe',
    subscription_type: 'jobs'
}));

// Подписка на конкретную задачу
ws.send(JSON.stringify({
    type: 'subscribe',
    job_id: 'your-job-id-here'
}));

// Подписка на системные уведомления
ws.send(JSON.stringify({
    type: 'subscribe',
    subscription_type: 'notifications'
}));
```

### Типы сообщений
- `connection_established` - Подтверждение подключения
- `job_update` - Обновление статуса задачи
- `new_job` - Новая задача создана
- `job_completed` - Задача завершена
- `notification` - Системное уведомление
- `system_status` - Статус системы

## 📁 Структура проекта

```
backend/
├── main.py                 # Главное FastAPI приложение
├── requirements.txt        # Зависимости Python
├── README.md              # Эта документация
├── api/
│   ├── tools_api.py       # REST API endpoints для инструментов
│   └── websocket_server.py # WebSocket сервер
├── core/
│   └── agents/
│       └── coordinator_agent.py  # Координатор агентов
├── tools/
│   └── tools_adapter.py   # Адаптер инструментов
└── static/                # Статические файлы (опционально)
```

## 🛠️ React Frontend

Система включает React фронтенд с компонентами:

- `ToolsInterface.jsx` - Основной интерфейс с табами
- `EstimateAnalyzer.jsx` - Анализ смет
- `ImageAnalyzer.jsx` - Анализ изображений

### Подключение к API
```javascript
// Анализ сметы
const analyzeEstimate = async (files, params) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  formData.append('params', JSON.stringify(params));
  
  const response = await fetch('/api/tools/analyze/estimate', {
    method: 'POST',
    body: formData
  });
  
  return response.json();
};
```

## 🔧 Настройка и конфигурация

### Переменные окружения
```bash
# Опциональные настройки
export API_HOST=0.0.0.0
export API_PORT=8000
export DEBUG_MODE=false
export LOG_LEVEL=info

# Для продакшена
export CORS_ORIGINS=https://yourdomain.com
export MAX_FILE_SIZE=100MB
```

### Конфигурация CORS
Для продакшена обновите настройки CORS в `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Указать конкретные домены
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

## 📊 Мониторинг

### Health Check
```bash
curl "http://localhost:8000/health"
```

### Статистика WebSocket
```bash
# Отправить через WebSocket
{
  "type": "get_statistics"
}
```

### Очистка завершенных задач
```bash
curl -X DELETE "http://localhost:8000/api/tools/jobs/cleanup"
```

## 🧪 Тестирование

### Запуск тестов
```bash
# Установка test зависимостей
pip install pytest pytest-asyncio pytest-cov

# Запуск тестов
pytest

# Запуск с покрытием
pytest --cov=. --cov-report=html
```

### Пример теста
```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

## 📈 Производительность

### Рекомендации для продакшена
- Используйте Redis для хранения состояния задач
- Настройте Celery для распределенной обработки
- Используйте nginx как reverse proxy
- Настройте логирование и мониторинг

### Масштабирование
```bash
# Запуск несколько воркеров
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000

# С Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🤝 Интеграция с SuperBuilder

Система интегрирована с основными компонентами SuperBuilder:

- **Coordinator Agent**: Для оркестрации инструментов
- **Tools Adapter**: Для унифицированного доступа к инструментам
- **Meta-Tools System**: Для сложных многошаговых анализов

## 📝 Лицензия

Эта система является частью проекта SuperBuilder.

## 🆘 Поддержка

При возникновении проблем:
1. Проверьте логи сервера
2. Убедитесь, что все зависимости установлены
3. Проверьте доступность портов
4. Обратитесь к документации API в /docs