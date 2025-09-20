@echo off
set NEO4J_PATH=C:\Users\papa\AppData\Local\Programs\neo4j-desktop
echo NEO4J_PATH: %NEO4J_PATH%
if exist "%NEO4J_PATH%" (
    echo Path exists
    for /f "delims=" %%i in ('dir "%NEO4J_PATH%" /s /b ^| findstr \\bin$ 2^>nul') do (
        echo Found bin directory: %%i
        if exist "%%i\neo4j.bat" (
            echo Found neo4j.bat in %%i
        )
    )
) else (
    echo Path does not exist
)