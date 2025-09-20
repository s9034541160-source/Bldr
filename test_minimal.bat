@echo off
echo Testing minimal script
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo Java not found
) else (
    echo Java found
)
echo Script completed