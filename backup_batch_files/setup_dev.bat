@echo off
echo Setting up Bldr Empire v2 Development Environment...

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install backend dependencies
echo Installing backend dependencies...
pip install -r requirements.txt

REM Install frontend dependencies
echo Installing frontend dependencies...
cd web/bldr_dashboard
npm install
cd ../..

echo Development environment setup complete!
echo To activate the environment, run: venv\Scripts\activate.bat
pause