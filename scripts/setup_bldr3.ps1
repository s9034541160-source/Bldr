param(
    [string[]]$PythonLaunchers = @("py -3.11", "C:\Users\papa\AppData\Local\Programs\Python\Python311\python.exe"),
    [string]$VenvName = ".venv",
    [string]$HuggingFaceToken = $env:HF_TOKEN,
    [switch]$SkipModelDownload,
    [switch]$SkipDockerStartup,
    [switch]$SkipFrontendInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Assert-Command {
    param([string]$Command, [string]$InstallHint)
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        throw "Команда '$Command' недоступна. $InstallHint"
    }
}

function Invoke-CommandChecked {
    param(
        [string]$Executable,
        [string[]]$Arguments,
        [string]$WorkingDirectory = $null
    )
    Write-Host ">> $Executable $($Arguments -join ' ')" -ForegroundColor DarkGray
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Executable
    $psi.Arguments = ($Arguments -join " ")
    if ($WorkingDirectory) { $psi.WorkingDirectory = $WorkingDirectory }
    $psi.RedirectStandardError = $false
    $psi.RedirectStandardOutput = $false
    $psi.UseShellExecute = $false
    $process = [System.Diagnostics.Process]::Start($psi)
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) {
        throw "Команда '$Executable $($Arguments -join ' ') ' завершилась с кодом $($process.ExitCode)"
    }
}

function Resolve-PythonLauncher {
    param([string[]]$Candidates)
    foreach ($candidate in $Candidates) {
        try {
            $version = & $candidate -c "import sys; print(sys.version.split()[0])" 2>$null
            if ($LASTEXITCODE -eq 0 -and $version.StartsWith("3.11")) {
                Write-Host "Использую Python $version через '$candidate'"
                return $candidate
            }
        } catch {
            continue
        }
    }
    throw "Не удалось найти подходящий Python 3.11. Укажите путь с помощью параметра -PythonLaunchers."
}

function Ensure-Venv {
    param([string]$Launcher, [string]$VenvPath)
    if (-not (Test-Path $VenvPath)) {
        Write-Step "Создание виртуального окружения ($VenvPath)"
        Invoke-CommandChecked $Launcher @("-m","venv",$VenvPath)
    } else {
        Write-Host "Виртуальное окружение уже существует ($VenvPath)"
    }
}

function Install-PythonDeps {
    param(
        [string]$PythonExe,
        [string]$RepoRoot
    )

    Write-Step "Обновление pip"
    Invoke-CommandChecked $PythonExe @("-m","pip","install","--upgrade","pip")

    Write-Step "Установка зависимостей backend"
    Invoke-CommandChecked $PythonExe @("-m","pip","install","-r","backend/requirements.txt") -WorkingDirectory $RepoRoot

    Write-Step "Проверка установленной версии PyTorch"
    $torchVersion = & $PythonExe "-c" "import importlib, pkgutil; import sys; 
try:
    import torch
    print(torch.__version__)
except Exception:
    sys.exit(1)"
    if ($LASTEXITCODE -eq 0 -and $torchVersion.Trim() -eq "2.8.0+cu126") {
        Write-Host "PyTorch 2.8.0+cu126 уже установлен — пропускаю переустановку."
    } else {
        Write-Step "Установка PyTorch стека с CUDA 12.6"
        Invoke-CommandChecked $PythonExe @(
            "-m","pip","install","--force-reinstall",
            "--index-url","https://download.pytorch.org/whl/cu126",
            "torch==2.8.0+cu126","torchvision==0.23.0+cu126","torchaudio==2.8.0+cu126"
        )
    }

    if (-not $env:CUDA_HOME) {
        $cudaPath = $env:CUDA_PATH
        if (-not $cudaPath) {
            $cudaPath = [Environment]::GetEnvironmentVariable("CUDA_PATH","Machine")
        }
        if ($cudaPath) {
            Write-Step "Экспорт CUDA_HOME из CUDA_PATH ($cudaPath)"
            $env:CUDA_HOME = $cudaPath
        } else {
            Write-Warning "CUDA_HOME и CUDA_PATH не заданы. flash-attn может не собраться; установите CUDA Toolkit и задайте переменную вручную."
        }
    }

    Write-Step "Установка qdrant-client без gRPC зависимостей"
    Invoke-CommandChecked $PythonExe @("-m","pip","install","qdrant-client==1.7.0","--no-deps")

    Write-Step "Установка зависимостей DeepSeek-OCR"
    Invoke-CommandChecked $PythonExe @("-m","pip","install","transformers==4.57.1","tokenizers==0.22.1","einops","addict","easydict")

    $flashAttnCheck = & $PythonExe "-c" "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('flash_attn') else 1)"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "flash-attn уже установлен — пропускаю сборку."
    } else {
        try {
            Invoke-CommandChecked $PythonExe @("-m","pip","install","flash-attn==2.7.3","--no-build-isolation")
        } catch {
            Write-Warning "Не удалось установить flash-attn (возможно, нет CUDA build toolchain). Пропускаю: $_"
        }
    }
    Invoke-CommandChecked $PythonExe @("-m","pip","install","huggingface_hub[cli]")
}

