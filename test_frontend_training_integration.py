#!/usr/bin/env python3
"""
Frontend Integration Test for Custom Training Workflow
Simulates the exact frontend workflow for custom directory training

Frontend Workflow:
1. User browses and selects directory
2. Frontend validates directory and shows preview
3. User confirms and starts training
4. Frontend shows progress with WebSocket updates
5. User can query the newly trained data
"""

import requests
import json
import time
import os
import asyncio
import websockets
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional

# Load environment variables
load_dotenv()

API_BASE = 'http://localhost:8000'
WS_BASE = 'ws://localhost:8000/ws'
API_TOKEN = os.getenv('API_TOKEN')

def get_auth_headers():
    """Get authentication headers for API calls"""
    headers = {
        "Content-Type": "application/json"
    }
    if API_TOKEN:
        headers['Authorization'] = f'Bearer {API_TOKEN}'
    return headers

class FrontendTrainingSimulator:
    """Simulates frontend behavior for custom training workflow"""
    
    def __init__(self):
        self.api_base = API_BASE
        self.ws_base = WS_BASE
        self.websocket = None
        self.training_updates = []
        
    async def connect_websocket(self):
        """Connect to WebSocket for real-time updates"""
        try:
            # Add auth token as query parameter for WebSocket
            ws_url = f"{self.ws_base}?token={API_TOKEN}" if API_TOKEN else self.ws_base
            self.websocket = await websockets.connect(ws_url)
            print("✅ WebSocket соединение установлено")
            return True
        except Exception as e:
            print(f"❌ Ошибка WebSocket подключения: {str(e)}")
            return False
    
    async def listen_for_updates(self, duration_seconds: int = 300):
        """Listen for WebSocket updates during training"""
        if not self.websocket:
            return
        
        print(f"👂 Прослушивание WebSocket обновлений ({duration_seconds}s)...")
        start_time = time.time()
        
        try:
            while (time.time() - start_time) < duration_seconds:
                try:
                    # Set timeout for individual message
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=10.0
                    )
                    
                    try:
                        data = json.loads(message)
                        self.training_updates.append(data)
                        
                        # Print relevant updates
                        if data.get('type') in ['training_update', 'ai_task_update']:
                            stage = data.get('stage', 'unknown')
                            progress = data.get('progress', 0)
                            message_text = data.get('message', '')
                            elapsed = int(time.time() - start_time)
                            print(f"📡 [{elapsed:3}s] {stage}: {message_text} ({progress}%)")
                            
                    except json.JSONDecodeError:
                        print(f"📡 Raw message: {message[:100]}...")
                        
                except asyncio.TimeoutError:
                    # No message received within timeout, continue listening
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("📡 WebSocket соединение закрыто")
                    break
                    
        except Exception as e:
            print(f"❌ Ошибка прослушивания WebSocket: {str(e)}")
    
    async def close_websocket(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            print("📡 WebSocket соединение закрыто")
    
    def browse_directory(self, directory_path: str) -> Dict[str, Any]:
        """Simulate frontend directory browsing"""
        print(f"📁 Симуляция выбора директории: {directory_path}")
        
        path = Path(directory_path)
        if not path.exists() or not path.is_dir():
            return {
                "valid": False,
                "error": f"Directory {directory_path} does not exist or is not a directory"
            }
        
        # Count files by type (similar to frontend preview)
        file_types = {
            ".pdf": 0, ".doc": 0, ".docx": 0, ".txt": 0,
            ".xls": 0, ".xlsx": 0, ".csv": 0, ".rtf": 0
        }
        
        total_files = 0
        total_size = 0
        sample_files = []
        
        try:
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    if ext in file_types:
                        file_types[ext] += 1
                        total_files += 1
                        file_size = file_path.stat().st_size
                        total_size += file_size
                        
                        # Keep sample files for preview
                        if len(sample_files) < 10:
                            sample_files.append({
                                "name": file_path.name,
                                "size": file_size,
                                "type": ext,
                                "path": str(file_path)
                            })
            
            return {
                "valid": True,
                "directory": directory_path,
                "total_files": total_files,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "sample_files": sample_files,
                "estimated_training_time": self._estimate_training_time(total_files, total_size)
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Error scanning directory: {str(e)}"
            }
    
    def _estimate_training_time(self, file_count: int, total_size: int) -> str:
        """Estimate training time based on file count and size"""
        # Rough estimation: 30 seconds per file + size factor
        base_time = file_count * 30  # seconds
        size_factor = total_size / (1024 * 1024) * 10  # MB to seconds
        total_seconds = base_time + size_factor
        
        if total_seconds < 300:  # < 5 minutes
            return "5-10 минут"
        elif total_seconds < 900:  # < 15 minutes
            return "10-20 минут"
        elif total_seconds < 1800:  # < 30 minutes
            return "20-40 минут"
        else:
            return "40+ минут"
    
    def show_directory_preview(self, dir_info: Dict[str, Any]):
        """Show directory preview like frontend would"""
        if not dir_info["valid"]:
            print(f"❌ {dir_info['error']}")
            return
        
        print("📋 Предварительный просмотр директории:")
        print(f"   📁 Путь: {dir_info['directory']}")
        print(f"   📄 Всего документов: {dir_info['total_files']}")
        print(f"   💾 Общий размер: {dir_info['total_size_mb']} MB")
        print(f"   ⏱️ Примерное время обучения: {dir_info['estimated_training_time']}")
        
        print(f"\n📊 Типы файлов:")
        for file_type, count in dir_info["file_types"].items():
            if count > 0:
                print(f"   {file_type}: {count} файлов")
        
        print(f"\n📋 Примеры файлов:")
        for i, file_info in enumerate(dir_info["sample_files"][:5], 1):
            size_kb = round(file_info["size"] / 1024, 1)
            print(f"   {i}. {file_info['name']} ({size_kb} KB)")
    
    async def start_training(self, directory_path: str) -> Optional[str]:
        """Start training process"""
        print(f"\n🚀 Запуск обучения на директории: {directory_path}")
        
        payload = {"custom_dir": directory_path}
        
        try:
            response = requests.post(
                f'{self.api_base}/train',
                json=payload,
                headers=get_auth_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Обучение запущено: {data.get('message', '')}")
                return "training_started"
            else:
                print(f"❌ Ошибка запуска: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Исключение при запуске: {str(e)}")
            return None
    
    async def monitor_training_progress(self, max_duration: int = 1800):
        """Monitor training progress with both REST and WebSocket"""
        print(f"\n📊 Мониторинг прогресса обучения...")
        
        # Start WebSocket listening in background
        ws_task = None
        if self.websocket:
            ws_task = asyncio.create_task(self.listen_for_updates(max_duration))
        
        start_time = time.time()
        last_rest_check = 0
        rest_interval = 30  # Check REST API every 30 seconds
        
        training_completed = False
        
        while (time.time() - start_time) < max_duration and not training_completed:
            current_time = time.time()
            
            # Check REST API periodically
            if (current_time - last_rest_check) >= rest_interval:
                try:
                    response = requests.get(
                        f'{self.api_base}/api/training/status',
                        headers=get_auth_headers(),
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        status_data = response.json()
                        is_training = status_data.get('is_training', False)
                        status = status_data.get('status', 'unknown')
                        progress = status_data.get('progress', 0)
                        stage = status_data.get('current_stage', 'unknown')
                        
                        elapsed = int(current_time - start_time)
                        print(f"🔄 [{elapsed:3}s] REST: {stage} - {status} ({progress}%)")
                        
                        if not is_training and status == 'success':
                            print(f"🎉 Обучение завершено успешно!")
                            training_completed = True
                            break
                        elif status == 'error':
                            print(f"❌ Ошибка обучения")
                            break
                    
                    last_rest_check = current_time
                    
                except Exception as e:
                    print(f"⚠️ Ошибка проверки статуса: {str(e)}")
            
            await asyncio.sleep(5)  # Small sleep between checks
        
        # Cancel WebSocket task if running
        if ws_task and not ws_task.done():
            ws_task.cancel()
            try:
                await ws_task
            except asyncio.CancelledError:
                pass
        
        return training_completed
    
    async def test_query_performance(self, test_queries: List[str]):
        """Test query performance on newly trained data"""
        print(f"\n🔍 Тестирование запросов на обученной системе...")
        
        results_summary = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"   🎯 Тест {i}: '{query}'")
            
            try:
                payload = {"query": query, "k": 5}
                response = requests.post(
                    f'{self.api_base}/query',
                    json=payload,
                    headers=get_auth_headers(),
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    ndcg = data.get('ndcg', 0)
                    
                    if results:
                        best_score = results[0].get('score', 0)
                        high_quality = len([r for r in results if r.get('score', 0) > 0.7])
                        
                        print(f"      ✅ {len(results)} результатов, score: {best_score:.3f}, NDCG: {ndcg:.3f}")
                        if high_quality > 0:
                            print(f"      🎯 {high_quality} высококачественных результатов")
                        
                        results_summary.append({
                            "query": query,
                            "results_count": len(results),
                            "best_score": best_score,
                            "ndcg": ndcg,
                            "high_quality_count": high_quality
                        })
                    else:
                        print(f"      ⚠️ Результатов не найдено")
                        results_summary.append({
                            "query": query,
                            "results_count": 0,
                            "best_score": 0,
                            "ndcg": 0,
                            "high_quality_count": 0
                        })
                else:
                    print(f"      ❌ Ошибка запроса: {response.status_code}")
                    
            except Exception as e:
                print(f"      ❌ Исключение: {str(e)}")
            
            await asyncio.sleep(1)  # Small delay between queries
        
        return results_summary
    
    def generate_training_report(self, dir_info: Dict[str, Any], 
                               training_completed: bool, 
                               query_results: List[Dict[str, Any]], 
                               total_time: float):
        """Generate comprehensive training report"""
        print(f"\n📋 Итоговый отчет обучения")
        print("=" * 60)
        
        # Directory summary
        print(f"📁 Обработанная директория: {dir_info.get('directory', 'Unknown')}")
        print(f"📄 Документов обработано: {dir_info.get('total_files', 0)}")
        print(f"💾 Общий размер: {dir_info.get('total_size_mb', 0)} MB")
        print(f"⏱️ Время выполнения: {int(total_time//60)}м {int(total_time%60)}с")
        print(f"🚀 Статус: {'✅ Успешно завершено' if training_completed else '❌ Не завершено'}")
        
        # Query performance
        if query_results:
            successful_queries = [r for r in query_results if r['results_count'] > 0]
            avg_score = sum(r['best_score'] for r in query_results) / len(query_results)
            total_high_quality = sum(r['high_quality_count'] for r in query_results)
            
            print(f"\n🔍 Результаты тестирования:")
            print(f"   📊 Успешных запросов: {len(successful_queries)}/{len(query_results)}")
            print(f"   🎯 Средний score: {avg_score:.3f}")
            print(f"   💎 Высококачественных результатов: {total_high_quality}")
            
            # Quality assessment
            if avg_score > 0.7:
                quality = "🌟 Отличное"
            elif avg_score > 0.5:
                quality = "✅ Хорошее"
            elif avg_score > 0.3:
                quality = "⚠️ Удовлетворительное"
            else:
                quality = "❌ Низкое"
            
            print(f"   📈 Качество поиска: {quality}")
        
        # WebSocket updates summary
        if self.training_updates:
            print(f"\n📡 WebSocket обновления: {len(self.training_updates)} сообщений")
            
            # Count different types of updates
            update_types = {}
            for update in self.training_updates:
                update_type = update.get('type', 'unknown')
                update_types[update_type] = update_types.get(update_type, 0) + 1
            
            for update_type, count in update_types.items():
                print(f"   📨 {update_type}: {count}")
        
        # Recommendations
        print(f"\n💡 Рекомендации:")
        if training_completed and avg_score > 0.5:
            print("   ✅ Система готова к использованию")
            print("   🎯 Качество поиска соответствует ожиданиям")
        elif not training_completed:
            print("   ⏳ Дождитесь завершения обучения")
            print("   🔄 Проверьте логи на предмет ошибок")
        elif avg_score <= 0.5:
            print("   📚 Рекомендуется добавить больше качественных документов")
            print("   🔍 Проверьте релевантность исходных файлов")

async def main():
    """Main simulation function"""
    # Configuration
    test_directory = "I:\\docs\\downloaded"
    test_queries = [
        "строительные нормы и правила",
        "требования безопасности",
        "технические регламенты",
        "качество строительных материалов",
        "проектная документация"
    ]
    
    print("🖥️ Симуляция Frontend Workflow для Custom Training")
    print("=" * 65)
    
    simulator = FrontendTrainingSimulator()
    start_time = time.time()
    
    try:
        # Step 1: Connect WebSocket
        print("📡 Шаг 1: Подключение WebSocket для real-time обновлений...")
        ws_connected = await simulator.connect_websocket()
        
        # Step 2: Browse directory (frontend directory picker simulation)
        print(f"\n📁 Шаг 2: Выбор директории пользователем...")
        dir_info = simulator.browse_directory(test_directory)
        
        if not dir_info["valid"]:
            # Try alternative directories
            alternative_dirs = ["I:\\docs\\база", "C:\\Bldr\\test_docs"]
            for alt_dir in alternative_dirs:
                if os.path.exists(alt_dir):
                    print(f"🔄 Пробуем альтернативную директорию: {alt_dir}")
                    test_directory = alt_dir
                    dir_info = simulator.browse_directory(test_directory)
                    if dir_info["valid"]:
                        break
            
            if not dir_info["valid"]:
                print(f"❌ Не найдено подходящих директорий для тестирования")
                return
        
        # Step 3: Show preview (like frontend would)
        print(f"\n📋 Шаг 3: Предварительный просмотр...")
        simulator.show_directory_preview(dir_info)
        
        # Step 4: User confirmation (simulated)
        print(f"\n✅ Шаг 4: Пользователь подтверждает начало обучения...")
        
        # Step 5: Start training
        training_status = await simulator.start_training(test_directory)
        if not training_status:
            print("❌ Не удалось запустить обучение")
            return
        
        # Step 6: Monitor progress with both REST and WebSocket
        training_completed = await simulator.monitor_training_progress(1800)  # 30 minutes
        
        # Step 7: Test queries
        print(f"\n🧪 Шаг 7: Тестирование обученной системы...")
        query_results = await simulator.test_query_performance(test_queries)
        
        # Step 8: Generate comprehensive report
        total_time = time.time() - start_time
        simulator.generate_training_report(dir_info, training_completed, query_results, total_time)
        
    finally:
        # Cleanup
        await simulator.close_websocket()
    
    print(f"\n✨ Симуляция Frontend Workflow завершена!")
    print(f"\n📋 Интеграция с фронтендом:")
    print(f"   🌐 REST API: {API_BASE}")
    print(f"   📡 WebSocket: {WS_BASE}")
    print(f"   🔐 Аутентификация: Bearer Token")
    print(f"   📊 Мониторинг: REST + WebSocket")

if __name__ == '__main__':
    asyncio.run(main())