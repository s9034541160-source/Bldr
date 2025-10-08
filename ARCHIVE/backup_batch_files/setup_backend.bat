@echo off
echo Installing Bldr Empire v2 Backend dependencies...
echo.

pip install -r requirements.txt

echo.
echo Setup complete!
echo To start the backend server, run:
echo python core/bldr_api.py
echo.
pause