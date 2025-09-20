"""Demo of Enterprise Process Monitoring System
Example showing how to integrate process tracking with different operations
"""

import asyncio
import time
import uuid
import sys
import os
from typing import Dict, Any

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.process_tracker import get_process_tracker, ProcessType, ProcessStatus
from core.retry_system import get_retry_system, RetryConfig

# Get instances
process_tracker = get_process_tracker()
retry_system = get_retry_system()

# Register retry configurations for different process types
retry_system.register_retry_config("document_processing", RetryConfig(max_attempts=3, initial_delay=1.0, max_delay=10.0))
retry_system.register_retry_config("data_analysis", RetryConfig(max_attempts=2, initial_delay=2.0, max_delay=30.0))

def simulate_document_processing(document_id: str) -> bool:
    """Simulate document processing that might fail"""
    print(f"Processing document {document_id}...")
    
    # Simulate some work
    time.sleep(2)
    
    # Simulate random failure (20% chance)
    import random
    if random.random() < 0.2:
        raise Exception(f"Failed to process document {document_id}")
    
    print(f"Document {document_id} processed successfully")
    return True

async def process_document_with_tracking(document_path: str) -> Dict[str, Any]:
    """Process a document with full process tracking and retry support"""
    process_id = f"doc_proc_{uuid.uuid4().hex[:8]}"
    
    # Start tracking the process
    process_tracker.start_process(
        process_id=process_id,
        process_type=ProcessType.DOCUMENT_PROCESSING,
        name=f"Process Document: {document_path}",
        description=f"Processing document {document_path}",
        metadata={
            "document_path": document_path,
            "start_time": time.time()
        }
    )
    
    try:
        # Update process status
        process_tracker.update_process(
            process_id,
            status=ProcessStatus.RUNNING,
            progress=10,
            metadata_update={"stage": "initializing"}
        )
        
        # Simulate document loading
        time.sleep(1)
        process_tracker.update_process(
            process_id,
            progress=30,
            metadata_update={"stage": "loading"}
        )
        
        # Process document with retry support
        def process_func():
            return simulate_document_processing(document_path)
        
        # Schedule retry if needed
        retry_system.schedule_retry(
            process_id,
            "document_processing",
            process_func
        )
        
        # Simulate processing
        time.sleep(2)
        process_tracker.update_process(
            process_id,
            progress=70,
            metadata_update={"stage": "processing"}
        )
        
        # Simulate finalization
        time.sleep(1)
        process_tracker.update_process(
            process_id,
            progress=90,
            metadata_update={"stage": "finalizing"}
        )
        
        # Complete process
        process_info = process_tracker.get_process(process_id)
        duration = time.time() - process_info.created_at if process_info else 0
        
        process_tracker.update_process(
            process_id,
            status=ProcessStatus.COMPLETED,
            progress=100,
            metadata_update={
                "stage": "completed",
                "end_time": time.time(),
                "duration": duration
            }
        )
        
        return {
            "process_id": process_id,
            "status": "success",
            "message": f"Document {document_path} processed successfully"
        }
        
    except Exception as e:
        # Update process status as failed
        process_tracker.update_process(
            process_id,
            status=ProcessStatus.FAILED,
            metadata_update={
                "stage": "error",
                "error": str(e),
                "end_time": time.time()
            }
        )
        
        return {
            "process_id": process_id,
            "status": "error",
            "message": f"Failed to process document {document_path}: {str(e)}"
        }

async def run_demo():
    """Run demonstration of process monitoring"""
    print("🚀 Starting Process Monitoring Demo")
    print("=" * 50)
    
    # Process some documents
    documents = [
        "document1.pdf",
        "document2.docx",
        "document3.txt",
        "document4.xlsx"
    ]
    
    tasks = []
    for doc in documents:
        task = process_document_with_tracking(doc)
        tasks.append(task)
    
    # Run all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Print results
    print("\n📊 Processing Results:")
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"  ❌ Document {documents[i]}: Error - {result}")
        elif isinstance(result, dict):
            print(f"  ✅ Document {documents[i]}: {result['message']}")
        else:
            print(f"  ℹ️ Document {documents[i]}: {result}")
    
    # Show process list
    print("\n📋 Current Processes:")
    all_processes = process_tracker.list_processes()
    for process in all_processes:
        print(f"  - {process['process_id']}: {process['name']} - {process['status']} ({process['progress']}%)")
    
    # Show process types and statuses
    print("\n📋 Available Process Types:")
    for process_type in ProcessType:
        print(f"  - {process_type.value}")
    
    print("\n📋 Available Process Statuses:")
    for status in ProcessStatus:
        print(f"  - {status.value}")
    
    print("\n✅ Demo completed!")

if __name__ == "__main__":
    asyncio.run(run_demo())