# Simple Frontend Compatibility Check

Write-Host "Frontend Compatibility Check" -ForegroundColor Cyan

# Check if frontend directory exists
if (Test-Path "C:\Bldr\web\bldr_dashboard") {
    Write-Host "Frontend directory exists" -ForegroundColor Green
} else {
    Write-Host "Frontend directory missing" -ForegroundColor Red
}

Write-Host "Frontend check complete!" -ForegroundColor Green