# Bldr Empire v2 - Service Startup System Summary

This document summarizes the one-click startup system implementation for Bldr Empire v2.

## Files Created

### Batch Scripts
1. **[one_click_start.bat](file:///c%3A/Bldr/one_click_start.bat)** - Main startup script
   - Checks system requirements
   - Installs missing dependencies
   - Starts all services (API, Dashboard, Telegram Bot)
   - Provides clear status messages

2. **[one_click_stop.bat](file:///c%3A/Bldr/one_click_stop.bat)** - Main stop script
   - Terminates all running services
   - Cleans up processes thoroughly

### PowerShell Scripts
3. **[one_click_start.ps1](file:///c%3A/Bldr/one_click_start.ps1)** - PowerShell version of startup script
   - Same functionality as batch version but with PowerShell syntax
   - Better error handling and output formatting

4. **[one_click_stop.ps1](file:///c%3A/Bldr/one_click_stop.ps1)** - PowerShell version of stop script
   - Same functionality as batch version but with PowerShell syntax

### Documentation
5. **[README_EMPIRE_LAUNCHER.md](file:///c%3A/Bldr/README_EMPIRE_LAUNCHER.md)** - User guide for the launcher system
   - Instructions for use
   - Troubleshooting guide
   - Service overview

### Utility Scripts
6. **[check_status.py](file:///c%3A/Bldr/check_status.py)** - Service status checker
   - Verifies if all services are running properly
   - Provides detailed status information

## Features Implemented

### Automatic Dependency Management
- Checks for Python and Node.js installation
- Automatically installs missing Python packages from requirements.txt
- Automatically installs missing Node.js packages

### Service Management
- Starts FastAPI backend server on port 8000
- Starts React dashboard on port 5173 (Vite dev server)
- Starts Telegram bot service
- Provides clear URLs for accessing services

### Process Control
- Starts each service in its own minimized window
- Properly terminates all services when stopping
- Cleans up any orphaned processes

### Error Handling
- Validates working directory
- Checks for required files and directories
- Provides clear error messages for missing dependencies
- Handles installation failures gracefully

### User Experience
- Color-coded output (PowerShell version)
- Progress indicators
- Clear instructions
- Comprehensive documentation

## Usage

### Starting Services
```cmd
# Using batch script
one_click_start.bat

# Using PowerShell script
powershell -ExecutionPolicy Bypass -File one_click_start.ps1
```

### Stopping Services
```cmd
# Using batch script
one_click_stop.bat

# Using PowerShell script
powershell -ExecutionPolicy Bypass -File one_click_stop.ps1
```

### Checking Status
```cmd
python check_status.py
```

## Services Overview

After startup, the following services will be available:

1. **API Server**: http://localhost:8000
   - FastAPI backend with all endpoints
   - Real-time WebSocket connections
   - Automatic norms updating

2. **Dashboard**: http://localhost:5173
   - React frontend with all tools and features
   - Real-time updates via WebSocket
   - File management and RAG training interface

3. **Telegram Bot**:
   - Connects to your configured Telegram bot
   - Provides query, training, and analysis capabilities via chat

## Requirements

- Windows OS (tested on Windows 10/11)
- Python 3.8 or higher
- Node.js 14 or higher
- Internet connection for initial setup

## Troubleshooting

If you encounter issues:

1. **Services not starting**:
   - Check that all prerequisites are installed
   - Ensure no antivirus is blocking the processes
   - Try running as administrator

2. **Port conflicts**:
   - Make sure ports 8000 and 5173 are not in use by other applications
   - You can change ports in the startup script if needed

3. **Dependency issues**:
   - The launcher should automatically install missing dependencies
   - If it fails, try manually running: `pip install -r requirements.txt`

## Future Improvements

Potential enhancements for future versions:
- Cross-platform support (Linux/Mac)
- Service installation as Windows services
- Configuration file for custom ports and settings
- Log file management
- Automatic updates