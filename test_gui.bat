@echo off
setlocal

title Bldr Empire v2 - GUI Test
color 0A

:: Change to the script's directory
cd /d "%~dp0"

echo ==================================================
echo    Bldr Empire v2 - GUI Test
echo ==================================================
echo.

echo Starting Bldr Empire GUI...
echo.
echo The GUI will open in a new window.
echo This window will stay open after the GUI closes.
echo.

:: Start the GUI and keep this window open
echo Running GUI...
python bldr_gui.py
echo.
echo GUI process finished with error level: %errorlevel%
echo.

echo ==================================================
echo    Bldr Empire v2 GUI Test Complete
echo ==================================================
echo.

echo Press any key to exit...
pause >nul