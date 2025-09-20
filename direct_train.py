import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

print("=== DIRECT TRAINING LAUNCH ===")

if not API_TOKEN:
    print("ERROR: No API token")
    exit(1)

headers = {"Authorization": f"Bearer {API_TOKEN}"}

# Check API
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"✅ API Health: {response.status_code}")
except Exception as e:
    print(f"❌ API Error: {e}")
    exit(1)

# Launch training
train_data = {"custom_dir": "I:/docs/downloaded"}

print(f"📤 Starting training on: {train_data['custom_dir']}")

try:
    response = requests.post(
        "http://localhost:8000/train",
        json=train_data,
        headers=headers,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Training started successfully!")
    else:
        print("❌ Training failed to start")
        
except Exception as e:
    print(f"❌ Training request error: {e}")

print("=== END ===")
input("Press Enter to continue...")