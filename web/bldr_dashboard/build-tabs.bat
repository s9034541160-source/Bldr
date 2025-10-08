@echo off
echo Building Bldr Dashboard with Tool Tabs support...
echo.

echo Installing dependencies...
call npm ci
if %errorlevel% neq 0 (
    echo Error installing dependencies
    pause
    exit /b 1
)

echo.
echo Building project...
call npm run build
if %errorlevel% neq 0 (
    echo Error building project
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo.
echo New features:
echo - Tool Tabs Manager for better tool management
echo - Individual tool pages for full-screen work
echo - Browser tab support for tools
echo.
pause
