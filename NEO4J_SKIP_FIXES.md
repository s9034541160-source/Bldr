# Neo4j Skip Fixes for Bldr Empire v2

This document summarizes the changes made to allow Bldr Empire v2 to run without Neo4j when it's not available or when the user prefers to start it manually.

## Changes Made

### 1. Core API Changes

**File**: [core/bldr_api.py](file:///c:/Bldr/core/bldr_api.py)

- Added support for `SKIP_NEO4J` environment variable
- Modified trainer initialization to skip Neo4j when requested
- Updated health check endpoint to report "skipped" status when Neo4j is disabled

### 2. RAG Trainer Changes

**File**: [scripts/bldr_rag_trainer.py](file:///c:/Bldr/scripts/bldr_rag_trainer.py)

- Added `skip_neo4j` parameter to constructor
- Modified Neo4j initialization to skip connection when requested
- Added logging to indicate when Neo4j is skipped

### 3. Startup Script Changes

**File**: [one_click_start.bat](file:///c:/Bldr/one_click_start.bat)

- Added `SKIP_NEO4J=true` environment variable when starting the backend
- Updated status messages to indicate Neo4j is being skipped
- Added instructions for manual Neo4j setup

### 4. New Utility Scripts

**Files Created**:
- [setup_neo4j_manual.py](file:///c:/Bldr/setup_neo4j_manual.py) - Python script to help set up Neo4j manually
- [setup_neo4j.bat](file:///c:/Bldr/setup_neo4j.bat) - Batch file to run the setup script
- [test_skip_neo4j.py](file:///c:/Bldr/test_skip_neo4j.py) - Test script to verify backend works without Neo4j
- [test_skip_neo4j.bat](file:///c:/Bldr/test_skip_neo4j.bat) - Batch file to run the test
- [TROUBLESHOOTING.md](file:///c:/Bldr/TROUBLESHOOTING.md) - Comprehensive troubleshooting guide

### 5. Documentation Updates

**File**: [README.md](file:///c:/Bldr/README.md)

- Added troubleshooting section
- Added instructions for manual Neo4j setup

## How to Use

### Option 1: Run with Neo4j Skipped (Default)

Simply run the [one_click_start.bat](file:///c:/Bldr/one_click_start.bat) script. It will now skip Neo4j initialization and start the rest of the system.

### Option 2: Test Without Neo4j

Run [test_skip_neo4j.bat](file:///c:/Bldr/test_skip_neo4j.bat) to verify that the backend can start without Neo4j.

### Option 3: Manual Neo4j Setup

If you want to use Neo4j:

1. Start Neo4j Desktop
2. Create or start a database instance
3. Ensure it's listening on port 7687
4. Run [setup_neo4j.bat](file:///c:/Bldr/setup_neo4j.bat) to configure the password

## Benefits

1. **Faster Startup**: System starts without waiting for Neo4j connection timeouts
2. **Reduced Dependencies**: Users can run the system without Neo4j installed
3. **Flexibility**: Users can choose when to start Neo4j manually
4. **Better Error Handling**: Clear status reporting when Neo4j is skipped
5. **Troubleshooting**: Comprehensive guide for resolving issues

## Limitations When Neo4j is Skipped

When Neo4j is skipped, the following features may be limited or unavailable:
- Template management
- Project management
- Some advanced data storage features
- Graph-based queries

However, the core functionality of the system will still work, including:
- RAG training and querying
- Document processing
- Celery task management
- Frontend dashboard
- Telegram bot