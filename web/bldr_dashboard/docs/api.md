# Интеграция с Bldr API

## Эндпоинты

### POST /train
Запуск процесса обучения RAG системы.

**Request:**
```json
{
  "base_dir": "string (optional)"
}
```

**Response:**
```json
{
  "status": "Train started background",
  "message": "14 stages symbiotism processing... logs via WebSocket if needed"
}
```

### POST /query
Выполнение семантического запроса к RAG системе.

**Request:**
```json
{
  "query": "string",
  "k": "number (optional, default: 5)"
}
```

**Response:**
```json
{
  "results": [
    {
      "chunk": "string",
      "meta": {
        "conf": "number",
        "entities": "object",
        "work_sequences": "array",
        "violations": "array"
      },
      "score": "number",
      "tezis": "string",
      "viol": "number"
    }
  ],
  "ndcg": "number"
}
```

### GET /metrics
Получение метрик обучения.

**Response:**
```json
{
  "total_chunks": "number",
  "avg_ndcg": "number",
  "coverage": "number",
  "conf": "number",
  "viol": "number",
  "entities": {
    "СП31": "number",
    "CL": "number",
    "FЗ": "number",
    "BIM": "number",
    "OVOS": "number",
    "LSR": "number"
  }
}
```

### POST /ai
Вызов AI с определенной ролью.

**Request:**
```json
{
  "prompt": "string",
  "model": "string (optional, default: deepseek/deepseek-r1-0528-qwen3-8b)"
}
```

**Response:**
```json
{
  "response": "string",
  "model": "string"
}
```

## WebSocket соединение

Для получения логов в реальном времени используется WebSocket соединение.

**Endpoint:** `/ws`

**События:**
- `stage_update` - обновление статуса этапа обучения
  ```json
  {
    "stage": "string",
    "log": "string"
  }
  ```

## Интеграция с 14-этапным пайплайном

Каждый этап пайплайна отражен в интерфейсе:
1. Валидация документа
2. Проверка на дубликаты
3. Извлечение текста
4. Определение типа документа
5. Структурный анализ
6. Извлечение кандидатов (Regex → Rubern)
7. Генерация разметки Rubern
8. Извлечение метаданных
9. Контроль качества
10. Тип-специфическая обработка
11. Извлечение рабочих последовательностей
12. Сохранение в Neo4j
13. Разбиение на чанки и генерация эмбеддингов
14. Сохранение в Qdrant

## Роли в системе

- **coordinator** (DeepSeek-R1-0528-Qwen3-8B) - планирование и координация
- **chief_engineer** (qwen2.5-vl-7b) - технический анализ
- **analyst** - финансовый анализ
- И другие специализированные роли