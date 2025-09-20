#!/usr/bin/env python3
"""
Test script for AI intelligent polling implementation
"""

import asyncio
import time
from threading import Thread, Event

# Mock send_stage_update function for testing
async def send_stage_update(stage: str, log: str, progress: int = 0, data: str = "", status: str = "processing"):
    """Mock function to simulate sending updates via WebSocket"""
    print(f"🔄 Update - Stage: {stage}, Log: {log}, Progress: {progress}%, Status: {status}")
    if data:
        print(f"   Data: {data[:100]}..." if len(data) > 100 else f"   Data: {data}")

class MockAICall:
    """Mock AICall class for testing"""
    def __init__(self, prompt: str, model: str):
        self.prompt = prompt
        self.model = model

async def run_ai_with_updates(task_id: str, request_data: MockAICall):
    """Test implementation of AI request with periodic status updates"""
    try:
        import requests
        import json
        import os
        
        # Send initial update
        await send_stage_update(task_id, "AI request started", 0)
        
        # For testing, we'll simulate the request instead of actually making it
        print(f"📝 Simulating AI request with prompt: '{request_data.prompt}' and model: '{request_data.model}'")
        
        # Set maximum timeout to 2 hours (7200 seconds)
        max_timeout = 10  # For testing, we'll use 10 seconds instead of 2 hours
        check_interval = 2  # For testing, we'll check every 2 seconds instead of 5 minutes
        
        # Create an event to signal when the request is complete
        request_complete = Event()
        response_data = {"status": "pending", "result": None, "error": None}
        
        # Keep a reference to the loop for use in the thread
        loop = asyncio.get_event_loop()
        
        # Function to make the actual request in a separate thread
        def make_request():
            try:
                # Send update that we're sending the request
                asyncio.run_coroutine_threadsafe(
                    send_stage_update(task_id, "Sending request to LM Studio", 10), 
                    loop
                )
                
                # Simulate processing time
                time.sleep(5)  # Simulate 5 seconds of processing
                
                # Simulate successful response
                response_data["result"] = "This is a simulated AI response to the prompt: " + request_data.prompt
                response_data["status"] = "completed"
            except Exception as e:
                # Send general error update
                error_msg = f"AI processing error: {str(e)}"
                response_data["error"] = error_msg
                response_data["status"] = "error"
            finally:
                request_complete.set()
        
        # Start the request in a separate thread
        request_thread = Thread(target=make_request)
        request_thread.start()
        
        # Polling loop - check every 5 minutes while request is processing
        start_time = time.time()
        last_update_time = start_time
        
        while not request_complete.is_set():
            current_time = time.time()
            
            # Check if we've exceeded the maximum timeout
            if current_time - start_time > max_timeout:
                response_data["error"] = "AI request timed out after 2 hours"
                response_data["status"] = "timeout"
                break
            
            # Send periodic status updates every 5 minutes
            if current_time - last_update_time >= check_interval:
                elapsed_seconds = int(current_time - start_time)
                asyncio.run_coroutine_threadsafe(
                    send_stage_update(
                        task_id, 
                        f"AI request still processing... {elapsed_seconds} seconds elapsed", 
                        min(90, 10 + (elapsed_seconds // 2) * 5)  # Progress increases gradually
                    ), 
                    loop
                )
                last_update_time = current_time
            
            # Small sleep to prevent busy waiting
            await asyncio.sleep(1)
        
        # Wait for the request thread to complete
        request_thread.join(timeout=10)  # Wait up to 10 seconds for thread to finish
        
        # Send final update based on the result
        if response_data["status"] == "completed":
            await send_stage_update(task_id, "AI response received", 100, response_data["result"], "completed")
        elif response_data["status"] == "timeout":
            await send_stage_update(task_id, "Timeout", 0, response_data["error"], "timeout")
        elif response_data["status"] == "error":
            await send_stage_update(task_id, "Error", 0, response_data["error"], "error")
        else:
            await send_stage_update(task_id, "Unknown Error", 0, "Request completed with unknown status", "error")
            
    except Exception as e:
        error_msg = f"AI task error: {str(e)}"
        await send_stage_update(task_id, "Task Error", 0, error_msg, "error")

async def main():
    """Main test function"""
    print("🚀 Testing AI Intelligent Polling Implementation")
    
    # Create mock AI call
    mock_request = MockAICall(
        prompt="Explain the importance of construction norms in building safety.",
        model="llama3.1"
    )
    
    # Run the AI request with updates
    await run_ai_with_updates("test_task_123", mock_request)
    
    print("✅ Test completed")

if __name__ == "__main__":
    asyncio.run(main())