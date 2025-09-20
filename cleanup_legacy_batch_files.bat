@echo off
title Bldr Empire v2 - Legacy File Cleanup
color 0E

echo ==================================================
echo    Bldr Empire v2 - Legacy File Cleanup
echo ==================================================
echo.

echo [INFO] Moving legacy batch files to backup directory...
echo.

REM Create backup directory if it doesn't exist
if not exist "backup_batch_files" (
    mkdir backup_batch_files
    echo [INFO] Created backup_batch_files directory
)

REM Move legacy batch files to backup directory
move /Y "one_click_start_fixed.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved one_click_start_fixed.bat to backup) else (echo [INFO] one_click_start_fixed.bat not found)

move /Y "one_click_start_fixed_v2.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved one_click_start_fixed_v2.bat to backup) else (echo [INFO] one_click_start_fixed_v2.bat not found)

move /Y "start_smart.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved start_smart.bat to backup) else (echo [INFO] start_smart.bat not found)

move /Y "start_final.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved start_final.bat to backup) else (echo [INFO] start_final.bat not found)

move /Y "start_debug.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved start_debug.bat to backup) else (echo [INFO] start_debug.bat not found)

move /Y "start_services_fixed.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved start_services_fixed.bat to backup) else (echo [INFO] start_services_fixed.bat not found)

move /Y "launch_empire.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved launch_empire.bat to backup) else (echo [INFO] launch_empire.bat not found)

move /Y "start_backend.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved start_backend.bat to backup) else (echo [INFO] start_backend.bat not found)

move /Y "start_celery.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved start_celery.bat to backup) else (echo [INFO] start_celery.bat not found)

move /Y "start_celery_beat.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved start_celery_beat.bat to backup) else (echo [INFO] start_celery_beat.bat not found)

move /Y "setup_dev.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved setup_dev.bat to backup) else (echo [INFO] setup_dev.bat not found)

move /Y "build.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved build.bat to backup) else (echo [INFO] build.bat not found)

move /Y "deploy.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved deploy.bat to backup) else (echo [INFO] deploy.bat not found)

move /Y "merge_py.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved merge_py.bat to backup) else (echo [INFO] merge_py.bat not found)

move /Y "one_click_stop.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved one_click_stop.bat to backup) else (echo [INFO] one_click_stop.bat not found)

move /Y "stop_empire.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved stop_empire.bat to backup) else (echo [INFO] stop_empire.bat not found)

move /Y "stop_empire_fixed.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved stop_empire_fixed.bat to backup) else (echo [INFO] stop_empire_fixed.bat not found)

move /Y "start_empire_fixed.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved start_empire_fixed.bat to backup) else (echo [INFO] start_empire_fixed.bat not found)

move /Y "one_click_start_en.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved one_click_start_en.bat to backup) else (echo [INFO] one_click_start_en.bat not found)

move /Y "one_click_start_new.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved one_click_start_new.bat to backup) else (echo [INFO] one_click_start_new.bat not found)

move /Y "one_click_start.ps1" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved one_click_start.ps1 to backup) else (echo [INFO] one_click_start.ps1 not found)

move /Y "one_click_stop.ps1" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved one_click_stop.ps1 to backup) else (echo [INFO] one_click_stop.ps1 not found)

move /Y "start_all_services.bat" "backup_batch_files\" >nul 2>&1
if %errorlevel% equ 0 (echo [INFO] Moved start_all_services.bat to backup) else (echo [INFO] start_all_services.bat not found)

echo.
echo ==================================================
echo    Cleanup Complete
echo ==================================================
echo.
echo All legacy batch files have been moved to the backup_batch_files directory.
echo You should now only use:
echo   - start_bldr.bat (to start the system)
echo   - stop_bldr.bat (to stop the system)
echo.
echo See SIMPLIFIED_STARTUP_GUIDE.md for more information.
echo.
pause