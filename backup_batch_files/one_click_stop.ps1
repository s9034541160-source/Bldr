# Bldr Empire v2 - One-Click Stop Script
# PowerShell Version

Write-Host "===================================================" -ForegroundColor Green
Write-Host "   Bldr Empire v2 - Stopping All Services (PowerShell)" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Stopping Bldr Empire v2 services..." -ForegroundColor Cyan
Write-Host ""

# Kill processes by port (more reliable than window title)
Write-Host "Checking for processes on common Bldr ports..." -ForegroundColor Cyan

# Define ports
$ports = @{
    "API_PORT" = 8000
    "DASHBOARD_PORT" = 3001
    "REDIS_PORT" = 6379
    "NEO4J_PORT" = 7474
    "QDRANT_PORT" = 6333
}

foreach ($port in $ports.GetEnumerator()) {
    Write-Host "Stopping services on port $($port.Value)..." -ForegroundColor Cyan
    $netstatOutput = netstat -aon | Select-String ":$($port.Value)" | Select-String "LISTENING"
    if ($netstatOutput) {
        foreach ($line in $netstatOutput) {
            $pid = ($line -split '\s+')[4]
            Write-Host "Killing process $pid on port $($port.Value)" -ForegroundColor Cyan
            taskkill /f /pid $pid 2>$null
        }
    }
}

# Kill by process name as fallback
Write-Host "Killing remaining Bldr-related processes..." -ForegroundColor Cyan
taskkill /f /im python.exe /fi "WINDOWTITLE eq *Bldr*" 2>$null
taskkill /f /im node.exe /fi "WINDOWTITLE eq *Bldr*" 2>$null
taskkill /f /im redis-server.exe 2>$null
taskkill /f /im java.exe /fi "WINDOWTITLE eq *Neo4j*" 2>$null
taskkill /f /im docker.exe /fi "WINDOWTITLE eq *Qdrant*" 2>$null
taskkill /f /im uvicorn.exe 2>$null
taskkill /f /im npm.exe 2>$null
taskkill /f /im celery.exe 2>$null

# Stop Neo4j service properly
Write-Host "Stopping Neo4j service..." -ForegroundColor Cyan
Set-Location -Path "C:\Program Files\Neo4j\neo4j-community-5.20.0\bin"
.\neo4j.bat stop 2>$null
Set-Location -Path $PSScriptRoot

# Stop Docker containers
Write-Host "Stopping Docker containers..." -ForegroundColor Cyan
docker stop qdrant-bldr 2>$null

Write-Host ""
Write-Host "===================================================" -ForegroundColor Green
Write-Host "   Bldr Empire v2 Services Stopped Successfully!" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Write-Host "All services have been terminated." -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit"
$host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")