#!/usr/bin/env python3
"""
Simple script to start the API server for testing
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set the Python path to include the core directory
os.environ['PYTHONPATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core')

if __name__ == "__main__":
    try:
        # Import and run the API server
        from core.bldr_api import app
        import uvicorn
        
        print("🚀 Starting Bldr API server...")
        uvicorn.run("core.bldr_api:app", host="localhost", port=8000, reload=True)
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        import traceback
        traceback.print_exc()