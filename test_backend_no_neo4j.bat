@echo off
title Bldr Empire v2 - Backend Test (No Neo4j)
color 0A

echo ==================================================
echo    Bldr Empire v2 - Backend Test (No Neo4j)
echo ==================================================
echo.

cd /d "%~dp0"

echo [INFO] Running backend test without Neo4j...
python test_backend_no_neo4j.py

echo.
echo ==================================================
echo    Backend Test Complete
echo ==================================================
echo.
echo Press any key to continue...
pause >nul