@echo off
echo Stopping Bldr Empire v2 services...
echo.

REM Kill Python processes (API and bot)
taskkill /f /im python.exe /fi "WINDOWTITLE eq Bldr API*"
taskkill /f /im python.exe /fi "WINDOWTITLE eq Bldr Bot*"

REM Kill Node.js processes (Dashboard)
taskkill /f /im node.exe /fi "WINDOWTITLE eq Bldr Dashboard*"

echo Bldr Empire v2 services stopped.
echo.
echo Press any key to exit
pause >nul