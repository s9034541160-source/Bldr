# Bldr Empire v2 - Simplified Startup Guide

## 🚀 Quick Start with New Unified Scripts

We've simplified the startup process to avoid confusion with multiple batch files. Now you can use just two scripts:

### Starting the System

1. **Start all services**: Double-click [start_bldr.bat](file:///c%3A/Bldr/start_bldr.bat) or run it from command prompt
2. **Access the dashboard**: Open http://localhost:3001 in your browser

### Stopping the System

1. **Stop all services**: Double-click [stop_bldr.bat](file:///c%3A/Bldr/stop_bldr.bat) or run it from command prompt

## What This Does

The [start_bldr.bat](file:///c%3A/Bldr/start_bldr.bat) script will automatically:

1. Clean up any existing processes (EXCEPT Neo4j)
2. Load environment variables (including your Neo4j credentials)
3. Start Redis server
4. Start Qdrant (if Docker is available)
5. Start Celery worker and beat scheduler
6. Start the FastAPI backend in a visible window
7. Start the React frontend in a visible window

## Prerequisites

Make sure you have:

1. **Neo4j Desktop** running with a database instance
   - Database should be accessible at `neo4j://localhost:7687`
   - Credentials should be `neo4j` / `neopassword`
   - **IMPORTANT**: Start Neo4j Desktop MANUALLY before running start_bldr.bat
2. **Redis** installed and accessible
3. **Docker** (optional, for Qdrant)
4. **Node.js** for the frontend

## Environment Variables

The system will use your `.env` file if it exists. If not, it will use these defaults:
```
NEO4J_USER=neo4j
NEO4J_PASSWORD=neopassword
NEO4J_URI=neo4j://localhost:7687
REDIS_URL=redis://localhost:6379
```

## Important Changes - Neo4j Processes Are No Longer Affected

**CRITICAL UPDATE**: Both [start_bldr.bat](file:///c%3A/Bldr/start_bldr.bat) and [stop_bldr.bat](file:///c%3A/Bldr/stop_bldr.bat) have been updated to NOT interfere with Neo4j processes:

- **start_bldr.bat** will NOT kill Java processes (which includes Neo4j)
- **stop_bldr.bat** will NOT kill Java processes (which includes Neo4j)
- Neo4j must be started MANUALLY before using start_bldr.bat
- Neo4j will continue running after using stop_bldr.bat

This change was made to address user frustration with scripts killing Neo4j processes.

## Troubleshooting

### If you see Neo4j authentication errors:

1. Make sure Neo4j Desktop is running
2. Make sure your database instance is started
3. Verify your credentials are `neo4j` / `neopassword`
4. If you changed the password, update your `.env` file

### If services don't start:

1. Check the individual command windows for error messages
2. Make sure all prerequisites are installed
3. Run [stop_bldr.bat](file:///c%3A/Bldr/stop_bldr.bat) and try again

### If ports are in use:

The script will automatically try to kill processes using our standard ports (EXCEPT Neo4j ports):
- 6379 (Redis)
- 6333 (Qdrant)
- 8000 (FastAPI)
- 3001 (Frontend)

## Legacy Scripts

**IMPORTANT**: Most legacy scripts have been moved to the [backup_batch_files](file:///c%3A/Bldr/backup_batch_files) directory and should NOT be used:
- `one_click_start.bat`
- `one_click_start_fixed.bat`
- `one_click_start_fixed_v2.bat`
- `start_debug.bat`
- `start_final.bat`
- `start_services_fixed.bat`
- `start_smart.bat`
- And many others...

Use [start_bldr.bat](file:///c%3A/Bldr/start_bldr.bat) and [stop_bldr.bat](file:///c%3A/Bldr/stop_bldr.bat) for a cleaner, simpler experience.