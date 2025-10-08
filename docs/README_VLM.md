# 🚀 ENTERPRISE RAG 3.0: Vision-Language Model (VLM) Support

## 📋 Обзор

VLM поддержка добавляет возможность анализа PDF документов как изображений, что значительно улучшает извлечение таблиц, формул и структурированного контента.

## 🎯 Возможности

### ✅ **Что умеет VLM:**
- **Анализ PDF как изображений** - конвертация в изображения с высоким DPI
- **Извлечение таблиц** - обнаружение таблиц через компьютерное зрение
- **Структурный анализ** - понимание макета документа
- **Классификация контента** - определение типов таблиц и списков
- **Контекстуализация** - связь таблиц с родительскими секциями

### 🔧 **Технические детали:**
- **BLIP** для описания изображений
- **LayoutLMv3** для анализа структуры документов
- **OpenCV** для обработки изображений
- **Tesseract** для OCR
- **PDF2Image** для конвертации PDF

## 📦 Установка

### 1. **Автоматическая установка:**
```bash
python install_vlm.py
```

### 2. **Ручная установка:**
```bash
pip install -r requirements_vlm.txt
```

### 3. **Проверка установки:**
```python
from vlm_processor import VLMProcessor

vlm = VLMProcessor()
if vlm.is_available():
    print("✅ VLM ready!")
else:
    print("❌ VLM not available")
```

## 🚀 Использование

### **В RAG тренере:**
VLM автоматически активируется для PDF файлов:

```python
# В enterprise_rag_trainer_full.py
if self.vlm_available and self._current_file_path.endswith('.pdf'):
    vlm_analysis = self.vlm_processor.analyze_document_structure(self._current_file_path)
    vlm_tables = vlm_analysis.get('tables', [])
```

### **Прямое использование:**
```python
from vlm_processor import VLMProcessor

vlm = VLMProcessor()

# Анализ PDF документа
analysis = vlm.analyze_document_structure("document.pdf")
tables = analysis['tables']

# Извлечение таблиц
tables = vlm.extract_tables_from_pdf("document.pdf")
```

## 📊 Результаты VLM

### **Структурированные метаданные:**
```json
{
    "tables": [
        {
            "page": 1,
            "position": [100, 200, 300, 150],
            "content": "Таблица с данными...",
            "confidence": 0.85,
            "detection_method": "VLM_LAYOUT",
            "metadata": {
                "data_type": "TABLE",
                "structured": true,
                "vlm_processed": true
            }
        }
    ],
    "vlm_available": true,
    "analysis_method": "sbert_semantic_vlm"
}
```

## ⚙️ Конфигурация

### **Устройства:**
- **CUDA** - для NVIDIA GPU (рекомендуется)
- **MPS** - для Apple Silicon
- **CPU** - fallback режим

### **Настройки:**
```python
# В vlm_processor.py
vlm = VLMProcessor(device="cuda")  # или "cpu", "mps", "auto"
```

## 🔧 Требования

### **Системные:**
- Python 3.8+
- 8GB+ RAM (рекомендуется 16GB+)
- GPU с 4GB+ VRAM (опционально)

### **Зависимости:**
- PyTorch 2.0+
- Transformers 4.30+
- OpenCV 4.8+
- PDF2Image 1.16+
- Tesseract OCR

## 🚨 Troubleshooting

### **Проблема: CUDA out of memory**
```python
# Решение: используйте CPU
vlm = VLMProcessor(device="cpu")
```

### **Проблема: Tesseract not found**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-rus

# Windows
# Скачайте с https://github.com/UB-Mannheim/tesseract/wiki
```

### **Проблема: PDF2Image fails**
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows
# Установите poppler-utils
```

## 📈 Производительность

### **Без VLM (Fallback):**
- Только regex извлечение таблиц
- Базовая структурная экстракция
- Быстрая обработка

### **С VLM:**
- Полный анализ изображений
- Высокая точность извлечения таблиц
- Медленнее, но качественнее

## 🎯 Рекомендации

1. **Для больших документов** - используйте GPU
2. **Для быстрой обработки** - отключите VLM
3. **Для максимальной точности** - включите VLM + GPU
4. **Для экономии ресурсов** - используйте CPU fallback

## 🔮 Будущие улучшения

- **Формулы** - извлечение математических выражений
- **Диаграммы** - анализ схем и графиков  
- **Многоязычность** - поддержка других языков
- **Оптимизация** - ускорение обработки
