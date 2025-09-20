@echo off
echo Checking Java...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Java is not installed or not in PATH. Neo4j requires Java to run.
    echo.
    echo [INFO] Please install Java 21 or later:
    echo [INFO] 1. Go to https://adoptium.net/
    echo [INFO] 2. Download "OpenJDK 21 (LTS) JDK"
    echo [INFO] 3. Run the installer and follow the instructions
    echo [INFO] 4. After installation, restart your computer
    echo [INFO] 5. Run this script again
    echo.
    echo [INFO] Note: Make sure to install the JDK (not JRE) version.
    echo.
    pause
    exit /b 1
)
echo Java found

