# Backend Initialization Fix

## Issue
The `start_bldr.ps1` script was unable to properly determine if the backend had initialized because:
1. It was using the `/status` endpoint which requires authentication (returns 403 Forbidden)
2. The timeout was set to 120 seconds (2 minutes) which was unnecessarily long
3. The script was not providing detailed information about the backend initialization status

## Solution

### 1. Reduced Timeout
Changed the timeout from 120 retries (2 minutes) to 30 retries (30 seconds) to match the user's requirement.

### 2. Changed Endpoint
Modified the script to use the `/auth/debug` endpoint instead of `/status` because:
- `/auth/debug` does not require authentication
- It provides detailed information about the backend's authentication configuration
- It confirms that the backend has properly loaded its configuration

### 3. Enhanced Status Reporting
Added detailed feedback about the backend's initialization status:
- Shows whether SKIP_AUTH is enabled
- Shows whether DEV_MODE is enabled
- Provides clearer progress updates

### 4. Fallback Mechanism
Added a fallback to the `/health` endpoint in case `/auth/debug` is not available.

## Files Modified
- `start_bldr.ps1` - Updated backend initialization check logic

## Testing
The fix has been tested and confirmed to work:
1. Script properly detects backend initialization within 30 seconds
2. Script provides detailed information about backend configuration
3. Fallback mechanism works correctly
4. Script continues execution even if backend check fails (as designed)

## Usage
Run the script as usual:
```powershell
.\start_bldr.ps1
```

The script will now:
1. Start all services
2. Wait up to 30 seconds for backend to initialize
3. Check initialization status using `/auth/debug` endpoint
4. Display detailed configuration information
5. Continue with frontend and other service startup