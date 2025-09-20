# Celery Queue Implementation for Request Routing/Prioritization

## Current Implementation Overview

The Bldr Empire system currently uses a hybrid approach for handling requests with a single LM Studio instance serving multiple users:

### 1. Training Requests (/train endpoint)
- Training requests are handled via FastAPI's BackgroundTasks
- The `train` endpoint starts training in the background using `run_training_with_updates`
- Training runs in a separate thread to avoid blocking the event loop
- Progress updates are sent via WebSocket for real-time feedback

### 2. Celery Integration
- Celery is currently used primarily for scheduled norms updates
- The `update_norms_task` is scheduled to run daily via Celery Beat
- Celery tasks are stored in Redis and results are also stored in Redis
- Task status and progress are tracked in Neo4j and accessible via the `/queue` endpoint

### 3. Queue Management (/queue endpoint)
- The queue status endpoint retrieves task information from Neo4j
- It also attempts to get real-time status from Celery for active tasks
- Tasks are displayed in the frontend Queue tab with progress information

## Current Limitations

1. **Training requests are not queued through Celery** - they use FastAPI's BackgroundTasks
2. **No prioritization mechanism** - all training requests are processed in the order they arrive
3. **No resource limiting** - multiple concurrent training requests can overload the system
4. **Single LM Studio instance** - all AI requests go to the same LM Studio endpoint

## Proposed Enhancement: Full Celery Integration for Request Routing

To better handle multiple users and requests with a single LM Studio instance, we could implement a more comprehensive Celery-based queuing system:

### 1. Convert Training to Celery Tasks

```python
# In core/celery_app.py, add new task
@celery_app.task(bind=True, name='core.celery_tasks.train_task')
def train_task(self, custom_dir: Optional[str] = None):
    """Celery task for RAG training with progress tracking"""
    task_id = self.request.id
    
    try:
        # Initialize trainer
        from scripts.bldr_rag_trainer import BldrRAGTrainer
        trainer = BldrRAGTrainer()
        
        # Override base_dir if custom directory provided
        if custom_dir:
            trainer.base_dir = custom_dir
            
        # Define progress callback
        def progress_callback(stage: str, log: str, progress: int = 0):
            # Update task progress in Neo4j
            update_task_progress(task_id, stage, log, progress)
            
            # Emit WebSocket update
            async def emit_update():
                await manager.broadcast(json.dumps({
                    'id': task_id,
                    'type': 'train',
                    'status': 'running',
                    'stage': stage,
                    'message': log,
                    'progress': progress
                }))
            
            # Run async emission
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(emit_update())
            loop.close()
        
        # Run training with progress tracking
        trainer.train(progress_callback)
        
        # Mark task as completed
        update_task_status(task_id, 'completed', 100)
        
        return {"status": "completed", "message": "Training finished successfully"}
        
    except Exception as e:
        # Mark task as failed
        update_task_status(task_id, 'failed', 0, str(e))
        raise
```

### 2. Update API Endpoint to Use Celery

```python
# In core/bldr_api.py, modify the train endpoint
@app.post("/train")
async def train(request: Request, custom_dir: Optional[str] = None, credentials: dict = Depends(verify_api_token)):
    """Submit training request to Celery queue"""
    try:
        # Import Celery task
        from core.celery_tasks import train_task
        
        # Send task to Celery worker
        task = train_task.delay(custom_dir)
        
        # Log task in Neo4j
        log_task_to_neo4j(task.id, 'train', custom_dir)
        
        return {
            "status": "queued", 
            "task_id": task.id,
            "message": "Training request queued successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue training request: {str(e)}")
```

### 3. Implement Priority Queues

```python
# In core/celery_app.py, configure priority queues
celery_app.conf.update(
    task_routes={
        'core.celery_tasks.train_task': {'queue': 'training'},
        'core.celery_tasks.query_task': {'queue': 'queries'},
        'core.celery_tasks.norms_update_task': {'queue': 'background'}
    },
    task_queue_max_priority=10,
    task_default_priority=5
)

# Add priority parameter to tasks
@celery_app.task(bind=True, name='core.celery_tasks.train_task')
def train_task(self, custom_dir: Optional[str] = None, priority: int = 5):
    """Celery task for RAG training with priority support"""
    # Set task priority
    self.update_state(priority=priority)
    # ... rest of implementation
```

### 4. Add Rate Limiting and Resource Management

```python
# In core/bldr_api.py, add resource management
class ResourceManager:
    def __init__(self):
        self.active_training_tasks = 0
        self.max_concurrent_training = 2  # Limit concurrent training tasks
        self.lock = asyncio.Lock()
    
    async def acquire_training_slot(self):
        async with self.lock:
            if self.active_training_tasks < self.max_concurrent_training:
                self.active_training_tasks += 1
                return True
            return False
    
    async def release_training_slot(self):
        async with self.lock:
            if self.active_training_tasks > 0:
                self.active_training_tasks -= 1

resource_manager = ResourceManager()

# Modify train endpoint to use resource management
@app.post("/train")
async def train(request: Request, custom_dir: Optional[str] = None, priority: int = 5, credentials: dict = Depends(verify_api_token)):
    """Submit training request with resource management"""
    # Try to acquire training slot
    if not await resource_manager.acquire_training_slot():
        raise HTTPException(
            status_code=429, 
            detail="Too many training requests. Please try again later."
        )
    
    try:
        # Import Celery task
        from core.celery_tasks import train_task
        
        # Send task to Celery worker with priority
        task = train_task.delay(custom_dir, priority=priority)
        
        # Log task in Neo4j
        log_task_to_neo4j(task.id, 'train', custom_dir, priority)
        
        return {
            "status": "queued", 
            "task_id": task.id,
            "message": "Training request queued successfully"
        }
    except Exception as e:
        await resource_manager.release_training_slot()
        raise HTTPException(status_code=500, detail=f"Failed to queue training request: {str(e)}")
```

### 5. Worker Configuration for Priority Handling

```bash
# Start workers with priority handling
celery -A core.celery_app worker --loglevel=info --queues=training -c 2
celery -A core.celery_app worker --loglevel=info --queues=queries -c 5
celery -A core.celery_app worker --loglevel=info --queues=background -c 1
```

## Benefits of Full Celery Integration

1. **Proper Queue Management**: All requests go through Celery's robust queuing system
2. **Priority Handling**: High-priority requests can be processed before low-priority ones
3. **Resource Control**: Limit concurrent training tasks to prevent system overload
4. **Better Monitoring**: Comprehensive task tracking and progress reporting
5. **Scalability**: Easy to add more workers for specific task types
6. **Fault Tolerance**: Failed tasks can be retried automatically

## Implementation Steps

1. Create new Celery tasks for training and query operations
2. Modify API endpoints to submit tasks to Celery instead of using BackgroundTasks
3. Implement priority queues and resource management
4. Update frontend to handle task IDs and poll for status
5. Add rate limiting to prevent queue overload
6. Configure workers for optimal resource utilization

This approach would provide a more robust and scalable solution for handling multiple users and requests with a single LM Studio instance.