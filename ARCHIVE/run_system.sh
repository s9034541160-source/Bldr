#!/bin/bash

# Bldr Empire v2 - Complete System Startup Script
# This script starts all required services for the full multi-agent system

echo "🚀 Starting Bldr Empire v2 Complete System..."
echo "=========================================="

# Function to check if a port is in use
check_port() {
    local port=$1
    if command -v netstat &> /dev/null; then
        netstat -an | grep ":$port " | grep LISTEN > /dev/null
    elif command -v ss &> /dev/null; then
        ss -tuln | grep ":$port " > /dev/null
    else
        return 1
    fi
}

# Function to kill processes on a port
kill_port() {
    local port=$1
    if command -v lsof &> /dev/null; then
        lsof -i :$port | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null
    elif command -v netstat &> /dev/null; then
        netstat -anop tcp | grep ":$port " | grep LISTEN | awk '{print $5}' | xargs kill -9 2>/dev/null
    fi
}

# Check if running on Windows (Git Bash or WSL)
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "⚠️  This script is designed for Linux/macOS. Please use the Windows batch files:"
    echo "   - one_click_start.bat (for development)"
    echo "   - launch_empire.bat (for Docker deployment)"
    exit 1
fi

# Kill any existing processes on our ports
echo "🔄 Cleaning up existing processes..."
kill_port 1234  # LM Studio
kill_port 6379  # Redis
kill_port 7474  # Neo4j
kill_port 6333  # Qdrant
kill_port 8000  # FastAPI
kill_port 3000  # Frontend

# Wait a moment
sleep 3

# 1. Start LM Studio with required models
echo "🔄 Starting LM Studio with required models..."
echo "⚠️  Please start LM Studio manually and load the following models:"
echo "   - DeepSeek/Qwen3-Coder (for coordinator)"
echo "   - Qwen2.5-VL (for vision analysis)"
echo "   - Mistral (for general tasks)"
echo "LM Studio should be running on http://localhost:1234"
echo ""
read -p "Press Enter when LM Studio is ready..."

# 2. Start Redis
echo "🔄 Starting Redis server..."
if command -v redis-server &> /dev/null; then
    redis-server --daemonize yes
    sleep 2
    
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis server is running on localhost:6379"
    else
        echo "❌ Failed to start Redis server"
        exit 1
    fi
else
    echo "⚠️  Redis not found. Starting with Docker..."
    docker run -d -p 6379:6379 --name redis-bldr redis:alpine
    sleep 5
    
    if docker ps | grep redis-bldr &> /dev/null; then
        echo "✅ Redis container is running on localhost:6379"
    else
        echo "❌ Failed to start Redis container"
        exit 1
    fi
fi

# 3. Start Neo4j with sample data
echo "🔄 Starting Neo4j database..."
if command -v neo4j &> /dev/null; then
    neo4j start
    sleep 10
    
    echo "✅ Neo4j is running on http://localhost:7474"
else
    echo "⚠️  Neo4j not found. Starting with Docker..."
    docker run -d -p 7474:7474 -p 7687:7687 --name neo4j-bldr neo4j:5.20
    sleep 15
    
    if docker ps | grep neo4j-bldr &> /dev/null; then
        echo "✅ Neo4j container is running on http://localhost:7474"
        echo "   Default credentials: neo4j/neo4j (change after first login)"
    else
        echo "❌ Failed to start Neo4j container"
        exit 1
    fi
fi

# 4. Start Qdrant
echo "🔄 Starting Qdrant vector database..."
docker run -d -p 6333:6333 -p 6334:6334 --name qdrant-bldr qdrant/qdrant:v1.7.0
sleep 10

if docker ps | grep qdrant-bldr &> /dev/null; then
    echo "✅ Qdrant is running on http://localhost:6333"
else
    echo "❌ Failed to start Qdrant container"
    exit 1
fi

# 5. Start Celery worker and beat
echo "🔄 Starting Celery services..."
cd /path/to/bldr/empire  # Update this path to your actual project directory

# Start Celery worker
celery -A core.celery_app worker --loglevel=info --concurrency=4 &
CELERY_WORKER_PID=$!
sleep 3

# Start Celery beat
celery -A core.celery_app beat --loglevel=info &
CELERY_BEAT_PID=$!
sleep 2

echo "✅ Celery services started"
echo "   Worker PID: $CELERY_WORKER_PID"
echo "   Beat PID: $CELERY_BEAT_PID"

# 6. Start FastAPI backend
echo "🔄 Starting FastAPI backend..."
uvicorn core.bldr_api:app --host 0.0.0.0 --port 8000 --reload &
FASTAPI_PID=$!
sleep 5

if check_port 8000; then
    echo "✅ FastAPI backend is running on http://localhost:8000"
else
    echo "❌ Failed to start FastAPI backend"
    exit 1
fi

# 7. Start Telegram Bot
echo "🔄 Starting Telegram Bot..."
python integrations/telegram_bot.py &
BOT_PID=$!
sleep 2

echo "✅ Telegram Bot is running"

# 8. Start Frontend
echo "🔄 Starting Frontend Dashboard..."
cd web/bldr_dashboard
npm start &
FRONTEND_PID=$!
cd ../..
sleep 10

if check_port 3000; then
    echo "✅ Frontend Dashboard is running on http://localhost:3000"
else
    echo "❌ Failed to start Frontend Dashboard"
    exit 1
fi

# 9. Prepare test data
echo "🔄 Preparing test data..."
echo "⚠️  Please ensure the following test data is available:"
echo "   - Sample photo (site.jpg for VL analysis)"
echo "   - Sample audio (meeting.mp3 for transcription if Whisper is used)"
echo "   - Sample estimate (smeta.csv with GESN rates)"
echo "   - Sample project LSR in Neo4j"
echo ""
read -p "Press Enter when test data is ready..."

echo ""
echo "🎉 All Bldr Empire v2 services started successfully!"
echo "=================================================="
echo "Services:"
echo "  - LM Studio: http://localhost:1234 (manual start required)"
echo "  - Redis: localhost:6379"
echo "  - Neo4j: http://localhost:7474"
echo "  - Qdrant: http://localhost:6333"
echo "  - FastAPI Backend: http://localhost:8000"
echo "  - Frontend Dashboard: http://localhost:3000"
echo "  - Telegram Bot: Running (token from .env)"
echo ""
echo "💡 To stop all services, press Ctrl+C"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    
    # Kill all background processes
    kill $CELERY_WORKER_PID $CELERY_BEAT_PID $FASTAPI_PID $BOT_PID $FRONTEND_PID 2>/dev/null
    
    # Stop Docker containers
    docker stop redis-bldr neo4j-bldr qdrant-bldr 2>/dev/null
    docker rm redis-bldr neo4j-bldr qdrant-bldr 2>/dev/null
    
    # Stop Redis if running locally
    redis-cli shutdown 2>/dev/null
    
    # Stop Neo4j if running locally
    neo4j stop 2>/dev/null
    
    echo "👋 All services stopped. Goodbye!"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for processes to complete
wait $CELERY_WORKER_PID $CELERY_BEAT_PID $FASTAPI_PID $BOT_PID $FRONTEND_PID