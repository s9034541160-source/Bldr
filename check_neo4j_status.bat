@echo off
title Neo4j Status Check
color 0A

echo ==================================================
echo    Neo4j Status Check
echo ==================================================
echo.

cd /d "%~dp0"

echo [INFO] Checking Neo4j status...
python check_neo4j_status.py

echo.
echo ==================================================
echo    Neo4j Status Check Complete
echo ==================================================
echo.
echo Press any key to continue...
pause >nul