@echo off
echo Checking Java...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Java is not installed or not in PATH. Neo4j requires Java to run.
    pause
    exit /b 1
)
echo Java found
pause

