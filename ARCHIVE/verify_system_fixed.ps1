# BLDR System Verification Script
# Run this after cleanup to verify everything works

Write-Host "🔍 BLDR System Verification" -ForegroundColor Cyan

# Test imports
try {
    python -c "from enterprise_rag_trainer_full import EnterpriseRAGTrainer; print('RAG Trainer import: OK')"
    Write-Host "✅ RAG Trainer import: OK" -ForegroundColor Green
} catch {
    Write-Host "❌ RAG Trainer import failed" -ForegroundColor Red
}

try {
    python -c "from core.tools_system import ToolsSystem; print('Tools System import: OK')" 
    Write-Host "✅ Tools System import: OK" -ForegroundColor Green
} catch {
    Write-Host "❌ Tools System import failed" -ForegroundColor Red
}

try {
    python -c "import sys; sys.path.append('backend'); from main import app; print('API Server import: OK')"
    Write-Host "✅ API Server import: OK" -ForegroundColor Green
} catch {
    Write-Host "❌ API Server import failed" -ForegroundColor Red
}

Write-Host "`n✅ Verification complete!" -ForegroundColor Green