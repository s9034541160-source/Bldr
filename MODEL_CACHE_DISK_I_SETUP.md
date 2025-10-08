# 🚀 Настройка загрузки моделей на диск I:\

## 📋 Обзор

Этот гайд поможет настроить загрузку всех моделей (Hugging Face, LLM, VLM) на диск `I:\` вместо системного диска `C:\`.

## 🎯 Преимущества

- **Экономия места на C:\**: Модели занимают 10-50GB
- **Производительность**: Диск I:\ может быть быстрее для больших файлов
- **Организация**: Все модели в одном месте
- **Безопасность**: Не засоряем системный диск

## 🔧 Способы настройки

### **Способ 1: Автоматическая настройка (Рекомендуется)**

#### **A. PowerShell скрипт (Windows)**
```powershell
# Запустите от имени администратора
.\setup_model_cache_disk_i.ps1
```

#### **B. Batch скрипт (Windows)**
```cmd
# Запустите от имени администратора
.\setup_model_cache_disk_i.bat
```

### **Способ 2: Ручная настройка**

#### **A. Переменные окружения**
Установите следующие переменные окружения:

```bash
# Hugging Face кэш
HF_HOME=I:\huggingface_cache
TRANSFORMERS_CACHE=I:\huggingface_cache
HF_DATASETS_CACHE=I:\huggingface_cache

# RAG-тренер кэш
LLM_CACHE_DIR=I:\models_cache
```

#### **B. Создание папок**
```cmd
mkdir I:\huggingface_cache
mkdir I:\models_cache
```

## 📁 Структура папок на диске I:\

```
I:\
├── huggingface_cache\          # Кэш Hugging Face
│   ├── models\                 # Модели (Qwen, RuT5, LayoutLMv3)
│   ├── datasets\               # Даты
│   └── tokenizers\            # Токенизаторы
└── models_cache\               # Кэш RAG-тренера
    ├── workhorse\              # Qwen3-8B
    ├── extraction\             # RuT5
    └── vlm\                    # LayoutLMv3
```

## 🔍 Проверка настройки

### **1. Проверка переменных окружения**
```cmd
echo %HF_HOME%
echo %TRANSFORMERS_CACHE%
echo %LLM_CACHE_DIR%
```

### **2. Проверка папок**
```cmd
dir I:\huggingface_cache
dir I:\models_cache
```

### **3. Тест загрузки модели**
```python
# test_model_loading.py
import os
from transformers import AutoTokenizer

print("Переменные окружения:")
print(f"HF_HOME: {os.environ.get('HF_HOME', 'НЕ УСТАНОВЛЕНА')}")
print(f"TRANSFORMERS_CACHE: {os.environ.get('TRANSFORMERS_CACHE', 'НЕ УСТАНОВЛЕНА')}")

# Тест загрузки токенизатора
tokenizer = AutoTokenizer.from_pretrained("microsoft/layoutlmv3-base")
print("✅ Модель загружена успешно!")
```

## 🚀 Использование в RAG-тренере

### **1. Автоматическая настройка**
RAG-тренер автоматически использует переменные окружения:

```python
# В workhorse_llm_ensemble.py
config = WorkhorseLLMConfig.from_env()  # Автоматически загружает настройки
```

### **2. Ручная настройка**
```python
# В enterprise_rag_trainer_full.py
config = WorkhorseLLMConfig(
    cache_dir="I:/models_cache",
    # ... другие настройки
)
```

## 📊 Размеры моделей

| Модель | Размер | Расположение |
|--------|--------|--------------|
| **Qwen3-8B** | ~15GB | `I:\huggingface_cache\models\Qwen` |
| **RuT5** | ~3GB | `I:\huggingface_cache\models\ai-forever` |
| **LayoutLMv3** | ~1.5GB | `I:\huggingface_cache\models\microsoft` |
| **SBERT** | ~1GB | `I:\huggingface_cache\models\sentence-transformers` |

**Общий размер**: ~20-25GB на диске I:\

## 🔧 Устранение проблем

### **Проблема 1: Переменные не применяются**
**Решение**: Перезапустите терминал/IDE

### **Проблема 2: Нет прав на создание папок**
**Решение**: Запустите скрипт от имени администратора

### **Проблема 3: Модели все еще загружаются на C:\**
**Решение**: Проверьте переменные окружения:
```cmd
set | findstr HF_
set | findstr LLM_
```

### **Проблема 4: Ошибка доступа к диску I:\**
**Решение**: Убедитесь, что диск I:\ доступен и имеет достаточно места

## 🎯 Результат

После настройки:
- ✅ Все модели загружаются на диск I:\
- ✅ Системный диск C:\ остается свободным
- ✅ RAG-тренер работает быстрее
- ✅ Легко управлять моделями

## 📝 Дополнительные настройки

### **Очистка кэша**
```cmd
# Очистка Hugging Face кэша
rmdir /s I:\huggingface_cache

# Очистка RAG-тренер кэша
rmdir /s I:\models_cache
```

### **Перенос существующих моделей**
```cmd
# Перенос с C:\ на I:\
xcopy "C:\Users\%USERNAME%\.cache\huggingface" "I:\huggingface_cache" /E /I /H /Y
```

## 🎉 Готово!

Теперь все модели будут загружаться на диск I:\ вместо C:\
