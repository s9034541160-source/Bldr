# Bldr Empire v2 - Unified Startup (PowerShell Version)
Write-Host "==================================================" -ForegroundColor Green
Write-Host "   Bldr Empire v2 - Unified Startup (PowerShell)" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# Change to project directory
Set-Location -Path $PSScriptRoot

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
    $env:NEO4J_URI = "neo4j://localhost:7687"
}

Write-Host "[INFO] Environment variables:" -ForegroundColor Cyan
Write-Host "  - NEO4J_USER: $($env:NEO4J_USER)" -ForegroundColor Cyan
Write-Host "  - NEO4J_PASSWORD: $($env:NEO4J_PASSWORD)" -ForegroundColor Cyan
Write-Host "  - NEO4J_URI: $($env:NEO4J_URI)" -ForegroundColor Cyan
Write-Host ""

# Check if Neo4j is running
Write-Host "[INFO] Checking Neo4j status..." -ForegroundColor Cyan
python check_neo4j_status.py
Write-Host ""

# 1. Start Redis
Write-Host "[INFO] Starting Redis server..." -ForegroundColor Cyan
if (Test-Path "redis") {
    Set-Location -Path "$PSScriptRoot\redis"
    if (Test-Path "redis-server.exe") {
        Start-Process -WindowStyle Minimized cmd "/c redis-server.exe redis.windows.conf"
        Write-Host "[INFO] Redis server started" -ForegroundColor Cyan
    } else {
        Write-Host "[ERROR] Redis server executable not found" -ForegroundColor Red
    }
    Set-Location -Path $PSScriptRoot
} else {
    Write-Host "[ERROR] Redis directory not found" -ForegroundColor Red
}
Start-Sleep -Seconds 5

# 2. Start Qdrant (if Docker is available)
Write-Host "[INFO] Starting Qdrant vector database..." -ForegroundColor Cyan
# If Qdrant already listening on 6333, skip Docker start and just report OK
$qdrantRunning = netstat -ano | findstr ":6333"
if ($qdrantRunning) {
    Write-Host "[INFO] Qdrant is already running on port 6333." -ForegroundColor Cyan
} else {
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
            & $dockerBin version >$null 2>&1
            if ($LASTEXITCODE -eq 0) {
                & $dockerBin ps >$null 2>&1
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "[WARN] Docker CLI available but daemon not reachable. Will try to start container anyway." -ForegroundColor Yellow
                }
                & $dockerBin start qdrant-bldr >$null 2>&1
                if ($LASTEXITCODE -ne 0) {
                    & $dockerBin run -d -p 6333:6333 -p 6334:6334 --name qdrant-bldr qdrant/qdrant:v1.7.0 >$null 2>&1
                    if ($LASTEXITCODE -ne 0) {
                        Write-Host "[WARN] Failed to start Qdrant container. System will use in-memory storage as fallback." -ForegroundColor Yellow
                    } else {
                        Write-Host "[INFO] Qdrant container created and started" -ForegroundColor Cyan
                    }
                } else {
                    Write-Host "[INFO] Qdrant container already running" -ForegroundColor Cyan
                }
            }
        } catch {
            Write-Host "[WARN] Docker not available. Qdrant will not be started." -ForegroundColor Yellow
            Write-Host "[INFO] System will use in-memory storage as fallback." -ForegroundColor Cyan
        }
    } else {
        Write-Host "[WARN] Docker not available. Qdrant will not be started." -ForegroundColor Yellow
        Write-Host "[INFO] System will use in-memory storage as fallback." -ForegroundColor Cyan
    }
}
Start-Sleep -Seconds 5

# 3. Start Celery worker and beat
Write-Host "[INFO] Starting Celery services..." -ForegroundColor Cyan
Set-Location -Path $PSScriptRoot
if (Test-Path "core") {
    Start-Process -WindowStyle Minimized cmd "/c celery -A core.celery_app worker --loglevel=info --concurrency=2"
    Start-Sleep -Seconds 2
    Start-Process -WindowStyle Minimized cmd "/c celery -A core.celery_app beat --loglevel=info"
    Write-Host "[INFO] Celery services started" -ForegroundColor Cyan
} else {
    Write-Host "[ERROR] Core directory not found" -ForegroundColor Red
}
Start-Sleep -Seconds 3

# 4. Start FastAPI backend
Write-Host "[INFO] Starting FastAPI backend..." -ForegroundColor Cyan
Set-Location -Path $PSScriptRoot
if (Test-Path "backend\main.py") {
    Start-Process cmd "/k python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload" -WindowStyle Normal
    Write-Host "[INFO] FastAPI backend started in visible window" -ForegroundColor Cyan
} else {
    Write-Host "[ERROR] main.py not found" -ForegroundColor Red

}

Write-Host "[INFO] Waiting for backend to initialize..." -ForegroundColor Cyan
$backendReady = $false
$retryCount = 0
$maxRetries = 30  # Reduced timeout to 30 seconds
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
    
    Write-Host "[INFO] Launching Frontend Dashboard..." -ForegroundColor Cyan
    Start-Process cmd "/k cd /d `"$frontendDir`" && npm run dev" -WindowStyle Normal
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

# 6. Start Telegram Bot
Write-Host "[INFO] Starting Telegram Bot..." -ForegroundColor Cyan
Set-Location -Path $PSScriptRoot
if (Test-Path "integrations\telegram_bot.py") {
    if ([string]::IsNullOrEmpty($env:TELEGRAM_BOT_TOKEN)) {
        Write-Host "[WARN] TELEGRAM_BOT_TOKEN not set. Skipping Telegram Bot startup." -ForegroundColor Yellow
    } else {
        Write-Host "[INFO] Launching Telegram Bot in a separate window..." -ForegroundColor Cyan
        Start-Process -WindowStyle Minimized cmd "/k python integrations/telegram_bot.py"
    }
} else {
    Write-Host "[WARN] Telegram bot script not found. Skipping." -ForegroundColor Yellow
}
Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "   Startup Complete" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Services:" -ForegroundColor Green
Write-Host "  - Redis: localhost:6379" -ForegroundColor Green
Write-Host "  - Neo4j: http://localhost:7474 (make sure it's running with neo4j/neopassword)" -ForegroundColor Green
Write-Host "  - Qdrant: http://localhost:6333 (if Docker is working)" -ForegroundColor Green
Write-Host "  - FastAPI Backend: http://localhost:8000" -ForegroundColor Green
Write-Host "  - Frontend Dashboard: http://localhost:3001" -ForegroundColor Green
Write-Host "  - Telegram Bot: Running in background (check for token in .env)" -ForegroundColor Green
Write-Host ""
Write-Host "[IMPORTANT] Check the FastAPI and Frontend windows for initialization logs" -ForegroundColor Yellow
Write-Host "[IMPORTANT] The system will be ready when both windows show successful startup messages" -ForegroundColor Yellow
Write-Host ""
Write-Host "To stop all services, run stop_bldr.bat" -ForegroundColor Yellow
Write-Host ""
Write-Host "Startup script completed. Services are running in background windows." -ForegroundColor Green