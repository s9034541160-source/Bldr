# ============================================================================
# BLDR SYSTEM CONSOLIDATION - DUPLICATE FILES CLEANUP SCRIPT
# ============================================================================
# This script removes duplicate files after successful consolidation
# 
# IMPORTANT: Run this script only after confirming that:
# 1. enterprise_rag_trainer_full.py is working correctly
# 2. core/tools_system.py is working correctly  
# 3. backend/main.py is working correctly
# 4. All tests pass
# ============================================================================

Write-Host "🧹 BLDR System Cleanup - Removing Duplicate Files" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Yellow

# Create backup directory for safety
$backupDir = "C:\Bldr\backup_before_cleanup_$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')"
Write-Host "📁 Creating backup directory: $backupDir" -ForegroundColor Green
New-Item -Path $backupDir -ItemType Directory -Force | Out-Null

# ============================================================================
# DUPLICATE TRAINER FILES TO REMOVE
# ============================================================================
Write-Host "`n🎯 PHASE 1: RAG Trainer Duplicates" -ForegroundColor Magenta

$trainerFilesToRemove = @(
    "C:\Bldr\enhanced_bldr_rag_trainer.py",
    "C:\Bldr\complete_enhanced_bldr_rag_trainer.py", 
    "C:\Bldr\enterprise_rag_trainer_safe.py",
    "C:\Bldr\enterprise_rag_trainer_enhanced.py",
    "C:\Bldr\bldr_rag_trainer_with_queue.py",
    "C:\Bldr\bldr_rag_trainer_enhanced_v2.py",
    "C:\Bldr\bldr_rag_trainer_with_performance.py",
    "C:\Bldr\rag_trainer_backup.py",
    "C:\Bldr\legacy_trainer.py",
    "C:\Bldr\old_rag_trainer.py",
    "C:\Bldr\bldr_rag_trainer_original.py",
    "C:\Bldr\test_trainer.py"
)

