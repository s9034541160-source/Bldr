@echo off
title Bldr Empire v2 - Neo4j Setup
color 0A

echo ==================================================
echo    Bldr Empire v2 - Neo4j Setup
echo ==================================================
echo.

cd /d "%~dp0"

echo [INFO] Running Neo4j setup script...
python setup_neo4j_manual.py

echo.
echo ==================================================
echo    Neo4j Setup Complete
echo ==================================================
echo.
echo Press any key to continue...
pause >nul