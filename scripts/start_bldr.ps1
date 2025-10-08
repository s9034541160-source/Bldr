# Bldr Empire v2 - Unified Startup (PowerShell Version)
Write-Host "==================================================" -ForegroundColor Green
Write-Host "   Bldr Empire v2 - Unified Startup (PowerShell)" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# Change to project directory
Set-Location -Path $PSScriptRoot

# Use global Python
Write-Host "[INFO] Using global Python" -ForegroundColor Cyan

# Kill any existing processes on our ports (EXCEPT Java/Neo4j)
Write-Host "[INFO] Cleaning up existing processes (excluding Neo4j and other Python apps)..." -ForegroundColor Cyan
taskkill /F /IM redis-server.exe 2>$null
taskkill /F /IM node.exe 2>$null
taskkill /F /IM uvicorn.exe 2>$null

# Don't kill all Python processes - only kill specific Bldr processes by port
$ports = @(8000, 3001)
foreach ($port in $ports) {
    $processes = netstat -ano | findstr ":$port"
    if ($processes) {
        $processes | ForEach-Object {
            if ($_ -match '\s+(\d+)$') {
                $processId = $matches[1]
                taskkill /F /PID $processId 2>$null
            }
        }
    }
}
taskkill /F /IM celery.exe 2>$null

Start-Sleep -Seconds 3

# Load environment variables
Write-Host "[INFO] Loading environment variables..." -ForegroundColor Cyan
if (Test-Path ".env") {
    Get-Content ".env" | Where-Object { $_ -notmatch '^\s*#' -and $_ -notmatch '^\s*$' } | ForEach-Object {
        $name, $value = $_.split('=', 2)
        if ($name -and $value) {
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
            Set-Variable -Name $name -Value $value
        }
    }
    Write-Host "[INFO] Environment variables loaded from .env" -ForegroundColor Cyan
} else {
    Write-Host "[WARN] .env file not found, using default values" -ForegroundColor Yellow
    $env:NEO4J_USER = "neo4j"
    $env:NEO4J_PASSWORD = "neopassword"
    $env:REDIS_URL = "redis://localhost:6379"
    $env:NEO4J_URI = "neo4j://127.0.0.1:7687"
    $env:TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
    $env:TELEGRAM_WEBHOOK_SECRET = "default_secret"
}

# Ensure Celery broker/result env vars (fallback to REDIS_URL or defaults)
if (-not $env:CELERY_BROKER_URL -or [string]::IsNullOrEmpty($env:CELERY_BROKER_URL)) {
    if ($env:REDIS_URL) {
        $env:CELERY_BROKER_URL = "$($env:REDIS_URL)/0"
    } else {
        $env:CELERY_BROKER_URL = "redis://localhost:6379/0"
    }
}
if (-not $env:CELERY_RESULT_BACKEND -or [string]::IsNullOrEmpty($env:CELERY_RESULT_BACKEND)) {
    if ($env:REDIS_URL) {
        $env:CELERY_RESULT_BACKEND = "$($env:REDIS_URL)/0"
    } else {
        $env:CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
    }
}

Write-Host "[INFO] Environment variables:" -ForegroundColor Cyan
Write-Host "  - NEO4J_USER: $($env:NEO4J_USER)" -ForegroundColor Cyan
Write-Host "  - NEO4J_PASSWORD: $($env:NEO4J_PASSWORD)" -ForegroundColor Cyan
Write-Host "  - NEO4J_URI: $($env:NEO4J_URI)" -ForegroundColor Cyan
Write-Host "  - REDIS_URL: $($env:REDIS_URL)" -ForegroundColor Cyan
Write-Host "  - TELEGRAM_BOT_TOKEN: $(if ($env:TELEGRAM_BOT_TOKEN -and $env:TELEGRAM_BOT_TOKEN -ne 'YOUR_TELEGRAM_BOT_TOKEN_HERE') { '***configured***' } else { 'not set' })" -ForegroundColor Cyan
Write-Host "  - TELEGRAM_WEBHOOK_SECRET: $(if ($env:TELEGRAM_WEBHOOK_SECRET) { '***configured***' } else { 'using default' })" -ForegroundColor Cyan
Write-Host ""

