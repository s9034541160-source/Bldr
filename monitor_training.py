#!/usr/bin/env python3
"""
Мониторинг прогресса RAG обучения на 1168 файлах НТД
"""

import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8000"
API_TOKEN = os.getenv("API_TOKEN")

def get_auth_headers():
    if API_TOKEN:
        return {"Authorization": f"Bearer {API_TOKEN}"}
    return {}

def test_search_progress():
    """Тестируем поиск для проверки прогресса"""
    print(f"🔍 [{datetime.now().strftime('%H:%M:%S')}] Тестируем поиск...")
    
    auth_headers = get_auth_headers()
    if not auth_headers:
        print("❌ Нет токена авторизации")
        return
    
    queries = [
        "строительные нормы и правила",
        "железобетонные конструкции", 
        "СП ГОСТ СНиП",
        "технические требования",
        "проектирование зданий"
    ]
    
    total_results = 0
    
    for query in queries:
        try:
            response = requests.post(
                f"{API_BASE}/query",
                json={"query": query, "k": 5},
                headers=auth_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                count = len(results.get('results', []))
                total_results += count
                if count > 0:
                    print(f"  ✅ '{query}': {count} результатов")
                else:
                    print(f"  ⚪ '{query}': нет результатов")
            else:
                print(f"  ❌ '{query}': ошибка {response.status_code}")
                
        except Exception as e:
            print(f"  ⚠️ '{query}': {e}")
    
    print(f"📊 Всего найдено результатов: {total_results}")
    return total_results

def monitor_system_resources():
    """Мониторим ресурсы системы"""
    try:
        import psutil
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        
        print(f"💻 Система:")
        print(f"   CPU: {cpu_percent:.1f}%")
        print(f"   RAM: {memory_percent:.1f}% ({memory_used_gb:.1f}GB / {memory_total_gb:.1f}GB)")
        
        # Проверяем процессы Python
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if 'python' in proc.info['name'].lower():
                    python_processes.append(proc.info)
            except:
                pass
        
        if python_processes:
            print(f"🐍 Python процессы: {len(python_processes)}")
            for proc in python_processes[:3]:  # Показываем первые 3
                print(f"   PID {proc['pid']}: CPU {proc['cpu_percent']:.1f}%, RAM {proc['memory_percent']:.1f}%")
                
    except ImportError:
        print("⚠️ psutil не установлен, пропускаем мониторинг ресурсов")
    except Exception as e:
        print(f"⚠️ Ошибка мониторинга ресурсов: {e}")

def main():
    """Основной цикл мониторинга"""
    print("🔍 Мониторинг RAG обучения на 1168 файлах")
    print("=" * 60)
    print("📝 Каждые 5 минут проверяем прогресс через поиск")
    print("⏹️  Для остановки нажмите Ctrl+C")
    print()
    
    start_time = datetime.now()
    iteration = 0
    
    try:
        while True:
            iteration += 1
            current_time = datetime.now()
            elapsed = current_time - start_time
            
            print(f"🔄 Итерация {iteration} | Время: {elapsed}")
            print("-" * 40)
            
            # Тестируем поиск
            results_count = test_search_progress()
            
            # Мониторим ресурсы
            monitor_system_resources()
            
            print()
            
            if results_count > 10:  # Если есть достаточно результатов
                print("🎉 Похоже, обучение дает результаты!")
                print("💡 Можете протестировать более сложные запросы")
            
            # Ждём 5 минут
            print("⏳ Ждём 5 минут до следующей проверки...")
            time.sleep(300)  # 5 минут
            
    except KeyboardInterrupt:
        print("\n⏹️ Мониторинг остановлен пользователем")
        elapsed = datetime.now() - start_time
        print(f"🕐 Время мониторинга: {elapsed}")

if __name__ == "__main__":
    main()