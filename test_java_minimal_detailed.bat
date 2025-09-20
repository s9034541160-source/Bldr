@echo off
echo Checking Java...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Java is not installed or not in PATH.
    echo.
    echo Please install Java 21 or later.
    echo.
    pause
    exit /b 1
) else (
    echo Java found
    pause
)
