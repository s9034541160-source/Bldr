import asyncio
import logging
import signal
import sys
from core.bldr_api import app
from fastapi.middleware.cors import CORSMiddleware

# Import Celery app
from core.celery_app import celery_app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_exception(loop, context):
    """Handle uncaught exceptions in the event loop"""
    msg = context.get("exception", context["message"])
    logger.error(f"Caught exception: {msg}")
    logger.info("Shutting down gracefully...")
    loop.stop()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://localhost:3005"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )
    
    try:
        import uvicorn
        
        # Run the FastAPI app
        uvicorn.run(app, host="localhost", port=8000)
        
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Error starting server: {e}", exc_info=True)
        sys.exit(1)