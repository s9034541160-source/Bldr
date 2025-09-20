# Bldr Empire v2 - One-Click Startup Solution

## Summary of Changes

This document summarizes the changes made to implement a true one-click startup solution for Bldr Empire v2 that:

1. Launches all required system components automatically
2. Opens the correct frontend URL in the browser
3. Eliminates the need to guess which port the frontend is running on

## Files Updated

### 1. Batch Scripts
- **[one_click_start.bat](file:///c%3A/Bldr/one_click_start.bat)** - Enhanced startup script with:
  - Correct frontend port information (http://localhost:3001)
  - Backend status checking before opening browser
  - Automatic browser opening to the correct URL
  - Clear service information display

- **[one_click_stop.bat](file:///c%3A/Bldr/one_click_stop.bat)** - Updated stop script with:
  - Correct frontend port (3001) in process termination
  - Improved reliability

### 2. PowerShell Scripts
- **[one_click_start.ps1](file:///c%3A/Bldr/one_click_start.ps1)** - New PowerShell version of startup script with:
  - Better error handling and user feedback
  - Color-coded output for improved visibility
  - Same functionality as batch version

- **[one_click_stop.ps1](file:///c%3A/Bldr/one_click_stop.ps1)** - New PowerShell version of stop script

### 3. Backend Configuration
- **[core/bldr_api.py](file:///c%3A/Bldr/core/bldr_api.py)** - Updated WebSocket origin configuration to:
  - Allow connections from http://localhost:3001 (primary)
  - Maintain compatibility with http://localhost:3000 and http://localhost:3002

### 4. Documentation
- **[README.md](file:///c%3A/Bldr/README.md)** - Updated quick start instructions to reference:
  - Correct frontend port (http://localhost:3001)
  - [one_click_start.bat](file:///c%3A/Bldr/one_click_start.bat) as the primary startup method

- **[BATCH_FILE_GUIDE.md](file:///c%3A/Bldr/BATCH_FILE_GUIDE.md)** - Updated dashboard URL reference

- **[README_EMPIRE_LAUNCHER.md](file:///c%3A/Bldr/README_EMPIRE_LAUNCHER.md)** - Updated dashboard URL references

## How It Works

### Startup Process
1. User runs `one_click_start.bat` (or `one_click_start.ps1`)
2. Script automatically:
   - Cleans up any existing processes
   - Starts all required services (Redis, Neo4j, Qdrant, Celery, Backend, Telegram Bot)
   - Launches the frontend dashboard
   - Waits for services to initialize
   - Checks backend health status
   - Automatically opens `http://localhost:3001` in the default browser

### Service Information Display
The startup script clearly displays:
```
Services:
  - Redis: localhost:6379
  - Neo4j: http://localhost:7474
  - Qdrant: http://localhost:6333
  - FastAPI Backend: http://localhost:8000
  - Frontend Dashboard: http://localhost:3001
```

### Shutdown Process
1. User runs `one_click_stop.bat` (or `one_click_stop.ps1`)
2. Script automatically terminates all Bldr-related processes by:
   - Port-based process identification (more reliable)
   - Process name fallback
   - Proper service shutdown procedures (Neo4j, Docker)

## Benefits

1. **True One-Click Startup**: No manual terminal management required
2. **Correct Frontend URL**: No more guessing between ports 3000/3001
3. **Automatic Browser Opening**: Frontend opens automatically when ready
4. **Service Status Verification**: Backend health check before browser opening
5. **Cross-Platform Support**: Both batch and PowerShell versions available
6. **Persistent Configuration**: No need to re-enter credentials or settings
7. **Resource Management**: Proper process cleanup to avoid system crashes

## Usage Instructions

### Starting the System
```bash
# Option 1: Batch file (Windows Command Prompt)
one_click_start.bat

# Option 2: PowerShell script
one_click_start.ps1
```

### Stopping the System
```bash
# Option 1: Batch file (Windows Command Prompt)
one_click_stop.bat

# Option 2: PowerShell script
one_click_stop.ps1
```

## Technical Details

### Frontend Configuration
The frontend dashboard is configured in [web/bldr_dashboard/vite.config.ts](file:///c%3A/Bldr/web/bldr_dashboard/vite.config.ts) to run on port 3001:
```typescript
server: {
  port: 3001,
  strictPort: true, // Enforce the port to avoid conflicts
  // ...
}
```

### Backend CORS Configuration
The backend allows connections from the correct frontend URLs:
```python
allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3001"), "http://localhost:3000", "http://localhost:3002"]
```

### WebSocket Origin Configuration
WebSocket connections are allowed from the correct frontend URLs:
```python
allowed_origins = [os.getenv("FRONTEND_URL", "http://localhost:3001"), "http://localhost:3000", "http://localhost:3002"]
```

## Verification

After running the one-click startup script:
1. All services should be running (check with task manager)
2. Browser should automatically open to http://localhost:3001
3. Dashboard should load without CORS errors
4. WebSocket connections should establish successfully
5. API endpoints should be accessible at http://localhost:8000

## Troubleshooting

### If Frontend Doesn't Open Automatically
1. Check that all services started successfully
2. Manually navigate to http://localhost:3001
3. Check for firewall or antivirus blocking

### If Services Don't Start
1. Ensure all prerequisites are installed (Redis, Neo4j, Docker, Node.js, Python)
2. Check that ports are not being used by other applications
3. Run the script as administrator if needed

### If CORS Errors Occur
1. Verify that the backend is running on http://localhost:8000
2. Check that CORS configuration allows http://localhost:3001
3. Restart both backend and frontend services