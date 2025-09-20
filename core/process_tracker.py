"""Enterprise Process Tracking System for Bldr API
Unified process tracking for different operation types with real-time WebSocket updates
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class ProcessType(Enum):
    """Types of processes that can be tracked"""
    AI_TASK = "ai_task"
    RAG_TRAINING = "rag_training"
    DOCUMENT_PROCESSING = "document_processing"
    SCHEDULED_TASK = "scheduled_task"
    BACKGROUND_JOB = "background_job"
    TOOLS_EXECUTION = "tools_execution"

class ProcessStatus(Enum):
    """Status of a process"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass
class ProcessInfo:
    """Information about a tracked process"""
    process_id: str
    process_type: ProcessType
    status: ProcessStatus
    name: str
    description: str = ""
    progress: int = 0
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

class ProcessTracker:
    """Enterprise process tracking system with WebSocket integration"""
    
    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager
        self.processes: Dict[str, ProcessInfo] = {}
        self.max_processes = 1000
        self.cleanup_interval = 300  # 5 minutes
        self.cleanup_task: Optional[asyncio.Task] = None
        
    def start_cleanup_task(self):
        """Start the periodic cleanup task (should be called when event loop is available)"""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    def start_process(self, process_id: str, process_type: ProcessType, name: str, description: str = "", metadata: Optional[Dict[str, Any]] = None) -> ProcessInfo:
        """Start tracking a new process"""
        process_info = ProcessInfo(
            process_id=process_id,
            process_type=process_type,
            status=ProcessStatus.PENDING,
            name=name,
            description=description,
            metadata=metadata or {}
        )
        self.processes[process_id] = process_info
        self._send_websocket_update_async(process_info, "Process started")
        return process_info
    
    def update_process(self, process_id: str, status: Optional[ProcessStatus] = None, progress: Optional[int] = None, 
                      error_message: Optional[str] = None, metadata_update: Optional[Dict[str, Any]] = None) -> Optional[ProcessInfo]:
        """Update process status"""
        if process_id not in self.processes:
            logger.warning(f"Process {process_id} not found")
            return None
            
        process_info = self.processes[process_id]
        
        # Update fields if provided
        if status is not None:
            process_info.status = status
            if status == ProcessStatus.RUNNING and process_info.started_at is None:
                process_info.started_at = time.time()
            elif status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED, ProcessStatus.CANCELLED, ProcessStatus.TIMEOUT]:
                process_info.completed_at = time.time()
                
        if progress is not None:
            process_info.progress = progress
            
        if error_message is not None:
            process_info.error_message = error_message
            
        if metadata_update is not None:
            process_info.metadata.update(metadata_update)
        
        self._send_websocket_update_async(process_info, "Process updated")
        return process_info
    
    def get_process(self, process_id: str) -> Optional[ProcessInfo]:
        """Get process information by ID"""
        return self.processes.get(process_id)
    
    def list_processes(self, process_type: Optional[ProcessType] = None, status: Optional[ProcessStatus] = None) -> List[Dict[str, Any]]:
        """List all processes, optionally filtered by type and status"""
        result = []
        for process_info in self.processes.values():
            # Apply filters
            if process_type and process_info.process_type != process_type:
                continue
            if status and process_info.status != status:
                continue
                
            result.append(asdict(process_info))
        return result
    
    def cancel_process(self, process_id: str) -> bool:
        """Cancel a process"""
        if process_id not in self.processes:
            return False
            
        process_info = self.processes[process_id]
        process_info.status = ProcessStatus.CANCELLED
        process_info.completed_at = time.time()
        self._send_websocket_update_async(process_info, "Process cancelled")
        return True
    
    def _send_websocket_update_async(self, process_info: ProcessInfo, message: str):
        """Schedule WebSocket update if manager is available and event loop is running"""
        if self.websocket_manager:
            try:
                # Check if there's a running event loop
                loop = asyncio.get_running_loop()
                # Schedule the async update
                loop.create_task(self._send_websocket_update(process_info, message))
            except RuntimeError:
                # No event loop running, skip WebSocket update
                pass
    
    async def _send_websocket_update(self, process_info: ProcessInfo, message: str):
        """Send WebSocket update if manager is available"""
        if self.websocket_manager:
            try:
                update_data = {
                    "type": "process_update",
                    "process_id": process_info.process_id,
                    "process_type": process_info.process_type.value,
                    "status": process_info.status.value,
                    "name": process_info.name,
                    "progress": process_info.progress,
                    "message": message,
                    "timestamp": time.time(),
                    "metadata": process_info.metadata
                }
                
                if process_info.error_message:
                    update_data["error_message"] = process_info.error_message
                
                await self.websocket_manager.broadcast(json.dumps(update_data))
            except Exception as e:
                logger.error(f"WebSocket update error: {str(e)}")
    
    async def _periodic_cleanup(self):
        """Periodically clean up old completed processes"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_completed_processes()
            except Exception as e:
                logger.error(f"Process cleanup error: {str(e)}")
    
    async def _cleanup_completed_processes(self, max_age_seconds: int = 3600):
        """Clean up completed processes older than max_age_seconds"""
        current_time = time.time()
        to_remove = []
        
        for process_id, process_info in self.processes.items():
            if process_info.status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED, ProcessStatus.CANCELLED, ProcessStatus.TIMEOUT]:
                age = current_time - (process_info.completed_at or process_info.created_at)
                if age > max_age_seconds:
                    to_remove.append(process_id)
        
        for process_id in to_remove:
            self.processes.pop(process_id, None)
            logger.info(f"Cleaned up old process: {process_id}")
        
        # Also limit total number of processes
        if len(self.processes) > self.max_processes:
            # Remove oldest completed processes
            completed_processes = [
                (process_id, process_info) 
                for process_id, process_info in self.processes.items() 
                if process_info.status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED, ProcessStatus.CANCELLED, ProcessStatus.TIMEOUT]
            ]
            completed_processes.sort(key=lambda x: x[1].completed_at or x[1].created_at)
            
            for process_id, _ in completed_processes[:-500]:  # Keep only 500 most recent
                self.processes.pop(process_id, None)

# Global instance
process_tracker_instance = None

def get_process_tracker() -> ProcessTracker:
    """Get or create global process tracker instance"""
    global process_tracker_instance
    if process_tracker_instance is None:
        # Import here to avoid circular imports
        try:
            from core.websocket_manager import manager
            process_tracker_instance = ProcessTracker(websocket_manager=manager)
        except ImportError:
            process_tracker_instance = ProcessTracker()
    return process_tracker_instance