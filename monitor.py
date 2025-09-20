import requests
import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
headers = {"Authorization": f"Bearer {API_TOKEN}"}

def check_progress():
    print(f"🔍 [{datetime.now().strftime('%H:%M:%S')}] Checking progress...")
    
    # Test search
    queries = ["ГОСТ", "СП", "строительные", "нормы"]
    total = 0
    
    for q in queries:
        try:
            resp = requests.post(
                "http://localhost:8000/query",
                json={"query": q, "k": 2},
                headers=headers,
                timeout=10
            )
            if resp.status_code == 200:
                results = resp.json().get('results', [])
                count = len(results)
                total += count
                if count > 0:
                    print(f"   ✅ '{q}': {count} results")
                else:
                    print(f"   ⚪ '{q}': 0 results")
        except:
            print(f"   ❌ '{q}': error")
    
    print(f"📊 Total results: {total}")
    if total > 0:
        print("🎉 Training is producing results!")
        return True
    else:
        print("⏳ Still training...")
        return False

# Monitor every 5 minutes
print("🚀 Starting training monitor...")
print("⏹️  Press Ctrl+C to stop")

try:
    while True:
        if check_progress():
            print("✅ Training successful! Results found.")
            break
        print("Waiting 5 minutes...")
        time.sleep(300)  # 5 minutes
except KeyboardInterrupt:
    print("\n⏹️  Monitor stopped")