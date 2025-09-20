@echo off
title Bldr Empire v2 - Launcher
echo ====================================================
echo   Bldr Empire v2 - Enterprise Mode Launcher
echo ====================================================
echo.

REM Start the API server in the background
start "Bldr API" /min cmd /c "cd /d c:\Bldr && python core\bldr_api.py"

REM Start the React dashboard
start "Bldr Dashboard" /min cmd /c "cd /d c:\Bldr\web\bldr_dashboard && npm start"

REM Start the Telegram bot
start "Bldr Bot" /min cmd /c "cd /d c:\Bldr && python integrations\telegram_bot.py"

echo Bldr Empire v2 started successfully!
echo API running on http://localhost:8000
echo Dashboard running on http://localhost:3000
echo Telegram bot active
echo.
echo Press any key to exit this window (services will continue running)
pause >nul
