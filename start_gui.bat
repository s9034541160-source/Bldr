@echo off
setlocal

title Bldr Empire v2 - GUI Launcher
color 0A

:: Change to the script's directory
cd /d "%~dp0"

echo ==================================================
echo    Bldr Empire v2 - GUI Launcher
echo ==================================================
echo.

echo Starting Bldr Empire GUI...
echo.
echo The GUI will open in a new window.
echo Use the GUI to start/stop all services.
echo.

:: Start the GUI in a way that keeps the window open
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found in PATH
    echo Please install Python and make sure it's in your system PATH
    echo.
    pause
    exit /b 1
)

echo Current directory: %cd%
echo Python version:
python --version
echo.

echo Running GUI with full error output...
echo.

:: Run the GUI and capture error level
echo === GUI Process Start ===
python bldr_gui.py
set GUI_EXIT_CODE=%errorlevel%
echo === GUI Process End ===
echo Python process finished with error level: %GUI_EXIT_CODE%
echo.

:: If we reach this point, the GUI has closed
echo ==================================================
echo    Bldr Empire v2 GUI Closed
echo ==================================================
echo.

if %GUI_EXIT_CODE% equ 0 (
    echo GUI closed normally
) else (
    echo GUI closed with error: %GUI_EXIT_CODE%
    echo.
    echo Check for error logs or traceback information above
)

echo.
echo Press any key to exit...
pause >nul
exit /b %GUI_EXIT_CODE%