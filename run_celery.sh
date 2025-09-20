#!/bin/bash

# Bldr Empire v2 - Celery Services Startup Script
# This script starts all required services for the Bldr Empire system

echo "🚀 Starting Bldr Empire v2 Services..."

# Check if Redis is installed
if ! command -v redis-server &> /dev/null
then
    echo "⚠️  Redis not found. Please install Redis first:"
    echo "   Ubuntu/Debian: sudo apt-get install redis-server"
    echo "   macOS: brew install redis"
    echo "   Or use Docker: docker run -p 6379:6379 redis"
    exit 1
fi

# Start Redis server in background
echo "🔄 Starting Redis server..."
redis-server --daemonize yes
sleep 2

# Check if Redis is running
if redis-cli ping &> /dev/null
then
    echo "✅ Redis server is running"
else
    echo "❌ Failed to start Redis server"
    exit 1
fi

# Start Celery worker in background
echo "🔄 Starting Celery worker..."
celery -A core.celery_app worker --loglevel=info --concurrency=4 &
CELERY_WORKER_PID=$!
sleep 3

# Start Celery beat in background
echo "🔄 Starting Celery beat..."
celery -A core.celery_app beat --loglevel=info &
CELERY_BEAT_PID=$!
sleep 2

# Start FastAPI server
echo "🔄 Starting FastAPI server..."
python -m core.main &
FASTAPI_PID=$!
sleep 3

echo "✅ All services started successfully!"
echo "   Redis: localhost:6379"
echo "   Celery Worker PID: $CELERY_WORKER_PID"
echo "   Celery Beat PID: $CELERY_BEAT_PID"
echo "   FastAPI Server: http://localhost:8000"
echo ""
echo "💡 To stop services, press Ctrl+C or run:"
echo "   pkill -f celery"
echo "   pkill -f uvicorn"
echo "   redis-cli shutdown"

# Wait for processes to complete
wait $CELERY_WORKER_PID $CELERY_BEAT_PID $FASTAPI_PID