@echo off
title Bldr Empire v2 - Stop GUI
color 0C

echo ==================================================
echo    Bldr Empire v2 - Stop GUI and Services
echo ==================================================
echo.

echo Stopping all Bldr Empire services...
echo.

REM Kill the GUI process and all related services
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Bldr Empire*" >nul 2>&1
taskkill /F /IM redis-server.exe >nul 2>&1
taskkill /F /IM java.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM docker.exe >nul 2>&1
taskkill /F /IM celery.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1

echo All Bldr Empire processes have been terminated.
echo.

echo ==================================================
echo    Cleanup Complete
echo ==================================================
echo.
echo Press any key to exit...
pause >nul