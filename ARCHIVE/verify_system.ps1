# BLDR System Verification Script
# Run this after cleanup to verify everything works

Write-Host "🔍 BLDR System Verification" -ForegroundColor Cyan

# Test imports
try {
    python -c "from enterprise_rag_trainer_full import EnterpriseRAGTrainer; print('✅ RAG Trainer import: OK')"
} catch {
    Write-Host "❌ RAG Trainer import failed" -ForegroundColor Red
}

try {
    python -c "from core.tools_system import ToolsSystem; print('✅ Tools System import: OK')" 
} catch {
    Write-Host "❌ Tools System import failed" -ForegroundColor Red
}

try {
    python -c "import sys; sys.path.append('backend'); from main import app; print('✅ API Server import: OK')"
} catch {
    Write-Host "❌ API Server import failed" -ForegroundColor Red
}

Write-Host "
✅ Verification complete!" -ForegroundColor Green
