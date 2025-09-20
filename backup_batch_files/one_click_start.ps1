# Bldr Empire v2 - One-Click Startup Script
# PowerShell Version

Write-Host "==================================================" -ForegroundColor Green
Write-Host "   Bldr Empire v2 - One-Click Startup (PowerShell)" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
    Write-Host "[INFO] Running with administrator privileges" -ForegroundColor Green
} else {
    Write-Host "[WARN] Not running as administrator. Some features may not work correctly." -ForegroundColor Yellow
}

# Kill any existing processes on our ports
Write-Host "[INFO] Cleaning up existing processes..." -ForegroundColor Cyan
taskkill /F /IM redis-server.exe 2>$null
taskkill /F /IM java.exe 2>$null
taskkill /F /IM docker.exe 2>$null
taskkill /F /IM node.exe 2>$null
taskkill /F /IM python.exe 2>$null

Start-Sleep -Seconds 3

# Check and restore NTD base if needed
Write-Host "[INFO] Checking NTD base..." -ForegroundColor Cyan
if (!(Test-Path "I:\docs\clean_base\construction")) {
    Write-Host "[INFO] NTD base not found. Starting restoration process..." -ForegroundColor Cyan
    Start-Process -FilePath "python" -ArgumentList "restore_ntd.py" -WindowStyle Minimized
    Start-Sleep -Seconds 10
} else {
    Write-Host "[INFO] NTD base already exists" -ForegroundColor Green
}

# 1. Start Redis
Write-Host "[INFO] Starting Redis server..." -ForegroundColor Cyan
Set-Location -Path "$PSScriptRoot\redis"
Start-Process -FilePath "redis-server.exe" -ArgumentList "redis.windows.conf" -WindowStyle Minimized -PassThru
Set-Location -Path $PSScriptRoot
Start-Sleep -Seconds 5

# 2. Start Neo4j
Write-Host "[INFO] Starting Neo4j database..." -ForegroundColor Cyan
Set-Location -Path "C:\Program Files\Neo4j\neo4j-community-5.20.0\bin"
Start-Process -FilePath "neo4j.bat" -ArgumentList "start" -WindowStyle Minimized -PassThru
Set-Location -Path $PSScriptRoot
Start-Sleep -Seconds 10

# 3. Start Qdrant
Write-Host "[INFO] Starting Qdrant vector database..." -ForegroundColor Cyan
$qdrantStatus = docker start qdrant-bldr 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[INFO] Creating new Qdrant container..." -ForegroundColor Cyan
    docker run -d -p 6333:6333 -p 6334:6334 --name qdrant-bldr qdrant/qdrant:v1.7.0
} else {
    Write-Host "[INFO] Qdrant container already running" -ForegroundColor Green
}
Start-Sleep -Seconds 5

# 4. Start Celery worker and beat
Write-Host "[INFO] Starting Celery services..." -ForegroundColor Cyan
$celeryCommand = "celery -A core.celery_app worker --loglevel=info --concurrency=2 & celery -A core.celery_app beat --loglevel=info"
Start-Process -FilePath "cmd" -ArgumentList "/c $celeryCommand" -WindowStyle Minimized -PassThru
Start-Sleep -Seconds 3

# 5. Start FastAPI backend
Write-Host "[INFO] Starting FastAPI backend..." -ForegroundColor Cyan
Start-Process -FilePath "uvicorn" -ArgumentList "core.bldr_api:app --host 0.0.0.0 --port 8000" -WindowStyle Minimized -PassThru
Start-Sleep -Seconds 5

# 6. Start Telegram Bot
Write-Host "[INFO] Starting Telegram Bot..." -ForegroundColor Cyan
Start-Process -FilePath "python" -ArgumentList "integrations/telegram_bot.py" -WindowStyle Minimized -PassThru
Start-Sleep -Seconds 2

# 7. Start Frontend
Write-Host "[INFO] Starting Frontend Dashboard..." -ForegroundColor Cyan
Set-Location -Path "$PSScriptRoot\web\bldr_dashboard"
Start-Process -FilePath "npm" -ArgumentList "run dev" -WindowStyle Minimized -PassThru
Set-Location -Path $PSScriptRoot
Start-Sleep -Seconds 10

# Wait for services to fully start
Write-Host "[INFO] Waiting for services to initialize..." -ForegroundColor Cyan
Start-Sleep -Seconds 15

# Check if backend is responding
Write-Host "[INFO] Checking backend status..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "[INFO] Backend is responding" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Backend may not be ready" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARN] Backend not responding yet" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "   Bldr Empire v2 Started Successfully!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Services:"
Write-Host "  - Redis: localhost:6379"
Write-Host "  - Neo4j: http://localhost:7474"
Write-Host "  - Qdrant: http://localhost:6333"
Write-Host "  - FastAPI Backend: http://localhost:8000"
Write-Host "  - Frontend Dashboard: http://localhost:3001"
Write-Host ""
Write-Host "Credentials:"
Write-Host "  - Neo4j: neo4j/neo4j"
Write-Host ""
Write-Host "Opening frontend in your browser..." -ForegroundColor Cyan
Start-Process "http://localhost:3001"
Write-Host ""
Write-Host "To stop all services, run one_click_stop.ps1 or one_click_stop.bat" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to continue..."
$host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")