# Neo4j Process Protection Update

## Issue
User reported that [start_bldr.bat](file:///C:/Bldr/start_bldr.bat) was killing Neo4j processes at startup, causing frustration.

## Solution Implemented
Updated both [start_bldr.bat](file:///C:/Bldr/start_bldr.bat) and [stop_bldr.bat](file:///C:/Bldr/stop_bldr.bat) to exclude Neo4j processes from cleanup operations.

### Changes Made to [start_bldr.bat](file:///C:/Bldr/start_bldr.bat):
1. Removed `taskkill /F /IM java.exe` from the process cleanup section
2. Updated informational messages to indicate that Neo4j processes are excluded
3. Added comments explaining that Java/Neo4j processes are intentionally not killed

### Changes Made to [stop_bldr.bat](file:///C:/Bldr/stop_bldr.bat):
1. Removed `taskkill /F /IM java.exe` from the process killing section
2. Removed port killing for Neo4j ports (7474 and 7687)
3. Updated informational messages to indicate that Neo4j processes are left running
4. Removed Neo4j container stopping from Docker section

### Documentation Updates:
1. Updated [SIMPLIFIED_STARTUP_GUIDE.md](file:///C:/Bldr/SIMPLIFIED_STARTUP_GUIDE.md) to clearly state that Neo4j processes are not affected
2. Updated [STARTUP_GUIDE.md](file:///C:/Bldr/STARTUP_GUIDE.md) with detailed explanation of Neo4j process protection
3. Updated [BATCH_FILE_GUIDE.md](file:///C:/Bldr/BATCH_FILE_GUIDE.md) to reflect the changes
4. Updated [README.md](file:///C:/Bldr/README.md) with a note about manual Neo4j management

## Result
- Neo4j processes are no longer killed by startup/cleanup scripts
- User must manually start/stop Neo4j Desktop
- All other services are managed normally by the scripts
- Documentation clearly explains the new behavior