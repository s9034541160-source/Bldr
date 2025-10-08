@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
set "PATH=C:\Bldr"
set "OUTPUT=C:\Bldr\fullcode.txt"
echo. > "%OUTPUT%"

for /r "%PATH%" %%f in (*.py) do (
    echo. >> "%OUTPUT%"
    echo ===== FILE: %%f ===== >> "%OUTPUT%"
    echo. >> "%OUTPUT%"
    type "%%f" >> "%OUTPUT%"
    echo. >> "%OUTPUT%"
    echo ------------------- END OF FILE ------------------- >> "%OUTPUT%"
    echo. >> "%OUTPUT%"
)

echo Merged all .py files into %OUTPUT%!
echo Count: 
dir /b /s "%PATH%\*.py" | find /c /v ""
pause