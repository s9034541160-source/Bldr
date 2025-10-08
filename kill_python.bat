@echo off
chcp 65001 >nul
echo ==========================================
echo    KILLING ALL PYTHON PROCESSES
echo ==========================================
echo.

echo [1/3] Killing python.exe...
taskkill /f /im python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] python.exe - TERMINATED
) else (
    echo [INFO] python.exe - NOT FOUND
)

echo [2/3] Killing py.exe...
taskkill /f /im py.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] py.exe - TERMINATED
) else (
    echo [INFO] py.exe - NOT FOUND
)

echo [3/3] Killing pythonw.exe...
taskkill /f /im pythonw.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] pythonw.exe - TERMINATED
) else (
    echo [INFO] pythonw.exe - NOT FOUND
)

echo.
echo ==========================================
echo    CHECKING REMAINING PROCESSES
echo ==========================================

echo Checking for remaining Python processes:
tasklist /fi "IMAGENAME eq python.exe" | findstr /i "python.exe" >nul
if %errorlevel% equ 0 (
    echo [WARNING] Found active python.exe processes!
    tasklist /fi "IMAGENAME eq python.exe"
) else (
    echo [OK] No active python.exe processes
)

tasklist /fi "IMAGENAME eq py.exe" | findstr /i "py.exe" >nul
if %errorlevel% equ 0 (
    echo [WARNING] Found active py.exe processes!
    tasklist /fi "IMAGENAME eq py.exe"
) else (
    echo [OK] No active py.exe processes
)

tasklist /fi "IMAGENAME eq pythonw.exe" | findstr /i "pythonw.exe" >nul
if %errorlevel% equ 0 (
    echo [WARNING] Found active pythonw.exe processes!
    tasklist /fi "IMAGENAME eq pythonw.exe"
) else (
    echo [OK] No active pythonw.exe processes
)

echo.
echo ==========================================
echo    ALL PYTHON PROCESSES TERMINATED
echo ==========================================
pause
