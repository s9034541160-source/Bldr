# 🌐 RAG API Documentation

## Обзор

RAG API Server предоставляет REST API для интеграции мощного RAG-тренера с фронтендом Bldr. API позволяет:

- **Анализировать** отдельные файлы без сохранения в БД
- **Дообучать** систему на новых файлах с сохранением в БД
- **Анализировать проекты** (пакеты файлов)
- **Получать информацию** о файлах и директориях

## 🚀 Запуск API Server

```bash
python rag_api_server.py
```

API будет доступен по адресу: `http://localhost:5000`

## 📡 Endpoints

### 1. Проверка здоровья
```http
GET /api/health
```

**Ответ:**
```json
{
  "status": "healthy",
  "rag_trainer_loaded": true,
  "timestamp": 1698765432.123
}
```

### 2. Анализ одного файла
```http
POST /api/analyze-file
Content-Type: application/json

{
  "file_path": "/path/to/document.pdf",
  "save_to_db": false
}
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "file_name": "document.pdf",
    "doc_type": "snip",
    "metadata": {
      "date_approved": "2023-01-15",
      "document_number": "СНиП 2.01.07-85*",
      "organization": "Минстрой России"
    },
    "chunks_count": 15,
    "processing_time": 2.34,
    "saved_to_db": false
  },
  "message": "File analyzed successfully"
}
```

### 3. Анализ проекта
```http
POST /api/analyze-project
Content-Type: application/json

{
  "file_paths": [
    "/path/to/doc1.pdf",
    "/path/to/doc2.pdf",
    "/path/to/doc3.pdf"
  ]
}
```

**Ответ:**
```json
{
  "success": true,
  "data": [
    {
      "file_name": "doc1.pdf",
      "doc_type": "snip",
      "confidence": 0.95,
      "key_metadata": {
        "date_approved": "2023-01-15",
        "document_number": "СНиП 2.01.07-85*"
      },
      "chunk_count": 15,
      "status": "success"
    },
    {
      "file_name": "doc2.pdf",
      "doc_type": "gost",
      "confidence": 0.88,
      "key_metadata": {
        "date_approved": "2023-02-20",
        "document_number": "ГОСТ 12345-2020"
      },
      "chunk_count": 12,
      "status": "success"
    }
  ],
  "message": "Project analyzed successfully (2 files)"
}
```

### 4. Дообучение на файле
```http
POST /api/train-file
Content-Type: application/json

{
  "file_path": "/path/to/new_document.pdf"
}
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "file_name": "new_document.pdf",
    "doc_type": "sp",
    "chunks_count": 20,
    "saved_to_db": true
  },
  "message": "File trained successfully and saved to database"
}
```

### 5. Информация о файле
```http
GET /api/get-file-info?file_path=/path/to/document.pdf
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "file_name": "document.pdf",
    "file_path": "/path/to/document.pdf",
    "file_size": 2048576,
    "file_extension": ".pdf",
    "exists": true
  }
}
```

### 6. Список файлов
```http
GET /api/list-files?directory=/path/to/directory&extension=.pdf
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "file_name": "doc1.pdf",
        "file_path": "/path/to/directory/doc1.pdf",
        "file_size": 1024000,
        "directory": "/path/to/directory"
      }
    ],
    "count": 1,
    "directory": "/path/to/directory",
    "extension": ".pdf"
  }
}
```

## 🔧 Интеграция с фронтендом

### JavaScript примеры

#### Анализ файла
```javascript
async function analyzeFile(filePath) {
  const response = await fetch('/api/analyze-file', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      file_path: filePath,
      save_to_db: false
    })
  });
  
  const result = await response.json();
  return result;
}
```

#### Анализ проекта
```javascript
async function analyzeProject(filePaths) {
  const response = await fetch('/api/analyze-project', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      file_paths: filePaths
    })
  });
  
  const result = await response.json();
  return result;
}
```

#### Дообучение на файле
```javascript
async function trainOnFile(filePath) {
  const response = await fetch('/api/train-file', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      file_path: filePath
    })
  });
  
  const result = await response.json();
  return result;
}
```

## 🎯 Сценарии использования

### 1. Анализ проекта
```javascript
// Пользователь загружает несколько файлов проекта
const projectFiles = [
  '/uploads/project/doc1.pdf',
  '/uploads/project/doc2.pdf',
  '/uploads/project/doc3.pdf'
];

// Анализируем проект
const analysis = await analyzeProject(projectFiles);

// Показываем результаты пользователю
analysis.data.forEach(file => {
  console.log(`${file.file_name}: ${file.doc_type} (${file.confidence})`);
});
```

### 2. Дообучение на новом документе
```javascript
// Пользователь загружает новый документ
const newDocument = '/uploads/new_document.pdf';

// Дообучаем систему
const training = await trainOnFile(newDocument);

if (training.success) {
  console.log('Документ успешно добавлен в базу знаний!');
  console.log(`Тип: ${training.data.doc_type}`);
  console.log(`Чанков: ${training.data.chunks_count}`);
}
```

### 3. Быстрый анализ файла
```javascript
// Пользователь хочет быстро проанализировать файл
const fileToAnalyze = '/uploads/unknown_document.pdf';

// Анализируем без сохранения
const analysis = await analyzeFile(fileToAnalyze);

if (analysis.success) {
  console.log(`Тип документа: ${analysis.data.doc_type}`);
  console.log(`Метаданные:`, analysis.data.metadata);
}
```

## ⚡ Производительность

- **Анализ файла**: 2-5 секунд (зависит от размера)
- **Дообучение**: 3-8 секунд (включая сохранение в БД)
- **Анализ проекта**: 5-15 секунд на файл

## 🛡️ Безопасность

- Все файлы проверяются на существование
- Валидация путей к файлам
- Обработка ошибок и исключений
- Логирование всех операций

## 📊 Мониторинг

API предоставляет детальную информацию о:
- Времени обработки
- Количестве чанков
- Типе документа
- Метаданных
- Статусе операций

## 🔄 Интеграция с CrewAI

API может использоваться агентами CrewAI для:
- Автоматического анализа документов
- Дообучения системы на новых данных
- Получения информации о файлах
- Анализа проектов

## 🚀 Готовность к продакшену

API готов для интеграции с фронтендом Bldr и может быть развернут в продакшене с минимальными изменениями.
