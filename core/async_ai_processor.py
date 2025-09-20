#!/usr/bin/env python3
"""
Async AI Processor for Bldr API
True async processing without blocking the main FastAPI server
"""

import asyncio
import aiohttp
import json
import time
import logging
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

# Import process tracking system
from core.process_tracker import get_process_tracker, ProcessType, ProcessStatus

logger = logging.getLogger(__name__)

# Get process tracker instance
process_tracker = get_process_tracker()

@dataclass
class AITaskResult:
    """Result of an AI task execution"""
    task_id: str
    status: str  # "pending", "processing", "completed", "error", "timeout"
    result: Optional[str] = None
    error: Optional[str] = None
    progress: int = 0
    stage: str = "queued"
    created_at: float = 0.0
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

class AsyncAIProcessor:
    """Asynchronous AI processing manager with WebSocket updates"""
    
    def __init__(self, lm_studio_url: Optional[str] = None, websocket_manager=None):
        self.lm_studio_url = lm_studio_url or os.getenv("LLM_BASE_URL", "http://localhost:1234")
        self.websocket_manager = websocket_manager
        self.active_tasks: Dict[str, AITaskResult] = {}
        self.max_concurrent_tasks = 3  # Conservative limit for stability
        self.semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        self.cleanup_interval = 300  # Clean up every 5 minutes
        
        # Start cleanup task
        asyncio.create_task(self._periodic_cleanup())
        
    async def submit_ai_request(self, task_id: str, prompt: str, model: str = "deepseek/deepseek-r1-0528-qwen3-8b", **kwargs) -> AITaskResult:
        """Submit AI request for async processing"""
        
        # Handle multimedia data
        enhanced_prompt = self._prepare_multimedia_prompt(prompt, **kwargs)
        
        # Create task result
        task_result = AITaskResult(
            task_id=task_id,
            status="pending",
            stage="queued"
        )
        self.active_tasks[task_id] = task_result
        
        # Register process with process tracker
        process_tracker.start_process(
            process_id=task_id,
            process_type=ProcessType.AI_TASK,
            name=f"AI Task: {task_id}",
            description=f"AI processing task with model {model}",
            metadata={
                "model": model,
                "prompt_length": len(prompt),
                "task_type": "ai_request"
            }
        )
        
        # Send initial WebSocket update
        await self._send_websocket_update(task_result, "AI request queued")
        
        # Process in background (fire and forget)
        asyncio.create_task(self._process_ai_request(task_result, enhanced_prompt, model))
        
        return task_result
    
    def _prepare_multimedia_prompt(self, prompt: str, **kwargs) -> str:
        """Prepare prompt with multimedia data context"""
        enhanced_prompt = prompt
        
        # Handle image data
        if kwargs.get('image_data'):
            enhanced_prompt = f"[IMAGE PROVIDED - Analyze this image] {enhanced_prompt}"
            
        # Handle voice data  
        if kwargs.get('voice_data'):
            enhanced_prompt = f"[VOICE MESSAGE PROVIDED - Transcribe and analyze] {enhanced_prompt}"
            
        # Handle document data
        if kwargs.get('document_data'):
            doc_name = kwargs.get('document_name', 'document.pdf')
            file_ext = doc_name.split('.')[-1].lower() if '.' in doc_name else 'unknown'
            
            if file_ext in ['pdf', 'doc', 'docx']:
                enhanced_prompt = f"[DOCUMENT: {doc_name} - Extract text and analyze construction requirements] {enhanced_prompt}"
            elif file_ext in ['xls', 'xlsx', 'csv']:
                enhanced_prompt = f"[SPREADSHEET: {doc_name} - Analyze data and construction metrics] {enhanced_prompt}"
            elif file_ext in ['dwg', 'dxf']:
                enhanced_prompt = f"[DRAWING: {doc_name} - Analyze architectural/construction drawing] {enhanced_prompt}"
            else:
                enhanced_prompt = f"[FILE: {doc_name} - Analyze construction-related content] {enhanced_prompt}"
                
        return enhanced_prompt
    
    async def _process_ai_request(self, task_result: AITaskResult, prompt: str, model: str):
        """Process AI request asynchronously with semaphore control"""
        async with self.semaphore:  # Limit concurrent requests
            try:
                task_result.status = "processing"
                task_result.stage = "connecting"
                task_result.progress = 10
                await self._send_websocket_update(task_result, "Connecting to AI service")
                
                # Update process tracker
                process_tracker.update_process(
                    task_result.task_id,
                    status=ProcessStatus.RUNNING,
                    progress=10,
                    metadata_update={"stage": "connecting"}
                )
                
                # Use aiohttp for truly async HTTP requests
                timeout = aiohttp.ClientTimeout(total=1800)  # 30 minutes timeout
                
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
                    await self._send_websocket_update(task_result, "Sending request to AI model")
                    
                    # Update process tracker
                    process_tracker.update_process(
                        task_result.task_id,
                        progress=20,
                        metadata_update={"stage": "sending_request"}
                    )
                    
                    # Send periodic updates during processing
                    update_task = asyncio.create_task(self._send_periodic_updates(task_result))
                    
                    try:
                        async with session.post(endpoint, json=payload, headers=headers) as response:
                            if response.status == 200:
                                result = await response.json()
                                ai_response = None
                                if isinstance(result, dict):
                                    choices = result.get('choices')
                                    if isinstance(choices, list) and choices:
                                        first = choices[0] if isinstance(choices[0], dict) else {}
                                        msg = first.get('message') if isinstance(first, dict) else None
                                        if isinstance(msg, dict):
                                            ai_response = msg.get('content')
                                        if not ai_response and isinstance(first, dict):
                                            ai_response = first.get('text')
                                    if not ai_response:
                                        ai_response = result.get('content') or result.get('message')
                                ai_response = ai_response or ""
                                
                                task_result.result = ai_response
                                task_result.status = "completed"
                                task_result.stage = "completed"
                                task_result.progress = 100
                                await self._send_websocket_update(task_result, "AI response completed", is_final=True)
                                
                                # Update process tracker
                                process_tracker.update_process(
                                    task_result.task_id,
                                    status=ProcessStatus.COMPLETED,
                                    progress=100,
                                    metadata_update={"stage": "completed", "response_length": len(ai_response)}
                                )
                            else:
                                error_text = await response.text()
                                task_result.error = f"LM Studio error: {response.status} - {error_text}"
                                task_result.status = "error"
                                task_result.stage = "error"
                                await self._send_websocket_update(task_result, f"AI service error: {response.status}")
                                
                                # Update process tracker
                                process_tracker.update_process(
                                    task_result.task_id,
                                    status=ProcessStatus.FAILED,
                                    metadata_update={"stage": "error", "error": task_result.error}
                                )
                                
                    except asyncio.TimeoutError:
                        task_result.error = "AI request timed out after 30 minutes"
                        task_result.status = "timeout"
                        task_result.stage = "timeout"
                        await self._send_websocket_update(task_result, "Request timed out")
                        
                        # Update process tracker
                        process_tracker.update_process(
                            task_result.task_id,
                            status=ProcessStatus.TIMEOUT,
                            metadata_update={"stage": "timeout", "error": task_result.error}
                        )
                        
                    except Exception as e:
                        logger.error(f"AI processing error for task {task_result.task_id}: {str(e)}")
                        task_result.error = f"AI processing error: {str(e)}"
                        task_result.status = "error"
                        task_result.stage = "error"
                        await self._send_websocket_update(task_result, f"Processing error: {str(e)}")
                        
                        # Update process tracker
                        process_tracker.update_process(
                            task_result.task_id,
                            status=ProcessStatus.FAILED,
                            metadata_update={"stage": "error", "error": task_result.error}
                        )
                        
                    finally:
                        update_task.cancel()
                        
            except Exception as e:
                logger.error(f"AI processing error for task {task_result.task_id}: {str(e)}")
                task_result.error = f"AI processing error: {str(e)}"
                task_result.status = "error"
                task_result.stage = "error"
                await self._send_websocket_update(task_result, f"Processing error: {str(e)}")
                
                # Update process tracker
                process_tracker.update_process(
                    task_result.task_id,
                    status=ProcessStatus.FAILED,
                    metadata_update={"stage": "error", "error": task_result.error}
                )
    
    async def _send_periodic_updates(self, task_result: AITaskResult):
        """Send periodic progress updates"""
        start_time = time.time()
        
        try:
            while task_result.status == "processing":
                await asyncio.sleep(15)  # Update every 15 seconds
                
                if task_result.status != "processing":  # Check again after sleep
                    break
                    
                elapsed_minutes = int((time.time() - start_time) / 60)
                task_result.stage = f"processing"
                task_result.progress = min(90, 20 + (elapsed_minutes * 2))  # Gradually increase progress
                
                await self._send_websocket_update(
                    task_result, 
                    f"AI processing in progress... {elapsed_minutes} minutes elapsed"
                )
                
                # Update process tracker
                process_tracker.update_process(
                    task_result.task_id,
                    progress=task_result.progress,
                    metadata_update={"stage": task_result.stage, "elapsed_minutes": elapsed_minutes}
                )
                
        except asyncio.CancelledError:
            pass  # Task completed, stop sending updates
    
    async def _send_websocket_update(self, task_result: AITaskResult, message: str, is_final: bool = False):
        """Send WebSocket update if manager is available"""
        if self.websocket_manager:
            try:
                update_data = {
                    "type": "ai_task_update",
                    "task_id": task_result.task_id,
                    "status": task_result.status,
                    "stage": task_result.stage,
                    "progress": task_result.progress,
                    "message": message,
                    "timestamp": time.time()
                }
                
                if is_final and task_result.result:
                    update_data["result"] = task_result.result
                    
                if task_result.error:
                    update_data["error"] = task_result.error
                
                await self.websocket_manager.broadcast(json.dumps(update_data))
            except Exception as e:
                logger.error(f"WebSocket update error: {str(e)}")
    
    def get_task_status(self, task_id: str) -> Optional[AITaskResult]:
        """Get status of a specific task"""
        return self.active_tasks.get(task_id)
    
    def list_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """List all active tasks"""
        return {
            task_id: asdict(task_result) 
            for task_id, task_result in self.active_tasks.items()
        }
    
    async def _periodic_cleanup(self):
        """Periodically clean up old completed tasks"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_completed_tasks()
            except Exception as e:
                logger.error(f"Cleanup error: {str(e)}")
    
    async def _cleanup_completed_tasks(self, max_age_seconds: int = 3600):
        """Clean up completed tasks older than max_age_seconds"""
        current_time = time.time()
        to_remove = []
        
        for task_id, task_result in self.active_tasks.items():
            if task_result.status in ["completed", "error", "timeout"]:
                age = current_time - task_result.created_at
                if age > max_age_seconds:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            self.active_tasks.pop(task_id, None)
            logger.info(f"Cleaned up old task: {task_id}")
        
        # Also limit total number of tasks
        if len(self.active_tasks) > 1000:
            # Remove oldest completed tasks
            completed_tasks = [
                (task_id, task_result) 
                for task_id, task_result in self.active_tasks.items() 
                if task_result.status in ["completed", "error", "timeout"]
            ]
            completed_tasks.sort(key=lambda x: x[1].created_at)
            
            for task_id, _ in completed_tasks[:-500]:  # Keep only 500 most recent
                self.active_tasks.pop(task_id, None)

# Global instance
ai_processor_instance = None

def get_ai_processor() -> AsyncAIProcessor:
    """Get or create global AI processor instance"""
    global ai_processor_instance
    if ai_processor_instance is None:
        # Import here to avoid circular imports
        try:
            from core.websocket_manager import manager
            ai_processor_instance = AsyncAIProcessor(websocket_manager=manager)
        except ImportError:
            ai_processor_instance = AsyncAIProcessor()
    return ai_processor_instance