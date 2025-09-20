@echo off
echo Checking Java...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Java is not installed or not in PATH. Neo4j requires Java to run.
    echo.
    echo Please install Java 21 or later:
    echo 1. Go to https://adoptium.net/
    echo 2. Download OpenJDK 21 (LTS) JDK
    echo 3. Run the installer and follow the instructions
    echo 4. After installation, restart your computer
    echo 5. Run this script again
    echo.
    echo Note: Make sure to install the JDK (not JRE) version.
    echo.
    pause
    exit /b 1
) else (
    echo Java found
    pause
)
