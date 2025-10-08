import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.celery_app import celery_app

print("Registered tasks:")
for task in celery_app.tasks.keys():
    print(f"  - {task}")