# Bldr Empire v2 Batch File Guide

## IMPORTANT: Simplified Structure

We've significantly simplified the batch file structure to address user frustration with too many options. **Most batch files have been moved to the backup_batch_files directory and should not be used.**

## Current Recommended Files

### Main Startup Files (Use These):
- [start_bldr.bat](file:///c%3A/Bldr/start_bldr.bat) - Starts ALL services (Redis, Neo4j, Celery, API, Frontend) - Does NOT touch Neo4j processes
- [stop_bldr.bat](file:///c%3A/Bldr/stop_bldr.bat) - Stops ALL services - Does NOT touch Neo4j processes

See [SIMPLIFIED_STARTUP_GUIDE.md](file:///c%3A/Bldr/SIMPLIFIED_STARTUP_GUIDE.md) for detailed instructions.

### Legacy Files (Do NOT Use):
All other batch files have been moved to [backup_batch_files](file:///c%3A/Bldr/backup_batch_files) directory. These include:
- one_click_start.bat
- one_click_stop.bat
- start_backend.bat
- start_celery.bat
- start_celery_beat.bat
- launch_empire.bat
- stop_empire.bat
- And many others...

These files are kept for reference only but should not be used for starting the system.

## Recommended Usage

### For Development and Production:
1. Start Neo4j Desktop manually and ensure your database instance is running
2. Double-click [start_bldr.bat](file:///c%3A/Bldr/start_bldr.bat) to start everything (except Neo4j)
3. Work on your project
4. Double-click [stop_bldr.bat](file:///c%3A/Bldr/stop_bldr.bat) when done (Neo4j will continue running)

## What [start_bldr.bat](file:///c%3A/Bldr/start_bldr.bat) Does

1. Loads environment variables from .env file
2. Checks Neo4j status (does not affect Neo4j processes)
3. Starts Redis server
4. Starts Qdrant vector database (if Docker is available)
5. Starts Celery worker and beat
6. Starts FastAPI backend
7. Starts Frontend Dashboard

## What [stop_bldr.bat](file:///c%3A/Bldr/stop_bldr.bat) Does

1. Kills all Bldr Empire related processes (except Neo4j)
2. Cleans up any remaining processes by port (except Neo4j ports)
3. Stops Docker containers (if any)
4. Leaves Neo4j running

## Important Notes About Neo4j Handling

**CRITICAL**: Both scripts have been specifically modified to NOT interfere with Neo4j processes:

- **start_bldr.bat** will NOT kill Java processes (which includes Neo4j)
- **stop_bldr.bat** will NOT kill Java processes (which includes Neo4j)
- Neo4j must be started MANUALLY before using start_bldr.bat
- Neo4j will continue running after using stop_bldr.bat

This change was made to address user frustration with scripts killing Neo4j processes.

## Troubleshooting

### If services won't start:
1. Run [stop_bldr.bat](file:///c%3A/Bldr/stop_bldr.bat) to clean up existing processes (except Neo4j)
2. Run [start_bldr.bat](file:///c%3A/Bldr/start_bldr.bat) again

### Service URLs

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:3001
- **Neo4j Browser**: http://localhost:7474
- **Redis**: localhost:6379