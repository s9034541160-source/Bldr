# 🛠️ СТАНДАРТЫ РЕЗУЛЬТАТОВ TOOLS

## 🎯 ПРИНЦИП: УНИВЕРСАЛЬНЫЙ КОМПОНЕНТ

**НИКОГДА НЕ ПЕРЕСБИРАЙТЕ FRONTEND ИЗ-ЗА НОВОГО TOOL!**

Все tools должны возвращать **стандартизированные результаты**, которые автоматически отображаются универсальным компонентом `ToolResultDisplay`.

---

## 📋 СТАНДАРТНЫЕ ТИПЫ РЕЗУЛЬТАТОВ

### ✅ РАЗРЕШЕННЫЕ ТИПЫ (строгий ENUM):

```typescript
type ResultType = 
  | 'text'      // Текстовый результат
  | 'table'     // Табличные данные  
  | 'file'      // Файлы для скачивания
  | 'image'     // Изображения
  | 'chart'     // Графики/диаграммы
  | 'json'      // JSON данные
```

### ❌ ЗАПРЕЩЕННЫЕ ТИПЫ:

```typescript
// НЕ ДЕЛАЙТЕ ТАК!
'advanced_table'  // ❌ Используйте 'table' + metadata
'search_results'  // ❌ Используйте 'table' + metadata  
'rag_output'      // ❌ Используйте 'table' + metadata
'custom_format'   // ❌ Используйте базовый тип + metadata
```

---

## 🏗️ СТРУКТУРА РЕЗУЛЬТАТА

### ✅ ПРАВИЛЬНАЯ СТРУКТУРА:

```python
{
    "status": "success",
    "result_type": "table",  # ← БАЗОВЫЙ ТИП
    "result_title": "🔍 Результаты поиска",
    "result_table": [...],   # ← ДАННЫЕ
    "metadata": {           # ← "КВАРГИ" ДЛЯ КОМПОНЕНТА
        "columns": ["rank", "score", "title"],
        "sortable": True,
        "mode": "rag_search",
        "search_query": "сп 119"
    },
    "execution_time": 4.731
}
```

### ❌ НЕПРАВИЛЬНАЯ СТРУКТУРА:

```python
# НЕ ДЕЛАЙТЕ ТАК!
{
    "status": "success",
    "result_type": "advanced_table",  # ❌ Специфичный тип
    "data": {                        # ❌ Данные в data
        "results": [...]
    }
}
```

---

## 🎨 МЕТАДАННЫЕ ДЛЯ КОМПОНЕНТА

### 📊 ТАБЛИЦЫ:

```python
"metadata": {
    "columns": ["rank", "score", "title", "content"],  # Показать колонки
    "sortable": True,                                  # Включить сортировку
    "searchable": True,                                # Включить поиск
    "mode": "rag_search",                             # Режим отображения
    "highlight": ["content"],                         # Подсветка в колонках
    "actions": ["download", "view"]                    # Действия с записями
}
```

### 📝 ТЕКСТ:

```python
"metadata": {
    "format": "markdown",     # Формат текста
    "highlight": True,        # Подсветка синтаксиса
    "copyable": True,         # Кнопка копирования
    "downloadable": True      # Кнопка скачивания
}
```

### 📁 ФАЙЛЫ:

```python
"metadata": {
    "preview": True,          # Превью файлов
    "download_all": True,     # Скачать все
    "file_types": ["pdf", "docx"]  # Типы файлов
}
```

---

## 🔧 АВТОМАТИЧЕСКАЯ НОРМАЛИЗАЦИЯ

Компонент `ToolResultDisplay` **автоматически** нормализует результаты:

### ✅ АВТОМАТИЧЕСКИЕ ПРЕОБРАЗОВАНИЯ:

```typescript
// Tool вернул:
{
    "data": {
        "results": [...]
    }
}

// Компонент автоматически создаст:
{
    "result_table": [...],
    "result_type": "table"
}
```

### ✅ ПОДДЕРЖИВАЕМЫЕ ФОРМАТЫ:

```typescript
// Формат 1: Стандартный
{ "result_type": "table", "result_table": [...] }

// Формат 2: data.results  
{ "data": { "results": [...] } }

// Формат 3: data как массив
{ "data": [...] }

// Формат 4: data.content
{ "data": { "content": "text" } }
```

---

## 🚀 ПРИМЕРЫ РЕАЛИЗАЦИИ

### ✅ ПРАВИЛЬНЫЙ TOOL:

```python
def execute(query: str) -> Dict[str, Any]:
    results = search_database(query)
    
    return {
        "status": "success",
        "result_type": "table",  # ← БАЗОВЫЙ ТИП
        "result_title": f"🔍 Результаты поиска: {query}",
        "result_table": results,  # ← ДАННЫЕ
        "metadata": {             # ← "КВАРГИ"
            "mode": "rag_search",
            "search_query": query,
            "sortable": True
        },
        "execution_time": 4.731
    }
```

### ❌ НЕПРАВИЛЬНЫЙ TOOL:

```python
def execute(query: str) -> Dict[str, Any]:
    results = search_database(query)
    
    return {
        "status": "success",
        "result_type": "advanced_table",  # ❌ Специфичный тип
        "data": {                         # ❌ Данные в data
            "results": results
        }
    }
```

---

## 🎯 ПРАВИЛА ДЛЯ РАЗРАБОТЧИКОВ

### ✅ ОБЯЗАТЕЛЬНО:

1. **Используйте только базовые типы** (`text`, `table`, `file`, `image`, `chart`, `json`)
2. **Помещайте данные в стандартные поля** (`result_table`, `result_content`, `result_url`)
3. **Используйте `metadata` для специфики** (режимы, опции, "кварги")
4. **Тестируйте с универсальным компонентом**

### ❌ ЗАПРЕЩЕНО:

1. **Создавать новые типы** (`advanced_table`, `custom_format`)
2. **Помещать данные в `data`** (используйте стандартные поля)
3. **Требовать изменений в frontend** для нового tool
4. **Хардкодить специфичную логику** в компоненте

---

## 🎉 РЕЗУЛЬТАТ

**С универсальным компонентом:**
- ✅ **Новый tool** → работает сразу
- ✅ **Нет пересборки** frontend
- ✅ **Единый стандарт** для всех tools
- ✅ **Автоматическая нормализация** данных
- ✅ **Гибкость через metadata** ("кварги")

**БОЛЬШЕ НИКОГДА НЕ ПЕРЕСБИРАЙТЕ FRONTEND ИЗ-ЗА TOOL!** 🚀
