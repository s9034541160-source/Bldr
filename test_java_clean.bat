@echo off
echo [INFO] Checking Java installation...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Java is not installed or not in PATH. Neo4j requires Java to run.
    echo.
    echo [INFO] Please install Java 21 or later:
    echo [INFO] 1. Go to https://adoptium.net/
