# Bldr Empire v2 - Complete Startup with Duplicate Elimination
Write-Host "==================================================" -ForegroundColor Green
Write-Host "   BLDR EMPIRE - COMPLETE STARTUP WITH DUPLICATE ELIMINATION" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# Change to project directory
Set-Location -Path $PSScriptRoot

Write-Host "[INFO] Starting Bldr Empire with automatic duplicate elimination..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Run automatic duplicate elimination
Write-Host "[STEP 1/3] Running automatic duplicate elimination..." -ForegroundColor Cyan
Write-Host "This will process all 299 duplicate functions automatically." -ForegroundColor Yellow
Write-Host "Please ensure you have a full backup before proceeding." -ForegroundColor Yellow
Write-Host ""

# Run the automatic eliminator
try {
    python full_automatic_duplicate_eliminator.py
    Write-Host "[INFO] Automatic duplicate elimination completed" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Automatic duplicate elimination failed or was cancelled" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[STEP 2/3] Verifying system after duplicate elimination..." -ForegroundColor Cyan
# Run verification
try {
    python verify_merged_functions.py
    Write-Host "[INFO] System verification completed" -ForegroundColor Green
} catch {
    Write-Host "[WARN] System verification encountered issues" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[STEP 3/3] Starting Bldr Empire services..." -ForegroundColor Cyan
Write-Host ""

# Run the main startup script
try {
    .\start_bldr.ps1
    Write-Host "[INFO] Bldr Empire services started successfully" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to start Bldr Empire services: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "   COMPLETE STARTUP PROCESS FINISHED" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "If everything went well, your system should now be running." -ForegroundColor Cyan
Write-Host "Check the individual service windows for detailed logs." -ForegroundColor Cyan