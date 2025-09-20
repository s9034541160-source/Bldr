#!/usr/bin/env python3
"""
End-to-End Test for Custom Directory Training
Test full pipeline: Frontend → API → Training → RAG → Query Testing

Simulates user workflow:
1. User selects custom directory in frontend (I:\docs\downloaded)
2. System scans and processes files
3. Trains RAG system on new documents
4. Tests query performance on trained data
"""

import requests
import json
import time
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Any

# Load environment variables
load_dotenv()

API_BASE = 'http://localhost:8000'
API_TOKEN = os.getenv('API_TOKEN')

def get_auth_headers():
    """Get authentication headers for API calls"""
    headers = {
        "Content-Type": "application/json"
    }
    if API_TOKEN:
        headers['Authorization'] = f'Bearer {API_TOKEN}'
    return headers

def check_directory_exists(directory_path: str) -> Dict[str, Any]:
    """Check if directory exists and scan for documents"""
    print(f"🔍 Проверка директории: {directory_path}")
    
    path = Path(directory_path)
    if not path.exists():
        return {
            "exists": False,
            "error": f"Directory {directory_path} does not exist"
        }
    
    if not path.is_dir():
        return {
            "exists": False,
            "error": f"{directory_path} is not a directory"
        }
    
    # Scan for document files
    document_extensions = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.xls', '.xlsx', '.csv'}
    files_found = []
    total_size = 0
    
    try:
        for file_path in path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in document_extensions:
                file_size = file_path.stat().st_size
                files_found.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": file_size,
                    "extension": file_path.suffix.lower()
                })
                total_size += file_size
        
        return {
            "exists": True,
            "files_count": len(files_found),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "files": files_found[:10],  # First 10 files for preview
            "extensions": list(set(f["extension"] for f in files_found))
        }
        
    except Exception as e:
        return {
            "exists": False,
            "error": f"Error scanning directory: {str(e)}"
        }

