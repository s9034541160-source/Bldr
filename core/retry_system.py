"""Enterprise Retry System for Bldr API
Centralized retry mechanism with exponential backoff for failed processes
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_exceptions: tuple = (Exception,)

class RetrySystem:
    """Enterprise retry system with exponential backoff"""
    
    def __init__(self, process_tracker=None):
        self.process_tracker = process_tracker
        self.retry_configs: Dict[str, RetryConfig] = {}
        self.retry_tasks: Dict[str, asyncio.Task] = {}
        self.max_concurrent_retries = 10
        self.semaphore = asyncio.Semaphore(self.max_concurrent_retries)
        
    def register_retry_config(self, process_type: str, config: RetryConfig):
        """Register retry configuration for a specific process type"""
        self.retry_configs[process_type] = config
    
    def schedule_retry(self, process_id: str, process_type: str, retry_func: Callable, *args, **kwargs) -> bool:
        """
        Schedule a retry for a failed process
        
        Args:
            process_id: Unique identifier for the process
            process_type: Type of process (used to lookup retry config)
            retry_func: Function to call for retry
            *args: Arguments for retry function
            **kwargs: Keyword arguments for retry function
            
        Returns:
            bool: True if retry was scheduled, False if not
        """
        if process_type not in self.retry_configs:
            logger.warning(f"No retry config found for process type: {process_type}")
            return False
            
        # Cancel existing retry task if any
        if process_id in self.retry_tasks:
            self.retry_tasks[process_id].cancel()
        
        # Create new retry task
        retry_task = asyncio.create_task(
            self._execute_retry(process_id, process_type, retry_func, *args, **kwargs)
        )
        self.retry_tasks[process_id] = retry_task
        
        logger.info(f"Scheduled retry for process {process_id} of type {process_type}")
        return True
    
    async def _execute_retry(self, process_id: str, process_type: str, retry_func: Callable, *args, **kwargs):
        """Execute retry with exponential backoff"""
        config = self.retry_configs.get(process_type)
        if not config:
            logger.error(f"No retry config for process type: {process_type}")
            return
            
        attempt = 1
        last_error = None
        
        # Update process tracker if available
        if self.process_tracker:
            self.process_tracker.update_process(
                process_id, 
                metadata_update={"retry_attempt": attempt, "max_attempts": config.max_attempts}
            )
        
        while attempt <= config.max_attempts:
            try:
                async with self.semaphore:  # Limit concurrent retries
                    # Calculate delay with exponential backoff
                    delay = self._calculate_delay(config, attempt)
                    
                    if self.process_tracker:
                        self.process_tracker.update_process(
                            process_id,
                            metadata_update={
                                "retry_status": "scheduled",
                                "retry_delay": delay,
                                "retry_scheduled_at": time.time()
                            }
                        )
                    
                    # Wait for delay
                    await asyncio.sleep(delay)
                    
                    if self.process_tracker:
                        self.process_tracker.update_process(
                            process_id,
                            metadata_update={"retry_status": "executing", "retry_started_at": time.time()}
                        )
                    
                    # Execute retry function
                    if asyncio.iscoroutinefunction(retry_func):
                        result = await retry_func(*args, **kwargs)
                    else:
                        result = retry_func(*args, **kwargs)
                    
                    # Success - update process tracker and exit
                    if self.process_tracker:
                        self.process_tracker.update_process(
                            process_id,
                            metadata_update={"retry_status": "success", "retry_completed_at": time.time()}
                        )
                    
                    logger.info(f"Retry successful for process {process_id} on attempt {attempt}")
                    return result
                    
            except config.retry_on_exceptions as e:
                last_error = e
                logger.warning(f"Retry attempt {attempt} failed for process {process_id}: {str(e)}")
                
                if self.process_tracker:
                    self.process_tracker.update_process(
                        process_id,
                        metadata_update={
                            "retry_status": "failed",
                            "retry_error": str(e),
                            "retry_completed_at": time.time()
                        }
                    )
                
                attempt += 1
                if attempt > config.max_attempts:
                    break
                    
            except Exception as e:
                # Unexpected exception - don't retry
                logger.error(f"Unexpected error in retry for process {process_id}: {str(e)}")
                if self.process_tracker:
                    self.process_tracker.update_process(
                        process_id,
                        metadata_update={
                            "retry_status": "error",
                            "retry_error": f"Unexpected error: {str(e)}",
                            "retry_completed_at": time.time()
                        }
                    )
                return
        
        # All retry attempts failed
        logger.error(f"All {config.max_attempts} retry attempts failed for process {process_id}")
        if self.process_tracker:
            self.process_tracker.update_process(
                process_id,
                metadata_update={
                    "retry_status": "exhausted",
                    "retry_error": f"All {config.max_attempts} attempts failed. Last error: {str(last_error)}",
                    "retry_completed_at": time.time()
                }
            )
    
    def _calculate_delay(self, config: RetryConfig, attempt: int) -> float:
        """Calculate delay with exponential backoff and optional jitter"""
        # Exponential backoff: delay = initial_delay * (base ^ (attempt - 1))
        delay = config.initial_delay * (config.exponential_base ** (attempt - 1))
        
        # Cap at max_delay
        delay = min(delay, config.max_delay)
        
        # Add jitter if enabled
        if config.jitter:
            delay = delay * (0.5 + random.random() * 0.5)  # 0.5 to 1.0 multiplier
            
        return delay
    
    def cancel_retry(self, process_id: str) -> bool:
        """Cancel scheduled retry for a process"""
        if process_id in self.retry_tasks:
            self.retry_tasks[process_id].cancel()
            del self.retry_tasks[process_id]
            logger.info(f"Cancelled retry for process {process_id}")
            return True
        return False
    
    def get_retry_status(self, process_id: str) -> Optional[Dict[str, Any]]:
        """Get retry status for a process"""
        if process_id in self.retry_tasks:
            task = self.retry_tasks[process_id]
            return {
                "process_id": process_id,
                "is_running": not task.done(),
                "is_cancelled": task.cancelled()
            }
        return None

# Global instance
retry_system_instance = None

def get_retry_system() -> RetrySystem:
    """Get or create global retry system instance"""
    global retry_system_instance
    if retry_system_instance is None:
        # Import here to avoid circular imports
        try:
            from core.process_tracker import get_process_tracker
            process_tracker = get_process_tracker()
            retry_system_instance = RetrySystem(process_tracker=process_tracker)
        except ImportError:
            retry_system_instance = RetrySystem()
    return retry_system_instance