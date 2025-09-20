# Интеграция WebSocket с RAG Trainer

## Архитектура интеграции

Для полноценной интеграции WebSocket обновлений с процессом обучения RAG, необходимо модифицировать `scripts/bldr_rag_trainer.py` для отправки реальных обновлений этапов.

## Модификация BldrRAGTrainer

### Добавление WebSocket callback

В класс `BldrRAGTrainer` добавьте метод для отправки обновлений:

```python
# В scripts/bldr_rag_trainer.py

class BldrRAGTrainer:
    def __init__(self, base_dir=r'I:\docs\база', neo4j_uri='bolt://localhost:7687', neo4j_user='neo4j', neo4j_pass='bldr', qdrant_path='data/qdrant_db', faiss_path='data/faiss_index.index', norms_db='data/norms_db', reports_dir='data/reports'):
        # ... существующий код ...
        self.websocket_callback = None
    
    def set_websocket_callback(self, callback):
        """Установка callback функции для отправки WebSocket обновлений"""
        self.websocket_callback = callback
    
    async def send_stage_update(self, stage, log, progress=0):
        """Отправка обновления этапа через WebSocket"""
        if self.websocket_callback:
            try:
                await self.websocket_callback(stage, log, progress)
            except Exception as e:
                print(f"Ошибка отправки WebSocket обновления: {e}")
```

### Модификация этапов обучения

В каждый метод этапа добавьте вызов обновления:

```python
def _stage1_initial_validation(self, file_path: str) -> Dict[str, Any]:
    # ... существующий код ...
    log = f'✅ [Stage 1/14] Initial validation: {log}'
    print(log)
    
    # Отправка WebSocket обновления
    if self.websocket_callback:
        asyncio.create_task(self.send_stage_update("1/14", log, 7))
    
    return {'exists': exists, 'size': size, 'can_read': can_read, 'log': log}

def _stage2_duplicate_checking(self, file_path: str) -> Dict[str, Any]:
    # ... существующий код ...
    log = f'✅ [Stage 2/14] Duplicate check: {log}'
    print(log)
    
    # Отправка WebSocket обновления
    if self.websocket_callback:
        asyncio.create_task(self.send_stage_update("2/14", log, 14))
    
    return {'is_duplicate': is_duplicate, 'file_hash': file_hash, 'log': log}

# Повторите для всех 14 этапов с соответствующими номерами и процентами прогресса
```

### Модификация метода train()

В методе `train()` установите callback:

```python
def train(self):
    # Установка WebSocket callback если доступен
    # Это будет установлено из API при запуске обучения
    
    # ... остальной код обучения ...
```

## Интеграция с FastAPI

В `core/bldr_api.py` модифицируйте функцию запуска обучения:

```python
# В core/bldr_api.py

# Глобальная переменная для хранения callback функции
websocket_callback_func = None

# Функция для установки callback
def set_websocket_callback(callback):
    global websocket_callback_func
    websocket_callback_func = callback

# Функция для отправки обновлений
async def send_stage_update(stage: str, log: str, progress: int = 0):
    global websocket_callback_func
    message = json.dumps({
        "stage": stage,
        "log": log,
        "progress": progress
    })
    await manager.broadcast(message)

# Модифицированная функция обучения
async def run_training_with_updates():
    try:
        # Установка callback в trainer
        trainer.set_websocket_callback(send_stage_update)
        
        # Запуск реального обучения
        trainer.train()
        
        # Отправка завершения
        await send_stage_update("complete", "🎉 Обработка документа завершена успешно", 100)
        
    except Exception as e:
        await send_stage_update("error", f"Ошибка во время обучения: {str(e)}", 0)
```

## Реализация на стороне клиента (React)

React компонент уже реализован для работы с этими обновлениями:

```javascript
// В RAGModule.tsx

// Подключение к WebSocket
useEffect(() => {
  if (!socketRef.current) {
    socketRef.current = io('http://localhost:8000');
    socketRef.current.on('stage_update', (data: StageUpdate) => {
      setStageLogs(prev => [...prev, `✅ [Этап ${data.stage}] ${data.log}`]);
    });
  }
  
  return () => {
    if (socketRef.current) {
      socketRef.current.disconnect();
    }
  };
}, []);
```

## Тестирование интеграции

1. Запустите backend сервер:
   ```
   python core/bldr_api.py
   ```

2. Подключитесь к WebSocket:
   ```
   ws://localhost:8000/ws
   ```

3. Отправьте POST запрос на `/train`:
   ```
   curl -X POST http://localhost:8000/train
   ```

4. Наблюдайте за обновлениями этапов в реальном времени

## Преимущества интеграции

1. **Real-time обновления** - пользователь видит прогресс обучения в реальном времени
2. **Точная информация** - обновления отправляются непосредственно из процесса обучения
3. **Обратная связь** - пользователь получает информацию о каждом этапе пайплайна
4. **Интеграция с архитектурой** - соответствует 14-этапному симбиотическому подходу

## Совместимость

Интеграция сохраняет полную обратную совместимость с существующим кодом:
- Все существующие функции продолжают работать
- Новые функции добавляются без изменения существующей логики
- WebSocket обновления являются дополнительной функцией