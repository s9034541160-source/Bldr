# Bldr Empire v2 - Stop All Services (PowerShell Version)
Write-Host "==================================================" -ForegroundColor Red
Write-Host "   Bldr Empire v2 - Stopping All Services" -ForegroundColor Red
Write-Host "==================================================" -ForegroundColor Red
Write-Host ""

# Change to project directory
Set-Location -Path $PSScriptRoot

# Stop Docker services
Write-Host "[INFO] Stopping Docker services..." -ForegroundColor Cyan
$dockerBin = "docker"
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    if (Test-Path "${env:ProgramFiles}\Docker\Docker\resources\bin\docker.exe") {
        $dockerBin = "${env:ProgramFiles}\Docker\Docker\resources\bin\docker.exe"
    } elseif (Test-Path "${env:ProgramFiles}\Docker\Docker\resources\bin\com.docker.cli.exe") {
        $dockerBin = "${env:ProgramFiles}\Docker\Docker\resources\bin\com.docker.cli.exe"
    }
}

if (Get-Command $dockerBin -ErrorAction SilentlyContinue) {
    try {
        # Stop Docker Compose services
        & $dockerBin compose down
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[INFO] Docker services stopped successfully" -ForegroundColor Cyan
        } else {
            Write-Host "[WARN] Some Docker services may not have stopped cleanly" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[WARN] Error stopping Docker services: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARN] Docker not found, skipping Docker service stop" -ForegroundColor Yellow
}

# Kill any remaining processes on our ports
Write-Host "[INFO] Cleaning up remaining processes..." -ForegroundColor Cyan
taskkill /F /IM redis-server.exe 2>$null
taskkill /F /IM node.exe 2>$null
taskkill /F /IM uvicorn.exe 2>$null
taskkill /F /IM celery.exe 2>$null

# Kill processes by port
$ports = @(8000, 3001, 6379, 7474, 7687, 6333)
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

Write-Host ""
Write-Host "==================================================" -ForegroundColor Red
Write-Host "   All Services Stopped" -ForegroundColor Red
Write-Host "==================================================" -ForegroundColor Red
Write-Host "Services stopped:" -ForegroundColor Red
Write-Host "  - Redis (Docker)" -ForegroundColor Red
Write-Host "  - Neo4j (Docker)" -ForegroundColor Red
Write-Host "  - Qdrant (Docker)" -ForegroundColor Red
Write-Host "  - FastAPI Backend" -ForegroundColor Red
Write-Host "  - Frontend Dashboard" -ForegroundColor Red
Write-Host "  - Celery Workers" -ForegroundColor Red
Write-Host "  - Telegram Bot" -ForegroundColor Red
Write-Host ""
Write-Host "To start services again, run start_bldr.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "Stop script completed." -ForegroundColor Red
