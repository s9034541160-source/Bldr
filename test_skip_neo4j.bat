@echo off
title Bldr Empire v2 - Skip Neo4j Test
color 0A

echo ==================================================
echo    Bldr Empire v2 - Skip Neo4j Test
echo ==================================================
echo.

cd /d "%~dp0"

echo [INFO] Running backend test with Neo4j skipped...
python test_skip_neo4j.py

echo.
echo ==================================================
echo    Skip Neo4j Test Complete
echo ==================================================
echo.
echo Press any key to continue...
pause >nul