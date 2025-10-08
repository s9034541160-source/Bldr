# Simple verification script

Write-Host "BLDR System Verification" -ForegroundColor Cyan

# Check if core files exist
if (Test-Path "C:\Bldr\enterprise_rag_trainer_full.py") {
    Write-Host "✅ RAG Trainer: Present" -ForegroundColor Green
} else {
    Write-Host "❌ RAG Trainer: Missing" -ForegroundColor Red
}

if (Test-Path "C:\Bldr\core\tools_system.py") {
    Write-Host "✅ Tools System: Present" -ForegroundColor Green
} else {
    Write-Host "❌ Tools System: Missing" -ForegroundColor Red
}

if (Test-Path "C:\Bldr\backend\main.py") {
    Write-Host "✅ API Server: Present" -ForegroundColor Green
} else {
    Write-Host "❌ API Server: Missing" -ForegroundColor Red
}

Write-Host "Verification complete!" -ForegroundColor Green