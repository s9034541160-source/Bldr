#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 TRAINING PROGRESS MONITOR
===========================
Простой монитор для отслеживания прогресса фонового RAG обучения
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
import psutil

def monitor_training():
    """Мониторинг прогресса обучения"""
    
    progress_file = Path("C:/Bldr/training_progress.json")
    stats_file = Path("C:/Bldr/training_stats.json")
    
    print("📊 RAG Training Monitor")
    print("=" * 50)
    print("Press Ctrl+C to exit monitor (training will continue)")
    print("=" * 50)
    
    try:
        while True:
            # Проверяем, запущен ли процесс обучения
            training_running = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'] and 'background_rag_training.py' in ' '.join(proc.info['cmdline'] or []):
                        training_running = True
                        break
                except:
                    continue
            
            if not training_running:
                print("⚠️ Training process not found")
            
            # Читаем прогресс
            if progress_file.exists():
                try:
                    with open(progress_file, 'r', encoding='utf-8') as f:
                        progress = json.load(f)
                    
                    stats = progress.get('stats', {})
                    
                    print(f"\n🕐 {datetime.now().strftime('%H:%M:%S')} - Training Status:")
                    print(f"  📈 Progress: {stats.get('progress_percent', 0):.1f}%")
                    print(f"  📁 Files found: {stats.get('files_found', 0)}")
                    print(f"  ✅ Processed: {stats.get('files_processed', 0)}")
                    print(f"  ❌ Failed: {stats.get('files_failed', 0)}")
                    print(f"  🧩 Chunks created: {stats.get('chunks_created', 0)}")
                    print(f"  ⏱️ Time left: {stats.get('estimated_time_left', 'unknown')}")
                    print(f"  📄 Current file: {stats.get('current_file', 'N/A')}")
                    
                    if training_running:
                        print(f"  🟢 Status: RUNNING")
                    else:
                        print(f"  🔴 Status: NOT RUNNING")
                        
                except Exception as e:
                    print(f"❌ Error reading progress: {e}")
            else:
                print("⚠️ No progress file found yet")
            
            time.sleep(10)  # Обновляем каждые 10 секунд
            
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped (training continues in background)")

if __name__ == "__main__":
    monitor_training()