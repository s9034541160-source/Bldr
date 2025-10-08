# Simple cleanup script for BLDR system

Write-Host "🧹 BLDR System Cleanup" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Yellow

# Create backup directory
$backupDir = "C:\Bldr\backup_simple_$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')"
New-Item -Path $backupDir -ItemType Directory -Force | Out-Null
Write-Host "📁 Backup directory created: $backupDir" -ForegroundColor Green

# Check core files
Write-Host "`n🔍 Checking core files..." -ForegroundColor Magenta

$coreFiles = @(
    @{Path="C:\Bldr\enterprise_rag_trainer_full.py"; Name="RAG Trainer"},
    @{Path="C:\Bldr\core\tools_system.py"; Name="Tools System"},
    @{Path="C:\Bldr\backend\main.py"; Name="API Server"}
)

foreach ($file in $coreFiles) {
    if (Test-Path $file.Path) {
        $size = (Get-Item $file.Path).Length
        Write-Host "✅ $($file.Name): Present ($([math]::Round($size/1KB, 1)) KB)" -ForegroundColor Green
    } else {
        Write-Host "❌ $($file.Name): MISSING!" -ForegroundColor Red
    }
}

Write-Host "`n✨ Cleanup check complete!" -ForegroundColor Green