# Bldr Empire v2 - GUI Service Manager

## Overview

This is a simple Python GUI application built with Tkinter that provides a user-friendly interface for managing all Bldr Empire services. Instead of using multiple batch files, you can now control the entire system with a single GUI application.

## Features

- **Two Main Controls**: Start All Services and Stop All Services buttons
- **Service Status Monitoring**: Real-time status indicators for all services
- **Automatic Status Updates**: Status refreshes every 2 minutes or on-demand
- **Detailed Logging**: Log area showing all operations and errors
- **Port-Based Detection**: Accurately detects which services are running

## Services Managed

1. **Redis** (Port: 6379)
2. **Neo4j** (Port: 7474)
3. **Qdrant** (Port: 6333)
4. **Celery** (Workers and Beat scheduler)
5. **Backend API** (Port: 8000)
6. **Frontend Dashboard** (Port: 3001)
7. **Telegram Bot**

## How to Use

### Starting the GUI

1. Run `start_gui.bat` from the project root directory
2. The GUI window will open

### Using the GUI

1. **Start All Services**: Click the "▶ Start All Services" button
   - All services will start in the correct order
   - Log area will show progress
   - Status indicators will update automatically

2. **Stop All Services**: Click the "⏹ Stop All Services" button
   - All services will be terminated
   - Log area will show progress
   - Status indicators will update automatically

3. **Refresh Status**: Click the "🔄 Refresh Status" button
   - Manually update the status of all services
   - Useful for checking if services started correctly

4. **View Logs**: Check the log area at the bottom
   - All operations are logged with timestamps
   - Errors and successes are clearly indicated

5. **Clear Logs**: Click the "Clear Logs" button
   - Clears the log area for better visibility

## Status Indicators

- **Green**: Service is running
- **Red**: Service is stopped
- **Orange**: Service status is unknown

## Requirements

- Python 3.8 or higher
- All requirements from `requirements.txt` installed
- Redis, Neo4j, Docker, and Node.js properly installed
- All Bldr Empire components properly configured

## Technical Details

The GUI uses port-based detection to determine service status:
- For services with specific ports, it checks if the port is in use
- For Celery, it checks for running Celery processes
- It uses `psutil` library for process and network monitoring

## Troubleshooting

### If Services Don't Start

1. Check the log area for error messages
2. Ensure all prerequisites are installed
3. Verify that ports are not being used by other applications
4. Try running the GUI as administrator

### If Status Indicators Are Incorrect

1. Click "Refresh Status" button
2. Wait a few moments for automatic refresh (every 2 minutes)
3. Check if services are actually running using Task Manager

### If GUI Doesn't Start

1. Ensure Python is installed and in PATH
2. Check that `psutil` library is installed (`pip install psutil`)
3. Run `start_gui.bat` from the project root directory

## Benefits Over Batch Files

1. **Visual Feedback**: See the status of all services at a glance
2. **Centralized Control**: One interface to manage everything
3. **Real-time Monitoring**: Continuous status updates
4. **Detailed Logging**: Comprehensive operation logs
5. **Error Handling**: Better error reporting and recovery
6. **User-Friendly**: No need to manage multiple terminal windows

## Future Enhancements

Possible improvements for future versions:
- Individual service start/stop controls
- Service configuration options
- Performance monitoring graphs
- Export logs to file
- System resource usage display