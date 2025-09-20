# Интеграция с существующим backend

## Совместимость с текущим API

Компонент полностью совместим с существующим Bldr API, определенным в `core/bldr_api.py`:

### Эндпоинты, которые уже реализованы в backend:

1. **POST /train** - запуск обучения RAG
2. **POST /query** - выполнение семантического запроса
3. **GET /metrics** - получение метрик обучения
4. **POST /ai** - вызов AI с определенной ролью

### Требуемые доработки backend:

Для полноценной работы компонента необходимо добавить WebSocket поддержку:

1. **WebSocket endpoint** - для передачи логов этапов в реальном времени
   ```python
   # В core/bldr_api.py добавить:
   from fastapi import WebSocket
   from fastapi.websockets import WebSocketDisconnect
   
   # WebSocket manager для управления соединениями
   class ConnectionManager:
       def __init__(self):
           self.active_connections: List[WebSocket] = []
   
       async def connect(self, websocket: WebSocket):
           await websocket.accept()
           self.active_connections.append(websocket)
   
       def disconnect(self, websocket: WebSocket):
           self.active_connections.remove(websocket)
   
       async def send_personal_message(self, message: str, websocket: WebSocket):
           await websocket.send_text(message)
   
       async def broadcast(self, message: str):
           for connection in self.active_connections:
               await connection.send_text(message)
   
   manager = ConnectionManager()
   
   @app.websocket("/ws")
   async def websocket_endpoint(websocket: WebSocket):
       await manager.connect(websocket)
       try:
           while True:
               data = await websocket.receive_text()
               # Обработка входящих сообщений если нужно
       except WebSocketDisconnect:
           manager.disconnect(websocket)
   
   # Функция для отправки логов этапов
   async def send_stage_update(stage: int, log: str):
       message = json.dumps({"stage": f"{stage}/14", "log": log})
       await manager.broadcast(message)
   ```

2. **Интеграция с этапами обучения** - для отправки логов в реальном времени:
   ```python
   # В scripts/bldr_rag_trainer.py в каждый этап добавить:
   # await send_stage_update(1, "Начальная валидация документа завершена успешно")
   # await send_stage_update(2, "Проверка на дубликаты завершена успешно - документ уникален")
   # и т.д. для всех 14 этапов
   ```

## Конфигурация прокси

Vite настроен на проксирование запросов к backend:

```javascript
// vite.config.ts
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
}
```

Это позволяет делать запросы к API как к относительным путям:
- `/train` вместо `http://localhost:8000/train`
- `/query` вместо `http://localhost:8000/query`

## CORS настройки

Backend уже настроен для работы с фронтендом:

```python
# core/bldr_api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

## Запуск системы

Для полноценной работы необходимо запустить:

1. **Backend (FastAPI)**:
   ```bash
   cd core
   python bldr_api.py
   ```

2. **Frontend (React + Vite)**:
   ```bash
   cd web/bldr_dashboard
   npm run dev
   ```

3. **Дополнительные сервисы**:
   - Neo4j для графовой базы данных
   - Qdrant для векторной базы данных

## Тестирование интеграции

После запуска всех сервисов:

1. Откройте `http://localhost:3000` в браузере
2. Перейдите на вкладку "Обучение"
3. Нажмите "Запустить Обучение"
4. Наблюдайте за логами этапов в реальном времени
5. Перейдите на вкладку "Дашборд" для просмотра метрик
6. Перейдите на вкладку "Запрос" для тестирования поиска

## Совместимость с существующими данными

Компонент работает с теми же данными, что и оригинальный Tkinter GUI:
- Использует те же файлы в `data/reports/`
- Работает с той же структурой Qdrant и Neo4j
- Совместим с форматом `processed_files.json`
- Использует те же модели и эмбеддинги

## Расширяемость

Компонент легко расширяем:
- Добавление новых вкладок через Tabs API Ant Design
- Расширение функциональности через services/api.ts
- Интеграция новых ролей через /ai endpoint
- Добавление новых метрик через /metrics endpoint