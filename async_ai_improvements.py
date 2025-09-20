#!/usr/bin/env python3
"""
Async AI Processing Improvements for Bldr API
Non-blocking LM Studio requests with proper async handling
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AITaskResult:
    """Result of an AI task execution"""
    task_id: str
    status: str  # "pending", "processing", "completed", "error", "timeout"
    result: Optional[str] = None
    error: Optional[str] = None
    progress: int = 0
    stage: str = "queued"

class AsyncAIProcessor:
    """Asynchronous AI processing manager"""
    
    def __init__(self, lm_studio_url: str = "http://localhost:1234"):
        self.lm_studio_url = lm_studio_url
        self.active_tasks: Dict[str, AITaskResult] = {}
        self.max_concurrent_tasks = 5  # Limit concurrent AI requests
        self.semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        
    async def submit_ai_request(self, task_id: str, prompt: str, model: str = "deepseek/deepseek-r1-0528-qwen3-8b") -> AITaskResult:
        """Submit AI request for async processing"""
        
        # Create task result
        task_result = AITaskResult(
            task_id=task_id,
            status="pending",
            stage="queued"
        )
        self.active_tasks[task_id] = task_result
        
        # Process in background (fire and forget)
        asyncio.create_task(self._process_ai_request(task_result, prompt, model))
        
        return task_result
    
    async def _process_ai_request(self, task_result: AITaskResult, prompt: str, model: str):
        """Process AI request asynchronously"""
        async with self.semaphore:  # Limit concurrent requests
            try:
                task_result.status = "processing"
                task_result.stage = "connecting"
                task_result.progress = 10
                
                # Use aiohttp for truly async HTTP requests
                timeout = aiohttp.ClientTimeout(total=3600)  # 1 hour timeout
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    payload = {
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 8192,
                        "stream": False
                    }
                    
                    headers = {"Content-Type": "application/json"}
                    endpoint = f"{self.lm_studio_url}/v1/chat/completions"
                    
                    task_result.stage = "sending_request"
                    task_result.progress = 20
                    
                    # Send periodic updates during processing
                    update_task = asyncio.create_task(self._send_periodic_updates(task_result))
                    
                    try:
                        async with session.post(endpoint, json=payload, headers=headers) as response:
                            if response.status == 200:
                                result = await response.json()
                                ai_response = result['choices'][0]['message']['content']
                                
                                task_result.result = ai_response
                                task_result.status = "completed"
                                task_result.stage = "completed"
                                task_result.progress = 100
                            else:
                                error_text = await response.text()
                                task_result.error = f"LM Studio error: {response.status} - {error_text}"
                                task_result.status = "error"
                                task_result.stage = "error"
                                
                    except asyncio.TimeoutError:
                        task_result.error = "AI request timed out after 1 hour"
                        task_result.status = "timeout"
                        task_result.stage = "timeout"
                        
                    finally:
                        update_task.cancel()
                        
            except Exception as e:
                logger.error(f"AI processing error for task {task_result.task_id}: {str(e)}")
                task_result.error = f"AI processing error: {str(e)}"
                task_result.status = "error"
                task_result.stage = "error"
    
    async def _send_periodic_updates(self, task_result: AITaskResult):
        """Send periodic progress updates"""
        start_time = time.time()
        
        try:
            while task_result.status == "processing":
                await asyncio.sleep(30)  # Update every 30 seconds
                
                elapsed_minutes = int((time.time() - start_time) / 60)
                task_result.stage = f"processing_{elapsed_minutes}min"
                task_result.progress = min(90, 20 + (elapsed_minutes // 2) * 5)  # Gradually increase progress
                
        except asyncio.CancelledError:
            pass  # Task completed, stop sending updates
    
    def get_task_status(self, task_id: str) -> Optional[AITaskResult]:
        """Get status of a specific task"""
        return self.active_tasks.get(task_id)
    
    def cleanup_completed_tasks(self, max_age_seconds: int = 3600):
        """Clean up completed tasks older than max_age_seconds"""
        current_time = time.time()
        to_remove = []
        
        for task_id, task_result in self.active_tasks.items():
            if task_result.status in ["completed", "error", "timeout"]:
                # For simplicity, remove immediately. In production, add timestamp tracking
                to_remove.append(task_id)
        
        for task_id in to_remove[-100:]:  # Keep only 100 most recent completed tasks
            self.active_tasks.pop(task_id, None)

# Improved API endpoint functions
async def improved_ai_endpoint(ai_processor: AsyncAIProcessor, request_data, credentials):
    """Improved AI endpoint with proper async handling"""
    task_id = f"ai_task_{int(time.time())}_{id(request_data)}"
    
    # Check for multimedia data support
    prompt = request_data.prompt
    model = request_data.model
    
    # Handle multimedia data if present
    if hasattr(request_data, 'image_data') and request_data.image_data:
        prompt = f"[IMAGE_DATA_BASE64: {request_data.image_data[:100]}...] {prompt}"
        
    if hasattr(request_data, 'voice_data') and request_data.voice_data:
        prompt = f"[VOICE_DATA_BASE64: {request_data.voice_data[:100]}...] {prompt}"
        
    if hasattr(request_data, 'document_data') and request_data.document_data:
        doc_name = getattr(request_data, 'document_name', 'document.pdf')
        prompt = f"[DOCUMENT: {doc_name}] [DOCUMENT_DATA_BASE64: {request_data.document_data[:100]}...] {prompt}"
    
    # Submit for async processing
    task_result = await ai_processor.submit_ai_request(task_id, prompt, model)
    
    return {
        "status": "processing",
        "message": "AI request submitted for async processing",
        "task_id": task_id,
        "model": model,
        "estimated_time": "1-30 minutes depending on complexity"
    }

async def task_status_endpoint(ai_processor: AsyncAIProcessor, task_id: str):
    """Get status of an AI task"""
    task_result = ai_processor.get_task_status(task_id)
    
    if not task_result:
        return {"error": "Task not found", "task_id": task_id}
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "stage": task_result.stage,
        "progress": task_result.progress
    }
    
    if task_result.result:
        response["result"] = task_result.result
        
    if task_result.error:
        response["error"] = task_result.error
    
    return response

# Usage example
async def demo_usage():
    """Demonstrate async AI processing"""
    processor = AsyncAIProcessor()
    
    # Submit multiple requests concurrently
    tasks = []
    for i in range(3):
        task_id = f"demo_task_{i}"
        prompt = f"Analyze construction requirements for project {i}"
        task_result = await processor.submit_ai_request(task_id, prompt)
        tasks.append(task_result)
        print(f"✅ Submitted task {task_id}")
    
    # Check status periodically
    while any(task.status == "processing" for task in tasks):
        await asyncio.sleep(5)
        for task in tasks:
            updated_task = processor.get_task_status(task.task_id)
            if updated_task:
                print(f"📊 Task {task.task_id}: {updated_task.status} - {updated_task.stage} ({updated_task.progress}%)")
    
    print("🎉 All tasks completed!")

if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_usage())