async def test_custom_directory_training(custom_directory: str):
    """Test the complete custom directory training process"""
    print("🚀 E2E тест обучения на пользовательской папке НТД")
    print("=" * 70)
    
    # Step 1: Check API availability
    print("📡 Шаг 1: Проверка доступности API...")
    try:
        response = requests.get(f'{API_BASE}/health', timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API доступен: {health_data.get('status', 'unknown')}")
        else:
            print(f"❌ API недоступен: HTTP {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {str(e)}")
        return
    
    # Step 2: Validate directory
    print(f"\n📂 Шаг 2: Валидация директории...")
    dir_info = check_directory_exists(custom_directory)
    
    if not dir_info["exists"]:
        print(f"❌ {dir_info['error']}")
        return
    
    print(f"✅ Директория найдена:")
    print(f"   📁 Файлов: {dir_info['files_count']}")
    print(f"   💾 Размер: {dir_info['total_size_mb']} MB")
    print(f"   📄 Типы: {', '.join(dir_info['extensions'])}")
    
    if dir_info['files_count'] == 0:
        print("⚠️ В директории не найдено документов для обучения")
        return
    
    # Preview some files
    print(f"\n📋 Первые файлы для обработки:")
    for i, file_info in enumerate(dir_info['files'][:5], 1):
        size_kb = round(file_info['size'] / 1024, 1)
        print(f"   {i}. {file_info['name']} ({size_kb} KB)")
    
    # Step 3: Start training process
    print(f"\n🚀 Шаг 3: Запуск процесса обучения...")
    
    training_payload = {
        "custom_dir": custom_directory
    }
    
    try:
        train_response = requests.post(
            f'{API_BASE}/train',
            json=training_payload,
            headers=get_auth_headers(),
            timeout=30
        )
        
        if train_response.status_code == 200:
            train_data = train_response.json()
            print(f"✅ Обучение запущено: {train_data.get('message', 'Training started')}")
            print(f"📁 Папка: {train_data.get('custom_dir', custom_directory)}")
        else:
            print(f"❌ Ошибка запуска обучения: {train_response.status_code}")
            print(f"   Ответ: {train_response.text}")
            return
            
    except Exception as e:
        print(f"❌ Исключение при запуске обучения: {str(e)}")
        return
    
    # Step 4: Monitor training progress
    print(f"\n📊 Шаг 4: Мониторинг прогресса обучения...")
    
    max_wait_time = 1800  # 30 minutes
    check_interval = 15   # Check every 15 seconds
    start_time = time.time()
    
    training_completed = False
    last_status = None
    
    while (time.time() - start_time) < max_wait_time and not training_completed:
        try:
            status_response = requests.get(
                f'{API_BASE}/api/training/status',
                headers=get_auth_headers(),
                timeout=10
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                current_status = status_data.get('status')
                is_training = status_data.get('is_training', False)
                progress = status_data.get('progress', 0)
                stage = status_data.get('current_stage', 'unknown')
                message = status_data.get('message', 'No message')
                
                # Only print if status changed
                if status_data != last_status:
                    elapsed_min = int((time.time() - start_time) / 60)
                    print(f"   [{elapsed_min:2}m] 📈 {stage}: {message} ({progress}%)")
                    last_status = status_data.copy()
                
                # Check if training completed
                if not is_training and current_status == 'success':
                    print(f"🎉 Обучение завершено успешно!")
                    training_completed = True
                    break
                elif current_status == 'error':
                    print(f"❌ Ошибка обучения: {message}")
                    break
                    
            else:
                print(f"⚠️ Ошибка получения статуса: {status_response.status_code}")
                
        except Exception as e:
            print(f"❌ Исключение при проверке статуса: {str(e)}")
        
        if not training_completed:
            await asyncio.sleep(check_interval)
    
    if not training_completed:
        print(f"⏰ Превышен лимит времени ожидания ({max_wait_time//60} минут)")
        print(f"   Обучение может продолжаться в фоне")
    
    # Step 5: Test query performance on new data
    print(f"\n🔍 Шаг 5: Тестирование запросов на обученных данных...")
    
    # Test queries related to potentially new documents
    test_queries = [
        "строительные требования",
        "нормативы безопасности",
        "технические условия", 
        "ГОСТ стандарты",
        "СНиП нормы"
    ]
    
    query_results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"   🔍 Тест {i}: '{query}'")
        
        try:
            query_payload = {
                "query": query,
                "k": 3
            }
            
            query_response = requests.post(
                f'{API_BASE}/query',
                json=query_payload,
                headers=get_auth_headers(),
                timeout=30
            )
            
            if query_response.status_code == 200:
                query_data = query_response.json()
                results = query_data.get('results', [])
                ndcg = query_data.get('ndcg', 0)
                
                if results:
                    best_score = results[0].get('score', 0) if results else 0
                    print(f"      ✅ {len(results)} результатов, лучший score: {best_score:.3f}, NDCG: {ndcg:.3f}")
                    
                    # Check if we have high-quality results
                    high_quality_results = [r for r in results if r.get('score', 0) > 0.7]
                    if high_quality_results:
                        print(f"      🎯 {len(high_quality_results)} высококачественных результатов")
                    
                    query_results.append({
                        "query": query,
                        "results_count": len(results),
                        "best_score": best_score,
                        "ndcg": ndcg,
                        "high_quality_count": len(high_quality_results)
                    })
                else:
                    print(f"      ⚠️ Результатов не найдено")
                    query_results.append({
                        "query": query,
                        "results_count": 0,
                        "best_score": 0,
                        "ndcg": 0,
                        "high_quality_count": 0
                    })
                    
            else:
                print(f"      ❌ Ошибка запроса: {query_response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Исключение запроса: {str(e)}")
        
        await asyncio.sleep(2)  # Small delay between queries
    
    # Step 6: Generate summary report
    print(f"\n📋 Шаг 6: Итоговый отчет")
    print("=" * 70)
    
    total_time = time.time() - start_time
    
    print(f"⏱️ Общее время выполнения: {int(total_time//60)}м {int(total_time%60)}с")
    print(f"📁 Обработанная директория: {custom_directory}")
    print(f"📄 Найдено документов: {dir_info['files_count']}")
    print(f"💾 Общий размер: {dir_info['total_size_mb']} MB")
    print(f"🚀 Статус обучения: {'✅ Завершено' if training_completed else '⏳ В процессе'}")
    
    # Query performance summary
    if query_results:
        avg_score = sum(r["best_score"] for r in query_results) / len(query_results)
        total_results = sum(r["results_count"] for r in query_results)
        total_high_quality = sum(r["high_quality_count"] for r in query_results)
        
        print(f"\n🔍 Результаты тестирования запросов:")
        print(f"   📊 Средний score: {avg_score:.3f}")
        print(f"   📈 Всего результатов: {total_results}")
        print(f"   🎯 Высококачественных: {total_high_quality}")
        print(f"   🎖️ Покрытие запросов: {len([r for r in query_results if r['results_count'] > 0])}/{len(query_results)}")
    
    # Recommendations
    print(f"\n💡 Рекомендации:")
    if training_completed and avg_score > 0.5:
        print("   ✅ Система успешно обучена на новых данных")
        print("   🎯 Качество поиска удовлетворительное")
    elif training_completed and avg_score <= 0.5:
        print("   ⚠️ Обучение завершено, но качество поиска низкое")
        print("   📝 Рекомендуется проверить качество исходных документов")
    else:
        print("   ⏳ Дождитесь завершения обучения для полной оценки")
    
    if dir_info['files_count'] < 10:
        print("   📚 Рекомендуется добавить больше документов для улучшения качества")

async def test_frontend_integration():
    """Test frontend integration points"""
    print(f"\n🌐 Дополнительный тест: Интеграция с фронтендом")
    print("-" * 50)
    
    # Test metrics endpoint (used by frontend dashboard)
    try:
        metrics_response = requests.get(
            f'{API_BASE}/metrics-json',
            timeout=10
        )
        
        if metrics_response.status_code == 200:
            metrics = metrics_response.json()
            print(f"✅ Метрики доступны:")
            print(f"   📊 Чанков: {metrics.get('total_chunks', 0)}")
            print(f"   🎯 NDCG: {metrics.get('avg_ndcg', 0)}")
            print(f"   📈 Покрытие: {metrics.get('coverage', 0)}")
        else:
            print(f"⚠️ Ошибка получения метрик: {metrics_response.status_code}")
            
    except Exception as e:
        print(f"❌ Исключение метрик: {str(e)}")
    
    # Test WebSocket endpoint availability
    print(f"🔌 WebSocket эндпоинт: ws://localhost:8000/ws (для real-time обновлений)")

async def main():
    """Main test function"""
    # Default test directory - can be changed
    test_directory = "I:\\docs\\downloaded"
    
    print("🔧 E2E Test: Обучение на пользовательской папке НТД")
    print("=" * 70)
    print(f"🎯 Цель: Протестировать полный процесс от фронта до запросов")
    print(f"📁 Тестовая директория: {test_directory}")
    print(f"⏱️ Максимальное время ожидания: 30 минут")
    print(f"🔗 API Base: {API_BASE}")
    
    # Check if test directory exists, if not, suggest alternatives
    if not os.path.exists(test_directory):
        print(f"\n⚠️ Директория {test_directory} не найдена")
        
        # Suggest alternative test directories
        alternative_dirs = [
            "I:\\docs\\база",
            "C:\\Bldr\\test_docs",
            "C:\\Bldr\\docs"
        ]
        
        for alt_dir in alternative_dirs:
            if os.path.exists(alt_dir):
                print(f"✅ Найдена альтернативная директория: {alt_dir}")
                test_directory = alt_dir
                break
        else:
            print("❌ Не найдено подходящих директорий для тестирования")
            print("💡 Создайте тестовую папку с несколькими PDF/Word документами")
            return
    
    await test_custom_directory_training(test_directory)
    await test_frontend_integration()
    
    print(f"\n✨ E2E тест завершен!")
    print(f"\nℹ️ Для использования во фронтенде:")
    print(f"   1. Пользователь выбирает папку в интерфейсе")
    print(f"   2. Фронт отправляет POST /train с custom_dir")
    print(f"   3. Мониторинг через GET /api/training/status")
    print(f"   4. WebSocket обновления в реальном времени")
    print(f"   5. Тестирование через POST /query")

if __name__ == '__main__':
    asyncio.run(main())