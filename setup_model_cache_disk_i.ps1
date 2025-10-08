# 🚀 Настройка загрузки моделей на диск I:\
# PowerShell скрипт для надежной настройки переменных окружения

Write-Host "🚀 Настройка загрузки моделей на диск I:\" -ForegroundColor Green
Write-Host ""

# Создаем папки на диске I:\
Write-Host "Создание папок для кэша моделей..." -ForegroundColor Yellow
$folders = @(
    "I:\huggingface_cache",
    "I:\models_cache"
)

foreach ($folder in $folders) {
    if (!(Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force
        Write-Host "✅ Создана папка: $folder" -ForegroundColor Green
    } else {
        Write-Host "✅ Папка уже существует: $folder" -ForegroundColor Green
    }
}

Write-Host ""

# Устанавливаем переменные окружения для Hugging Face
Write-Host "Установка переменных окружения для Hugging Face..." -ForegroundColor Yellow

$envVars = @{
    "HF_HOME" = "I:\huggingface_cache"
    "TRANSFORMERS_CACHE" = "I:\huggingface_cache"
    "HF_DATASETS_CACHE" = "I:\huggingface_cache"
    "LLM_CACHE_DIR" = "I:\models_cache"
}

foreach ($var in $envVars.GetEnumerator()) {
    [Environment]::SetEnvironmentVariable($var.Key, $var.Value, "User")
    Write-Host "✅ Установлена переменная: $($var.Key)=$($var.Value)" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎉 Настройка завершена!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 ВАЖНО: Перезапустите терминал для применения переменных окружения" -ForegroundColor Cyan
Write-Host "📝 Все модели будут загружаться на диск I:\ вместо C:\" -ForegroundColor Cyan
Write-Host ""

# Проверяем текущие переменные
Write-Host "Текущие переменные окружения:" -ForegroundColor Yellow
Write-Host "HF_HOME: $env:HF_HOME"
Write-Host "TRANSFORMERS_CACHE: $env:TRANSFORMERS_CACHE"
Write-Host "HF_DATASETS_CACHE: $env:HF_DATASETS_CACHE"
Write-Host "LLM_CACHE_DIR: $env:LLM_CACHE_DIR"
Write-Host ""

Read-Host "Нажмите Enter для завершения"
