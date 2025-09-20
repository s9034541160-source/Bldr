@echo off
title Bldr Empire v2 - NTD Restoration
color 0A

echo ==================================================
echo    Bldr Empire v2 - NTD Base Restoration
echo ==================================================
echo.

echo [INFO] Starting NTD base restoration process...
echo [INFO] This will create a clean, structured NTD base from official sources
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Run the restoration script
echo [INFO] Running restoration script...
python restore_ntd.py

if %errorlevel% equ 0 (
    echo.
    echo ==================================================
    echo    NTD Base Restoration Completed Successfully!
    echo ==================================================
    echo.
    echo Next steps:
    echo 1. Run the complete cleaning process: python run_clean.py
    echo 2. Start the system: start_empire_fixed.bat
    echo 3. Access the dashboard at http://localhost:3000
    echo 4. Go to the Norms tab and trigger an update
    echo.
) else (
    echo.
    echo ==================================================
    echo    NTD Base Restoration Failed!
    echo ==================================================
    echo Please check the error messages above
    echo.
)

pause