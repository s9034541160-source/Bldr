# Bldr Empire v2 - Simplified Startup Guide

## Important Notice

We've simplified the startup process to address your frustration with too many batch files. Now you only need to use these two files:

## Main Startup Files

1. **[start_bldr.bat](file:///C:/Bldr/start_bldr.bat)** - Starts ALL services (Redis, Celery, API, Frontend) - Does NOT touch Neo4j processes
2. **[stop_bldr.bat](file:///C:/Bldr/stop_bldr.bat)** - Stops ALL services - Does NOT touch Neo4j processes

## How to Start the System

1. Make sure Neo4j Desktop is running with a database instance configured with:
   - URI: neo4j://127.0.0.1:7687
   - User: neo4j
   - Password: neopassword
2. Double-click on **[start_bldr.bat](file:///C:/Bldr/start_bldr.bat)**
3. Wait for all services to initialize (this may take 30-60 seconds)
4. Access the system:
   - Frontend Dashboard: http://localhost:3001
   - API Documentation: http://localhost:8000/docs

## How to Stop the System

1. Double-click on **[stop_bldr.bat](file:///C:/Bldr/stop_bldr.bat)**
2. Wait for all services to stop
3. Neo4j will continue running and does not need to be restarted

## Prerequisites

1. Neo4j Desktop must be running with a database instance configured with:
   - URI: neo4j://127.0.0.1:7687
   - User: neo4j
   - Password: neopassword

2. Redis server (included in the project directory)

3. Node.js and npm for the frontend

## Troubleshooting

If you encounter any issues:

1. Make sure Neo4j Desktop is running with the correct credentials
2. Check that no other services are using the required ports (6379, 8000, 3001)
3. If problems persist, check the individual service windows for error messages

## Legacy Files (Do NOT Use)

All other batch files have been moved to the [backup_batch_files](file:///C:/Bldr/backup_batch_files) directory. These files are kept for reference only and should not be used for starting the system.