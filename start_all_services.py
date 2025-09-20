#!/usr/bin/env python3
"""
Script to start all Bldr Empire v2 services:
1. Backend API server (FastAPI on port 8000)
2. Frontend dashboard (React on port 3000)
3. Telegram bot (if token is provided)
"""
import os
import subprocess
import sys
import time
from pathlib import Path

def start_backend():
    """Start the backend API server"""
    print("🚀 Starting Backend API Server...")
    backend_process = subprocess.Popen([
        sys.executable, "-m", "core.main"
    ], cwd=".", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait a bit to see if it starts successfully
    time.sleep(3)
    
    if backend_process.poll() is None:
        print("✅ Backend API Server started successfully on http://localhost:8000")
        return backend_process
    else:
        stdout, stderr = backend_process.communicate()
        print("❌ Backend API Server failed to start:")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        return None

def start_frontend():
    """Start the frontend dashboard"""
    print("🚀 Starting Frontend Dashboard...")
    
    # Check if we're on Windows or Unix-like system
    if os.name == 'nt':  # Windows
        frontend_process = subprocess.Popen([
            "npm", "run", "dev"
        ], cwd="./web/bldr_dashboard", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    else:  # Unix-like
        frontend_process = subprocess.Popen([
            "npm", "run", "dev"
        ], cwd="./web/bldr_dashboard", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait a bit to see if it starts successfully
    time.sleep(3)
    
    if frontend_process.poll() is None:
        print("✅ Frontend Dashboard started successfully on http://localhost:3000")
        return frontend_process
    else:
        stdout, stderr = frontend_process.communicate()
        print("❌ Frontend Dashboard failed to start:")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        return None

def start_telegram_bot():
    """Start the Telegram bot if token is available"""
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not telegram_token or telegram_token == 'YOUR_TELEGRAM_BOT_TOKEN_HERE':
        print("⚠️  TELEGRAM_BOT_TOKEN not set. Skipping Telegram bot start.")
        print("   To enable Telegram bot, set TELEGRAM_BOT_TOKEN environment variable.")
        return None
    
    print("🚀 Starting Telegram Bot...")
    bot_process = subprocess.Popen([
        sys.executable, "integrations/telegram_bot.py"
    ], cwd=".", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait a bit to see if it starts successfully
    time.sleep(3)
    
    if bot_process.poll() is None:
        print("✅ Telegram Bot started successfully")
        return bot_process
    else:
        stdout, stderr = bot_process.communicate()
        print("❌ Telegram Bot failed to start:")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        return None

def main():
    print("🚀 Bldr Empire v2 - Starting All Services")
    print("=" * 50)
    
    # Change to the project directory
    os.chdir(Path(__file__).parent)
    
    # Start services
    backend_process = start_backend()
    frontend_process = start_frontend()
    bot_process = start_telegram_bot()
    
    # Keep the script running
    try:
        print("\n🎯 All services started!")
        print("   - Backend API: http://localhost:8000")
        print("   - Frontend Dashboard: http://localhost:3000")
        if bot_process:
            print("   - Telegram Bot: Enabled")
        else:
            print("   - Telegram Bot: Disabled (no token)")
        
        print("\nPress Ctrl+C to stop all services")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        
        # Terminate processes
        if backend_process:
            backend_process.terminate()
            backend_process.wait()
            print("✅ Backend API Server stopped")
            
        if frontend_process:
            frontend_process.terminate()
            frontend_process.wait()
            print("✅ Frontend Dashboard stopped")
            
        if bot_process:
            bot_process.terminate()
            bot_process.wait()
            print("✅ Telegram Bot stopped")
            
        print("👋 All services stopped. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()