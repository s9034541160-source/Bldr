@echo off
echo Checking Java...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo Java not found
    pause
    exit /b 1
)
echo Java found
pause

