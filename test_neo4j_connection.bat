@echo off
title Neo4j Connection Test
color 0A

echo ==================================================
echo    Neo4j Connection Test
echo ==================================================
echo.

cd /d "%~dp0"

echo [INFO] Testing Neo4j connection with default credentials...
python test_neo4j_connection.py

echo.
echo ==================================================
echo    Neo4j Connection Test Complete
echo ==================================================
echo.
echo Press any key to continue...
pause >nul