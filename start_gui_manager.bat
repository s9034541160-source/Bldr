@echo off
title Bldr Empire v2 - GUI Manager
color 0A

echo ==================================================
echo    Bldr Empire v2 - GUI Service Manager
echo ==================================================
echo.

cd /d "%~dp0"

echo [INFO] Starting GUI Service Manager...
echo [INFO] Please use the GUI to start/stop services
echo.

python bldr_gui_manager.py

echo.
echo ==================================================
echo    GUI Manager Closed
echo ==================================================
echo.
pause