# Check if Neo4j is running
Write-Host "[INFO] Checking Neo4j status..." -ForegroundColor Cyan
python check_neo4j_status.py
Write-Host ""

# 1. Start Docker Services (Redis, Neo4j, Qdrant)
Write-Host "[INFO] Starting Docker services (Redis, Neo4j, Qdrant)..." -ForegroundColor Cyan

# Check if Docker is available
$dockerBin = "docker"
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    if (Test-Path "${env:ProgramFiles}\Docker\Docker\resources\bin\docker.exe") {
        $dockerBin = "${env:ProgramFiles}\Docker\Docker\resources\bin\docker.exe"
    } elseif (Test-Path "${env:ProgramFiles}\Docker\Docker\resources\bin\com.docker.cli.exe") {
        $dockerBin = "${env:ProgramFiles}\Docker\Docker\resources\bin\com.docker.cli.exe"
    }
}

if (Get-Command $dockerBin -ErrorAction SilentlyContinue) {
    Write-Host "[INFO] Docker detected: $dockerBin" -ForegroundColor Cyan
    try {
        # Check Docker daemon
        & $dockerBin version >$null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[INFO] Docker daemon is running" -ForegroundColor Cyan
            
            # Check if containers are already running
            $redisRunning = netstat -ano | findstr ":6379"
            $neo4jRunning = netstat -ano | findstr ":7474"
            $qdrantRunning = netstat -ano | findstr ":6333"
            
            if ($redisRunning -and $neo4jRunning -and $qdrantRunning) {
                Write-Host "[INFO] All database services are already running" -ForegroundColor Cyan
            } else {
                Write-Host "[INFO] Starting Docker Compose services..." -ForegroundColor Cyan
                
                # Start Docker Compose services
                & $dockerBin compose up -d redis neo4j qdrant
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "[INFO] Docker services started successfully" -ForegroundColor Cyan
                    
                    # Wait for services to be ready
                    Write-Host "[INFO] Waiting for services to be ready..." -ForegroundColor Cyan
                    $maxWait = 60  # 60 seconds max wait
                    $waitCount = 0
                    
                    do {
                        $redisReady = netstat -ano | findstr ":6379"
                        $neo4jReady = netstat -ano | findstr ":7474"
                        $qdrantReady = netstat -ano | findstr ":6333"
                        
                        if ($redisReady -and $neo4jReady -and $qdrantReady) {
                            Write-Host "[INFO] All services are ready!" -ForegroundColor Cyan
                            break
                        }
                        
                        $waitCount++
                        if ($waitCount % 10 -eq 0) {
                            Write-Host "[INFO] Still waiting for services... ($waitCount/$maxWait)" -ForegroundColor Yellow
                        }
                        Start-Sleep -Seconds 1
                    } while ($waitCount -lt $maxWait)
                    
                    if ($waitCount -ge $maxWait) {
                        Write-Host "[WARN] Services may not be fully ready, but continuing..." -ForegroundColor Yellow
                    }
                } else {
                    Write-Host "[ERROR] Failed to start Docker services" -ForegroundColor Red
                    Write-Host "[WARN] System will use fallback mechanisms" -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "[ERROR] Docker daemon not running" -ForegroundColor Red
            Write-Host "[WARN] Please start Docker Desktop and try again" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[ERROR] Docker not available: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "[WARN] System will use fallback mechanisms" -ForegroundColor Yellow
    }
} else {
    Write-Host "[ERROR] Docker not found" -ForegroundColor Red
    Write-Host "[WARN] Please install Docker Desktop and try again" -ForegroundColor Yellow
    Write-Host "[WARN] System will use fallback mechanisms" -ForegroundColor Yellow
}

Start-Sleep -Seconds 5

# 3. Start Celery worker and beat
Write-Host "[INFO] Starting Celery services..." -ForegroundColor Cyan
Set-Location -Path $PSScriptRoot
if (Test-Path "core") {
    # Allow running Celery inside WSL with prefork/concurrency
    $useWslCelery = ($env:USE_WSL_CELERY -and $env:USE_WSL_CELERY.ToLower() -eq "true")
    $celeryConcurrency = if ($env:CELERY_CONCURRENCY) { $env:CELERY_CONCURRENCY } else { "2" }

    if ($useWslCelery) {
        # Convert Windows path to WSL path
        $wslProjectPath = ("$PSScriptRoot" -replace ":","" -replace "\\","/")
        $wslProjectPath = "/mnt/" + $wslProjectPath.Substring(0,1).ToLower() + "/" + $wslProjectPath.Substring(2)

        # Optional WSL venv path (e.g., /mnt/c/Bldr/.venv). If not set, use system Celery in WSL
        $wslVenvPath = $env:WSL_VENV_PATH
        $wslActivate = if ($wslVenvPath) { "source `"$wslVenvPath/bin/activate`" && " } else { "" }

        # Worker with prefork and configurable concurrency
        Start-Process -WindowStyle Minimized wsl.exe -ArgumentList "-e","bash","-lc","cd `"$wslProjectPath`" && $wslActivate celery -A core.celery_app:celery_app worker --loglevel=info --concurrency=$celeryConcurrency"
        Start-Sleep -Seconds 2
        # Beat
        Start-Process -WindowStyle Minimized wsl.exe -ArgumentList "-e","bash","-lc","cd `"$wslProjectPath`" && $wslActivate celery -A core.celery_app:celery_app beat --loglevel=info"
    } else {
        # Prefer Windows venv celery if available; use solo pool for Windows stability
        $celeryBin = Join-Path $PSScriptRoot "venv\Scripts\celery.exe"
        if (-not (Test-Path $celeryBin)) { $celeryBin = "celery" }
        $env:PYTHONPATH = $PSScriptRoot
        # Worker (Windows) - Use batch file for better error handling
        Start-Process -WindowStyle Normal -FilePath "start_celery_worker.bat"
        Start-Sleep -Seconds 3
        # Beat (Windows) - Use batch file for better error handling  
        Start-Process -WindowStyle Normal -FilePath "start_celery_beat.bat"
    }
    Write-Host "[INFO] Celery services started" -ForegroundColor Cyan
} else {
    Write-Host "[ERROR] Core directory not found" -ForegroundColor Red
}
Start-Sleep -Seconds 3

# 4. Start FastAPI backend
Write-Host "[INFO] Starting FastAPI backend..." -ForegroundColor Cyan
Set-Location -Path $PSScriptRoot

# Check for main.py in root directory first, then in backend directory
$mainPyPath = ""
if (Test-Path "main.py") {
    $mainPyPath = "main.py"
    Write-Host "[INFO] Found main.py in root directory" -ForegroundColor Cyan
} elseif (Test-Path "backend\main.py") {
    $mainPyPath = "backend\main.py"
    Write-Host "[INFO] Found main.py in backend directory" -ForegroundColor Cyan
} else {
    Write-Host "[ERROR] main.py not found in root or backend directory" -ForegroundColor Red
}

if ($mainPyPath -ne "") {
    Write-Host "[INFO] Starting FastAPI with: uvicorn main:app --host 127.0.0.1 --port 8000" -ForegroundColor Cyan
    # Ensure we run from project root so 'main:app' is importable
    # Use global Python
    Start-Process cmd "/k cd /d `"$PSScriptRoot`" && py -m uvicorn main:app --host 127.0.0.1 --port 8000" -WindowStyle Normal
    Write-Host "[INFO] FastAPI backend started in visible window" -ForegroundColor Cyan
} else {
    Write-Host "[ERROR] Could not locate main.py - backend will not start" -ForegroundColor Red
}

Write-Host "[INFO] Waiting for backend to initialize..." -ForegroundColor Cyan
$backendReady = $false
$retryCount = 0
$maxRetries = 90  # Allow up to 90 seconds for backend to be ready
do {
    try {
        # Try /auth/debug endpoint first as it provides more detailed info about backend initialization
        $response = Invoke-WebRequest -Uri "http://localhost:8000/auth/debug" -Method GET -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            Write-Host "[INFO] Backend is ready" -ForegroundColor Cyan
            # Show some debug info
            try {
                $debugInfo = $response.Content | ConvertFrom-Json
                Write-Host "[INFO] Auth config: SKIP_AUTH=$($debugInfo.skip_auth), DEV_MODE=$($debugInfo.dev_mode)" -ForegroundColor Cyan
            } catch {
                # Ignore JSON parsing errors
            }
            break
        }
    } catch {
        try {
            # Fallback to /health endpoint
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                $backendReady = $true
                Write-Host "[INFO] Backend is ready (health check)" -ForegroundColor Cyan
                break
            }
        } catch {
            # Ignore errors and continue
        }
    }
    
    $retryCount++
    if ($retryCount % 5 -eq 0) {
        Write-Host "[INFO] Still waiting for backend... ($retryCount/30)" -ForegroundColor Yellow
    }
    Start-Sleep -Seconds 1
} while ($retryCount -lt $maxRetries)

if (-not $backendReady) {
    Write-Host "[ERROR] Backend failed to start in time" -ForegroundColor Red
    Write-Host "[WARN] Continuing startup anyway..." -ForegroundColor Yellow
}

# Additional readiness check: wait for tools registry to load (prevents frontend racing)
if ($backendReady) {
    Write-Host "[INFO] Verifying tools registry readiness..." -ForegroundColor Cyan
    $toolsReady = $false
    $toolRetries = 0
    $toolMaxRetries = 60  # up to 60 seconds for tools to register
    # Try to obtain JWT token for authorized requests
    $authHeader = $null
    try {
        $tokenResp = Invoke-WebRequest -Uri "http://localhost:8000/token" -Method Post -Body "username=admin&password=admin&grant_type=password" -ContentType "application/x-www-form-urlencoded" -TimeoutSec 5
        if ($tokenResp.StatusCode -eq 200 -and $tokenResp.Content) {
            $tokenJson = $tokenResp.Content | ConvertFrom-Json
            if ($tokenJson.access_token) {
                $authHeader = @{ Authorization = "Bearer $($tokenJson.access_token)" }
                Write-Host "[INFO] Acquired JWT token for tools readiness check" -ForegroundColor Cyan
            }
        }
    } catch { }
    do {
        try {
            if ($authHeader) {
                $resp = Invoke-WebRequest -Uri "http://localhost:8000/tools/list" -Method GET -Headers $authHeader -TimeoutSec 5
            } else {
                $resp = Invoke-WebRequest -Uri "http://localhost:8000/tools/list" -Method GET -TimeoutSec 5
            }
            if ($resp.StatusCode -eq 200 -and $resp.Content) {
                try {
                    $json = $resp.Content | ConvertFrom-Json
                    # Try to get total_count or count tools dictionary
                    $total = 0
                    if ($json.total_count) { $total = [int]$json.total_count }
                    elseif ($json.data -and $json.data.total_count) { $total = [int]$json.data.total_count }
                    elseif ($json.tools) { $total = ($json.tools.PSObject.Properties | Measure-Object).Count }
                    elseif ($json.data -and $json.data.tools) { $total = ($json.data.tools.PSObject.Properties | Measure-Object).Count }
                    if ($total -ge 1) {
                        $toolsReady = $true
                        Write-Host "[INFO] Tools registry ready (count=$total)" -ForegroundColor Cyan
                        break
                    }
                } catch {}
            }
        } catch {}
        $toolRetries++
        if ($toolRetries % 10 -eq 0) {
            Write-Host "[INFO] Waiting for tools... ($toolRetries/$toolMaxRetries)" -ForegroundColor Yellow
        }
        Start-Sleep -Seconds 1
    } while ($toolRetries -lt $toolMaxRetries)
    if (-not $toolsReady) {
        Write-Host "[WARN] Tools registry not fully ready; proceeding anyway" -ForegroundColor Yellow
    }
    
    # Check new services availability
    Write-Host "[INFO] Checking new services availability..." -ForegroundColor Cyan
    
    # Check Telegram Webhook
    try {
        $webhookResp = Invoke-WebRequest -Uri "http://localhost:8000/tg/health" -Method GET -TimeoutSec 5
        if ($webhookResp.StatusCode -eq 200) {
            Write-Host "[INFO] Telegram Webhook service ready" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "[WARN] Telegram Webhook service not available" -ForegroundColor Yellow
    }
    
    # Check Tender Analyzer
    try {
        $tenderResp = Invoke-WebRequest -Uri "http://localhost:8000/analyze/health" -Method GET -TimeoutSec 5
        if ($tenderResp.StatusCode -eq 200) {
            Write-Host "[INFO] Tender Analyzer service ready" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "[WARN] Tender Analyzer service not available" -ForegroundColor Yellow
    }
    
    # Check Estimate Calculator
    try {
        $estimateResp = Invoke-WebRequest -Uri "http://localhost:8000/tools/estimate_calculator/health" -Method GET -TimeoutSec 5
        if ($estimateResp.StatusCode -eq 200) {
            Write-Host "[INFO] Estimate Calculator service ready" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "[WARN] Estimate Calculator service not available" -ForegroundColor Yellow
    }
}

# 5. Start Frontend
Write-Host "[INFO] Starting Frontend Dashboard..." -ForegroundColor Cyan
$frontendDir = "$PSScriptRoot\web\bldr_dashboard"
if (Test-Path "$frontendDir\package.json") {
    Write-Host "[INFO] Preparing Frontend dependencies..." -ForegroundColor Cyan
    Set-Location -Path $frontendDir
    
    if (-not (Test-Path "node_modules")) {
        Write-Host "[INFO] node_modules not found -> npm ci" -ForegroundColor Cyan
        npm ci
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[WARN] npm ci failed. If you see EPERM unlink for esbuild.exe:" -ForegroundColor Yellow
            Write-Host "       1) Close all Node processes and antivirus real-time scan for this folder" -ForegroundColor Yellow
            Write-Host "       2) Manually delete node_modules\@esbuild" -ForegroundColor Yellow
            Write-Host "       3) Re-run this script" -ForegroundColor Yellow
        } else {
            Write-Host "[INFO] Dependencies installed" -ForegroundColor Cyan
        }
    } else {
        if (-not (Test-Path "node_modules\.bin\vite.cmd")) {
            Write-Host "[WARN] vite not found -> npm ci" -ForegroundColor Yellow
            npm ci
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[WARN] npm ci failed. See hints above (EPERM / antivirus / close node)" -ForegroundColor Yellow
            } else {
                Write-Host "[INFO] Dependencies repaired" -ForegroundColor Cyan
            }
        } else {
            Write-Host "[INFO] node_modules OK (vite present)" -ForegroundColor Cyan
        }
    }

    # Check if port 3001 is already in use
    $port3001InUse = netstat -ano | findstr ":3001"
    if ($port3001InUse) {
        Write-Host "[WARN] Port 3001 is already in use. Attempting to kill existing process..." -ForegroundColor Yellow
        $port3001InUse | ForEach-Object {
            if ($_ -match '\s+(\d+)$') {
                $processId = $matches[1]
                taskkill /F /PID $processId 2>$null
            }
        }
    }
    
    Write-Host "[INFO] Building Frontend Dashboard..." -ForegroundColor Cyan
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Frontend build failed" -ForegroundColor Red
    } else {
        Write-Host "[INFO] Frontend built successfully" -ForegroundColor Cyan
    }
    
    Write-Host "[INFO] Launching Frontend Dashboard (Production)..." -ForegroundColor Cyan
    Start-Process cmd "/k cd /d `"$frontendDir`" && py -m http.server 3001 --directory dist" -WindowStyle Normal
    Set-Location -Path $PSScriptRoot
    Start-Sleep -Seconds 15
    Write-Host "[INFO] Opening browser to http://localhost:3001" -ForegroundColor Cyan
    Start-Process "http://localhost:3001"

} else {
    Write-Host "[ERROR] Frontend dashboard not found" -ForegroundColor Red
}
Set-Location -Path $PSScriptRoot

Write-Host "[INFO] Continuing startup..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# 6. Start Telegram Bot (aiogram)
Write-Host "[INFO] Starting Telegram Bot (aiogram)..." -ForegroundColor Cyan
Set-Location -Path $PSScriptRoot
if (Test-Path "integrations\\telegram_bot_aiogram.py") {
    if ([string]::IsNullOrEmpty($env:TELEGRAM_BOT_TOKEN) -or $env:TELEGRAM_BOT_TOKEN -eq 'YOUR_TELEGRAM_BOT_TOKEN_HERE') {
        Write-Host "[WARN] TELEGRAM_BOT_TOKEN not set. Skipping Telegram Bot startup." -ForegroundColor Yellow
    } else {
        Write-Host "[INFO] Launching Telegram Bot (aiogram) in a separate window..." -ForegroundColor Cyan
        Start-Process -WindowStyle Minimized cmd "/k python integrations/telegram_bot_aiogram.py"
    }
} else {
    Write-Host "[WARN] Aiogram Telegram bot script not found. Skipping." -ForegroundColor Yellow
}
Set-Location -Path $PSScriptRoot

# 7. Start Telegram Webhook (if configured)
Write-Host "[INFO] Checking Telegram Webhook configuration..." -ForegroundColor Cyan
if (-not [string]::IsNullOrEmpty($env:TELEGRAM_BOT_TOKEN) -and $env:TELEGRAM_BOT_TOKEN -ne 'YOUR_TELEGRAM_BOT_TOKEN_HERE') {
    Write-Host "[INFO] Telegram Bot Token configured - webhook endpoints available at /tg/webhook" -ForegroundColor Cyan
    Write-Host "[INFO] Webhook URL: http://localhost:8000/tg/webhook" -ForegroundColor Cyan
} else {
    Write-Host "[WARN] TELEGRAM_BOT_TOKEN not set. Webhook endpoints will not be available." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "   Startup Complete" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Services:" -ForegroundColor Green
Write-Host "  - Redis: localhost:6379 (Docker)" -ForegroundColor Green
Write-Host "  - Neo4j: http://localhost:7474 (Docker, neo4j/neopassword)" -ForegroundColor Green
Write-Host "  - Qdrant: http://localhost:6333 (Docker)" -ForegroundColor Green
Write-Host "  - FastAPI Backend: http://localhost:8000" -ForegroundColor Green
Write-Host "  - Frontend Dashboard: http://localhost:3001" -ForegroundColor Green
Write-Host "  - Telegram Bot: Running in background (check for token in .env)" -ForegroundColor Green
Write-Host "  - Telegram Webhook: http://localhost:8000/tg/webhook" -ForegroundColor Green
Write-Host "  - Tender Analyzer: http://localhost:8000/analyze/tender" -ForegroundColor Green
Write-Host "  - Estimate Calculator: http://localhost:8000/tools/estimate_calculator/" -ForegroundColor Green
Write-Host ""
Write-Host "[IMPORTANT] Check the FastAPI and Frontend windows for initialization logs" -ForegroundColor Yellow
Write-Host "[IMPORTANT] The system will be ready when both windows show successful startup messages" -ForegroundColor Yellow
Write-Host ""
Write-Host "To stop all services, run stop_bldr.bat" -ForegroundColor Yellow
Write-Host ""
Write-Host "Startup script completed. Services are running in background windows." -ForegroundColor Green