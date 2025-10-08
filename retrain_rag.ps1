# ПЕРЕОБРАБОТКА RAG - ПРИНУДИТЕЛЬНАЯ
# ===================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ПЕРЕОБРАБОТКА RAG - ПРИНУДИТЕЛЬНАЯ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверяем наличие Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python найден: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ОШИБКА: Python не найден!" -ForegroundColor Red
    Write-Host "Установите Python и добавьте его в PATH" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверяем наличие файлов
$requiredFiles = @(
    "enterprise_rag_trainer_full.py",
    "clear_rag_data.py"
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ ОШИБКА: Не найден файл $file" -ForegroundColor Red
        Read-Host "Нажмите Enter для выхода"
        exit 1
    }
}

Write-Host "✅ Все файлы найдены" -ForegroundColor Green
Write-Host ""

# Шаг 1: Очистка данных RAG
Write-Host "[1/3] Очистка данных RAG..." -ForegroundColor Yellow
try {
    python clear_rag_data.py
    if ($LASTEXITCODE -ne 0) {
        throw "Ошибка очистки данных RAG"
    }
    Write-Host "✅ Данные RAG очищены" -ForegroundColor Green
} catch {
    Write-Host "❌ ОШИБКА: Не удалось очистить данные RAG!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host ""

# Шаг 2: Запуск RAG-тренера
Write-Host "[2/3] Запуск RAG-тренера..." -ForegroundColor Yellow
try {
    python enterprise_rag_trainer_full.py
    if ($LASTEXITCODE -ne 0) {
        throw "Ошибка RAG-тренера"
    }
    Write-Host "✅ RAG-тренер завершен" -ForegroundColor Green
} catch {
    Write-Host "❌ ОШИБКА: Не удалось запустить RAG-тренер!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host ""

# Шаг 3: Завершение
Write-Host "[3/3] Завершено!" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ПЕРЕОБРАБОТКА RAG ЗАВЕРШЕНА УСПЕШНО!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Показываем статистику
if (Test-Path "processed_files.json") {
    $processedFiles = Get-Content "processed_files.json" | ConvertFrom-Json
    $totalFiles = $processedFiles.Count
    Write-Host "📊 Обработано файлов: $totalFiles" -ForegroundColor Green
}

Write-Host ""
Read-Host "Нажмите Enter для выхода"
