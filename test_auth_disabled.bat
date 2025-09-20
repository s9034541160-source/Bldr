@echo off
cd /d "c:\Bldr"
echo Testing authentication disabled configuration...
python verify_auth_disabled.py
echo.
echo If authentication is disabled, you should be able to access the system without login.
echo Restart the Bldr system for changes to take effect.
pause