function Download-DeepSeekModel {
    param(
        [string]$PythonExe,
        [string]$RepoRoot,
        [string]$Token = $null
    )

    if ($Token) {
        Write-Step "Аутентификация в HuggingFace"
        $env:HF_TOKEN = $Token
        try {
            $loginScript = "from huggingface_hub import HfFolder; HfFolder.save_token('$Token')"
            Invoke-CommandChecked $PythonExe @("-c","""$loginScript""")
        } catch {
            Write-Warning "Не удалось сохранить токен через huggingface_hub. Продолжаю с переменной окружения HF_TOKEN: $_"
        }
    } else {
        Write-Host "HF токен не указан. Предполагаю, что модель общедоступна."
    }

    $targetDir = Join-Path $RepoRoot "models\deepseek-ocr"
    if (-not (Test-Path $targetDir)) {
        Write-Step "Загрузка модели DeepSeek-OCR (может занять время)"
        New-Item -ItemType Directory -Path $targetDir | Out-Null
        $escapedDir = $targetDir -replace '\\','\\\\'
        $downloadScript = "from huggingface_hub import snapshot_download; snapshot_download(repo_id='deepseek-ai/DeepSeek-OCR', local_dir=r'$escapedDir', local_dir_use_symlinks=False, token='$Token')"
        Invoke-CommandChecked $PythonExe @("-c","""$downloadScript""")
    } else {
        Write-Host "Каталог с моделью уже существует ($targetDir) — пропускаю загрузку."
    }
}

function Start-DockerServices {
    param([string]$RepoRoot)
    Write-Step "Запуск инфраструктурных сервисов (docker compose)"
    try {
        Invoke-CommandChecked "docker" @("compose","up","-d","redis","postgres","minio","qdrant","neo4j") -WorkingDirectory $RepoRoot
    } catch {
        Write-Warning "Не удалось запустить docker compose. Убедитесь, что Docker Desktop запущен и повторите команду вручную."
        throw
    }
}

function Start-Backend {
    param([string]$PythonExe, [string]$RepoRoot)
    Write-Step "Старт backend (uvicorn)"
    Start-Process $PythonExe "-m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload" -WorkingDirectory $RepoRoot
}

function Start-Celery {
    param([string]$VenvPath, [string]$RepoRoot)
    Write-Step "Старт Celery воркера"
    $celery = Join-Path $VenvPath "Scripts\celery.exe"
    Start-Process $celery "-A backend.tasks worker -l info -Q bldr_default,documents,processes,monitoring,models" -WorkingDirectory $RepoRoot
}

function Setup-Frontend {
    param([string]$RepoRoot, [switch]$SkipInstall)
    $frontendDir = Join-Path $RepoRoot "frontend"
    Assert-Command -Command "npm" -InstallHint "Установите Node.js (https://nodejs.org/) и повторите."

    $npmExecutable = "npm.cmd"
    if (-not $SkipInstall) {
        Write-Step "Установка npm зависимостей"
        Invoke-CommandChecked "cmd.exe" @("/c","npm","install") -WorkingDirectory $frontendDir
    } else {
        Write-Host "Пропускаю npm install (задан Switch)."
    }

    Write-Step "Старт npm run dev"
    Start-Process $npmExecutable "run dev" -WorkingDirectory $frontendDir
}

function Summarize {
    param([string]$RepoRoot)
    Write-Host "`n===  Запуск завершён  ===" -ForegroundColor Green
    Write-Host "Backend: http://localhost:8000"
    Write-Host "Frontend: http://localhost:3000"
    Write-Host "Swagger: http://localhost:8000/api/docs"
    Write-Host "Celery, backend и frontend запущены в отдельных окнах/процессах."
    Write-Host "Для остановки: закройте соответствующие процессы (или выполните docker compose down)."
}

# --- основной сценарий ---

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repoRoot $VenvName
$pythonExe = Join-Path $venvPath "Scripts\python.exe"

# Шаги
Write-Step "Поиск интерпретатора Python 3.11"
$pythonLauncher = Resolve-PythonLauncher -Candidates $PythonLaunchers

Ensure-Venv -Launcher $pythonLauncher -VenvPath $venvPath
Install-PythonDeps -PythonExe $pythonExe -RepoRoot $repoRoot

if (-not $SkipModelDownload) {
    Download-DeepSeekModel -PythonExe $pythonExe -RepoRoot $repoRoot -Token $HuggingFaceToken
} else {
    Write-Host "Пропускаю загрузку модели (опция --SkipModelDownload)."
}

if (-not $SkipDockerStartup) {
    Assert-Command -Command "docker" -InstallHint "Установите Docker Desktop: https://www.docker.com/products/docker-desktop/"
    Start-DockerServices -RepoRoot $repoRoot
} else {
    Write-Host "Пропускаю запуск docker compose."
}

Start-Backend -PythonExe $pythonExe -RepoRoot $repoRoot
Start-Celery -VenvPath $venvPath -RepoRoot $repoRoot

Setup-Frontend -RepoRoot $repoRoot -SkipInstall:$SkipFrontendInstall
Summarize -RepoRoot $repoRoot

