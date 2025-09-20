@echo off
echo [INFO] Checking Java installation...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Java is not installed or not in PATH.
    pause
    exit /b 1
)
echo [INFO] Java is installed and accessible.
pause