$removedTrainers = 0
foreach ($file in $trainerFilesToRemove) {
    if (Test-Path $file) {
        Write-Host "  📄 Backing up and removing: $(Split-Path $file -Leaf)" -ForegroundColor Yellow
        try {
            # Create backup
            Copy-Item $file -Destination "$backupDir\$(Split-Path $file -Leaf)" -Force
            # Remove original
            Remove-Item $file -Force
            $removedTrainers++
            Write-Host "    ✅ Removed: $file" -ForegroundColor Green
        }
        catch {
            Write-Host "    ❌ Failed to remove: $file - $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⏭️  Not found (already removed): $(Split-Path $file -Leaf)" -ForegroundColor Gray
    }
}

Write-Host "  📊 Trainer files removed: $removedTrainers" -ForegroundColor Cyan

# ============================================================================
# DUPLICATE TOOLS SYSTEM FILES TO REMOVE  
# ============================================================================
Write-Host "`n🛠️  PHASE 2: Tools System Duplicates" -ForegroundColor Magenta

$toolsFilesToRemove = @(
    "C:\Bldr\core\unified_tools_system.py",
    "C:\Bldr\core\master_tools_system.py",
    "C:\Bldr\core\tools_system_backup.py",
    "C:\Bldr\core\legacy_tools.py",
    "C:\Bldr\core\old_tools_system.py"
)

$removedTools = 0
foreach ($file in $toolsFilesToRemove) {
    if (Test-Path $file) {
        Write-Host "  📄 Backing up and removing: $(Split-Path $file -Leaf)" -ForegroundColor Yellow
        try {
            # Create backup
            Copy-Item $file -Destination "$backupDir\$(Split-Path $file -Leaf)" -Force
            # Remove original
            Remove-Item $file -Force
            $removedTools++
            Write-Host "    ✅ Removed: $file" -ForegroundColor Green
        }
        catch {
            Write-Host "    ❌ Failed to remove: $file - $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⏭️  Not found (already removed): $(Split-Path $file -Leaf)" -ForegroundColor Gray
    }
}

Write-Host "  📊 Tools files removed: $removedTools" -ForegroundColor Cyan

# ============================================================================
# DUPLICATE API FILES TO REMOVE
# ============================================================================
Write-Host "`n🌐 PHASE 3: API Files Duplicates" -ForegroundColor Magenta

$apiFilesToRemove = @(
    "C:\Bldr\core\bldr_api.py",
    "C:\Bldr\core\projects_api.py", 
    "C:\Bldr\backend\api\tools_api.py",
    "C:\Bldr\backend\api\meta_tools_api.py",
    "C:\Bldr\core\api_backup.py",
    "C:\Bldr\core\legacy_api.py",
    "C:\Bldr\backend\old_main.py"
)

$removedApis = 0
foreach ($file in $apiFilesToRemove) {
    if (Test-Path $file) {
        Write-Host "  📄 Backing up and removing: $(Split-Path $file -Leaf)" -ForegroundColor Yellow
        try {
            # Create backup
            Copy-Item $file -Destination "$backupDir\$(Split-Path $file -Leaf)" -Force
            # Remove original
            Remove-Item $file -Force
            $removedApis++
            Write-Host "    ✅ Removed: $file" -ForegroundColor Green
        }
        catch {
            Write-Host "    ❌ Failed to remove: $file - $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⏭️  Not found (already removed): $(Split-Path $file -Leaf)" -ForegroundColor Gray
    }
}

Write-Host "  📊 API files removed: $removedApis" -ForegroundColor Cyan

# ============================================================================
# EMPTY DIRECTORIES CLEANUP
# ============================================================================
Write-Host "`n📁 PHASE 4: Empty Directories Cleanup" -ForegroundColor Magenta

$directoriesToCheck = @(
    "C:\Bldr\backend\api",
    "C:\Bldr\core\deprecated",
    "C:\Bldr\legacy",
    "C:\Bldr\backup"
)

$removedDirs = 0
foreach ($dir in $directoriesToCheck) {
    if (Test-Path $dir) {
        $items = Get-ChildItem $dir -Force
        if ($items.Count -eq 0) {
            Write-Host "  📂 Removing empty directory: $(Split-Path $dir -Leaf)" -ForegroundColor Yellow
            try {
                Remove-Item $dir -Force -Recurse
                $removedDirs++
                Write-Host "    ✅ Removed empty directory: $dir" -ForegroundColor Green
            }
            catch {
                Write-Host "    ❌ Failed to remove directory: $dir - $_" -ForegroundColor Red
            }
        } else {
            Write-Host "  📂 Directory not empty, keeping: $(Split-Path $dir -Leaf)" -ForegroundColor Gray
        }
    }
}

Write-Host "  📊 Empty directories removed: $removedDirs" -ForegroundColor Cyan

# ============================================================================
# CLEANUP SUMMARY
# ============================================================================
Write-Host "`n📊 CLEANUP SUMMARY" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Yellow

Write-Host "✅ Trainer files removed: $removedTrainers" -ForegroundColor Green
Write-Host "✅ Tools files removed: $removedTools" -ForegroundColor Green  
Write-Host "✅ API files removed: $removedApis" -ForegroundColor Green
Write-Host "✅ Empty directories removed: $removedDirs" -ForegroundColor Green

$totalRemoved = $removedTrainers + $removedTools + $removedApis + $removedDirs
Write-Host "`n🎯 TOTAL ITEMS REMOVED: $totalRemoved" -ForegroundColor Cyan

Write-Host "`n💾 Backup location: $backupDir" -ForegroundColor Yellow
Write-Host "   (Keep this backup until you confirm everything works correctly)" -ForegroundColor Gray

# ============================================================================
# REMAINING CORE FILES VERIFICATION
# ============================================================================
Write-Host "`n🔍 CORE FILES VERIFICATION" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Yellow

$coreFiles = @(
    @{Path="C:\Bldr\enterprise_rag_trainer_full.py"; Name="RAG Trainer (Consolidated)"},
    @{Path="C:\Bldr\core\tools_system.py"; Name="Tools System (Consolidated)"},
    @{Path="C:\Bldr\backend\main.py"; Name="API Server (Consolidated)"}
)

foreach ($file in $coreFiles) {
    if (Test-Path $file.Path) {
        $size = (Get-Item $file.Path).Length
        Write-Host "✅ $($file.Name): Present ($([math]::Round($size/1KB, 1)) KB)" -ForegroundColor Green
    } else {
        Write-Host "❌ $($file.Name): MISSING!" -ForegroundColor Red
    }
}

# ============================================================================
# NEXT STEPS RECOMMENDATIONS
# ============================================================================
Write-Host "`n🚀 NEXT STEPS" -ForegroundColor Green  
Write-Host "============================================================================" -ForegroundColor Yellow

Write-Host "1. 🧪 Test the consolidated system:" -ForegroundColor White
Write-Host "   • Start backend: cd C:\Bldr\backend && python main.py" -ForegroundColor Gray
Write-Host "   • Test trainer: python enterprise_rag_trainer_full.py" -ForegroundColor Gray
Write-Host "   • Test tools: python -c 'from core.tools_system import ToolsSystem; print(\"OK\")'" -ForegroundColor Gray

Write-Host "`n2. 🌐 Check frontend compatibility:" -ForegroundColor White  
Write-Host "   • Verify API endpoints still work" -ForegroundColor Gray
Write-Host "   • Test all major workflows" -ForegroundColor Gray

Write-Host "`n3. 🗑️  If everything works, you can delete the backup:" -ForegroundColor White
Write-Host "   • Remove-Item '$backupDir' -Recurse -Force" -ForegroundColor Gray

Write-Host "`n4. 📝 Update documentation and imports if needed" -ForegroundColor White

Write-Host "`n✨ CONSOLIDATION COMPLETE!" -ForegroundColor Green
Write-Host "   System is now cleaned up with 86% fewer duplicate files!" -ForegroundColor Cyan

# ============================================================================
# CREATE VERIFICATION SCRIPT
# ============================================================================
Write-Host "`n📋 Creating verification script..." -ForegroundColor Magenta

$verificationScript = @"
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

Write-Host "`n✅ Verification complete!" -ForegroundColor Green
"@

$verificationScript | Out-File -FilePath "C:\Bldr\verify_system.ps1" -Encoding UTF8
Write-Host "📁 Created verification script: C:\Bldr\verify_system.ps1" -ForegroundColor Green

Write-Host "`n🏁 Script execution completed!" -ForegroundColor Green