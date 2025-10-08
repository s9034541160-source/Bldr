# Установка Poppler для VLM

## Проблема
```
VLM table extraction failed: Unable to get page count. Is poppler installed and in PATH?
```

## Решение

### Вариант 1: Скачать вручную
1. Перейдите на https://github.com/oschwartz10612/poppler-windows/releases
2. Скачайте последнюю версию (например, `poppler-23.08.0-0.tar.xz`)
3. Распакуйте в `C:\poppler`
4. Добавьте `C:\poppler\Library\bin` в PATH

### Вариант 2: Через conda (если установлен)
```bash
conda install -c conda-forge poppler
```

### Вариант 3: Через pip (альтернатива)
```bash
pip install pdf2image[poppler]
```

## Проверка установки
```bash
pdftoppm -h
```

## После установки
Перезапустите RAG тренер:
```bash
.\rag.bat
```

## Примечание
Poppler нужен для VLM анализа PDF файлов. Без него VLM функции будут работать в fallback режиме.
