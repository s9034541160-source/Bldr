#!/usr/bin/env python3
"""
Final verification script to confirm all Bldr Empire v2 services are working together
"""
import os
import requests
import sys
from pathlib import Path

def verify_end_to_end():
    """Verify end-to-end functionality"""
    print("🔍 Bldr Empire v2 - Final Verification")
    print("=" * 50)
    
    # Load environment variables
    os.chdir(Path(__file__).parent)
    if os.path.exists('.env'):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            print("   ⚠️  python-dotenv not installed, skipping .env loading")
    
    # 1. Check backend is running
    print("1. Checking Backend API Server...")
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend API is running")
        else:
            print(f"   ❌ Backend API error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Backend API not accessible: {e}")
        return False
    
    # 2. Check frontend is running
    print("2. Checking Frontend Dashboard...")
    try:
        response = requests.get('http://localhost:3000', timeout=5)
        if response.status_code == 200:
            print("   ✅ Frontend Dashboard is running")
        else:
            print(f"   ❌ Frontend Dashboard error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Frontend Dashboard not accessible: {e}")
        return False
    
    # 3. Check Telegram bot token
    print("3. Checking Telegram Bot...")
    token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    try:
        if not token or token == 'YOUR_TELEGRAM_BOT_TOKEN_HERE':
            print("   ⚠️  Telegram Bot token not set (optional)")
        else:
            response = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=5)
            if response.status_code == 200 and response.json().get('ok'):
                print("   ✅ Telegram Bot token is valid")
            else:
                print("   ⚠️  Telegram Bot token invalid (optional)")
    except Exception as e:
        print(f"   ⚠️  Telegram Bot check failed: {e} (optional)")
    
    # 4. Test a simple API endpoint
    print("4. Testing API Query Endpoint...")
    try:
        # Test with a simple query
        response = requests.post('http://localhost:8000/query', 
                                json={'query': 'test', 'k': 1}, 
                                timeout=10)
        if response.status_code == 200:
            print("   ✅ API Query endpoint working")
        else:
            print(f"   ❌ API Query endpoint error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API Query endpoint not accessible: {e}")
        return False
    
    # 5. Check database configurations
    print("5. Checking Database Configuration...")
    neo4j_uri = os.getenv('NEO4J_URI')
    qdrant_path = os.getenv('QDRANT_PATH')
    
    if neo4j_uri and qdrant_path:
        print("   ✅ Database environment variables set")
    else:
        print("   ❌ Database environment variables missing")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Bldr Empire v2 - All Systems Operational!")
    print("   🔧 Backend API: http://localhost:8000")
    print("   🖥️  Frontend Dashboard: http://localhost:3000")
    if token and token != 'YOUR_TELEGRAM_BOT_TOKEN_HERE':
        print("   🤖 Telegram Bot: @sstroitel_bot (configured)")
    else:
        print("   🤖 Telegram Bot: Not configured (optional)")
    print("\nReady for full operation! 🚀")
    
    return True

if __name__ == "__main__":
    success = verify_end_to_end()
    sys.exit(0 if success else 1)