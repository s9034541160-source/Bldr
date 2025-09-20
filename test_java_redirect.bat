@echo off
echo Running java -version command with redirection...
java -version >nul 2>&1
echo Command completed with exit code: %errorlevel%
