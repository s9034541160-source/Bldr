# Real Celery Implementation in Bldr Empire v2

This document describes the real Celery implementation that replaces all mock implementations in Bldr Empire v2.

## What Was Removed (Mocks Eliminated)

1. **Celery mock in update_norms** → Replaced with real task.delay()
2. **Fake queue data** → Replaced with /queue endpoint from Neo4j + Redis
3. **Simulate emit** → Replaced with real sio.emit
4. **Mock responses** → Replaced with real HTTP requests and database operations

## Implementation Details

### Backend Components

1. **Celery Configuration** (`core/celery_app.py`):
   - Real Redis broker and backend configuration
   - Proper task serialization settings
   - Timezone configuration (Europe/Moscow)
   - Beat schedule for daily norms updates

2. **Celery Tasks** (`core/celery_norms.py`):
   - Real `update_norms_task` implementation
   - Proper task status logging to Neo4j
   - Real WebSocket updates during task execution
   - Error handling with proper status updates

3. **API Endpoints** (`core/bldr_api.py`):
   - `/norms-update` endpoint for triggering tasks
   - `/queue` endpoint for retrieving task status
   - Proper authentication and error handling

### Frontend Components

1. **Queue Component** (`web/bldr_dashboard/src/components/Queue.tsx`):
   - Real data fetching from `/queue` endpoint
   - WebSocket integration for real-time updates
   - Proper error handling and empty state display

2. **API Service** (`web/bldr_dashboard/src/services/api.ts`):
   - Real queue data retrieval
   - Proper typing for queue tasks

## Services Architecture

```
[FastAPI Server] ←→ [Redis] ←→ [Celery Worker]
      ↓               ↑
[Neo4j Database] ←─────┘
      ↓
[WebSocket Clients]
```

## How to Run

### Using Docker (Recommended)

1. Start all services:
   ```bash
   docker-compose up -d
   ```

2. Start Celery worker:
   ```bash
   celery -A core.celery_app worker --loglevel=info
   ```

3. Start Celery beat (for scheduled tasks):
   ```bash
   celery -A core.celery_app beat --loglevel=info
   ```

### Using Local Services

1. Install Redis:
   - Windows: Download from https://redis.io/download/
   - macOS: `brew install redis`
   - Linux: `sudo apt-get install redis-server`

2. Start Redis:
   ```bash
   redis-server
   ```

3. Start FastAPI server:
   ```bash
   python -m core.main
   ```

4. Start Celery worker:
   ```bash
   celery -A core.celery_app worker --loglevel=info
   ```

5. Start Celery beat:
   ```bash
   celery -A core.celery_app beat --loglevel=info
   ```

## Testing the Implementation

### Automated Tests

Run the comprehensive test script:
```bash
python comprehensive_celery_test.py
```

### Manual Testing

1. Start all services as described above
2. Make an authenticated POST request to `/norms-update`
3. Observe the Celery worker logs
4. Check Neo4j for task status updates
5. Verify WebSocket updates in the frontend queue

## Key Features

1. **Real Task Queuing**: Tasks are properly queued in Redis using `.delay()`
2. **Database Integration**: Task status is stored in Neo4j
3. **Real-time Updates**: WebSocket updates are sent during task execution
4. **Error Handling**: Proper error handling with status updates
5. **No Mocks**: All mock implementations have been replaced with real functionality

## Troubleshooting

### Redis Connection Issues

1. Ensure Redis is running on localhost:6379
2. Check firewall settings
3. Verify Redis configuration

### Celery Worker Issues

1. Check that all dependencies are installed
2. Verify Redis connectivity
3. Check worker logs for specific error messages

### Task Execution Issues

1. Check Neo4j connectivity
2. Verify proper authentication
3. Check task logs for specific error messages

## Performance Considerations

1. **Resource Usage**: The implementation avoids the memory issues mentioned in previous mock implementations
2. **Concurrency**: Celery workers can be scaled for better performance
3. **Database Connections**: Proper connection pooling is implemented

## Future Enhancements

1. Add more task types (train_rag, parse_batch)
2. Implement task prioritization
3. Add task cancellation functionality
4. Enhance error reporting and logging