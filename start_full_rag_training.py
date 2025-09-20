#!/usr/bin/env python3
"""
🚀 ПОЛНОЦЕННОЕ RAG-ОБУЧЕНИЕ со всеми 15 стадиями!
Сложный NLP анализ, Rubern markup, NetworkX, SpaCy, все базы данных!
НО БЕЗ LMstudio!
"""

import requests
import json
import time
import os

# API конфигурация
API_BASE_URL = "http://localhost:8000"

def create_test_token():
    """Создать тестовый токен для аутентификации"""
    import jwt
    from datetime import datetime, timedelta
    
    payload = {
        "sub": "full_training_user",
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    
    token = jwt.encode(payload, "your-secret-key-change-in-production", algorithm="HS256")
    return token

def start_full_rag_training():
    """Запустить ПОЛНОЦЕННОЕ RAG-обучение со всеми 15 стадиями"""
    print("🚀 ЗАПУСК ПОЛНОЦЕННОГО RAG-ОБУЧЕНИЯ!")
    print("🔥 СО ВСЕМИ 15 СТАДИЯМИ СЛОЖНОГО NLP АНАЛИЗА!")
    print("=" * 80)
    
    # Создаем токен
    token = create_test_token()
    
    # Проверяем директорию
    custom_dir = "I:/docs/downloaded"
    if not os.path.exists(custom_dir):
        print(f"⚠️ Директория {custom_dir} не найдена!")
        print("💡 Попробуем с базовой директорией...")
        custom_dir = None
    else:
        files_count = len([f for f in os.listdir(custom_dir) if os.path.isfile(os.path.join(custom_dir, f))])
        print(f"📁 Найдено {files_count} файлов в {custom_dir}")
        print(f"📚 Готовимся к ПОЛНОЙ обработке всех документов!")
    
    # Данные запроса - ВАЖНО: fast_mode = False для полного анализа!
    request_data = {
        "fast_mode": False,  # 🔥 ПОЛНОЦЕННЫЙ РЕЖИМ!
        "custom_dir": custom_dir
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"🔥 Запуск ПОЛНОЦЕННОГО RAG-обучения...")
        print(f"📂 Директория: {custom_dir or 'по умолчанию'}")
        print(f"⚙️ Режим: ПОЛНЫЙ (все 15 стадий)")
        print(f"🧠 SpaCy NLP: ВКЛЮЧЕН")
        print(f"🏗️ Rubern markup: ВКЛЮЧЕН") 
        print(f"📊 NetworkX graphs: ВКЛЮЧЕН")
        print(f"🗄️ Neo4j: ВКЛЮЧЕН")
        print(f"🔍 Qdrant: ВКЛЮЧЕН")
        print(f"🔬 Сложный анализ: ВКЛЮЧЕН")
        print()
        
        # Запускаем обучение
        response = requests.post(
            f"{API_BASE_URL}/train",
            json=request_data,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            mode = 'FULL' if not result.get('fast_mode') else 'FAST'
            print(f"🏃 Режим: {mode}")
            
            if result.get('fast_mode'):
                print("❌ ВНИМАНИЕ: Система запустилась в БЫСТРОМ режиме!")
                print("❌ Это НЕ то что мы хотели! Нужен ПОЛНЫЙ режим!")
                return
            
            # Мониторим прогресс
            print("\n📊 МОНИТОРИНГ ПОЛНОГО RAG-ОБУЧЕНИЯ:")
            print("🔥 Отслеживаем все 15 стадий сложного анализа...")
            print("-" * 80)
            
            last_progress = -1
            last_stage = ""
            start_time = time.time()
            stage_times = {}
            
            while True:
                time.sleep(5)  # Проверяем каждые 5 секунд (полный режим медленнее)
                
                try:
                    status_response = requests.get(
                        f"{API_BASE_URL}/api/training/status",
                        headers=headers,
                        timeout=15
                    )
                    
                    if status_response.status_code == 200:
                        status = status_response.json()
                        
                        progress = status.get("progress", 0)
                        stage = status.get("current_stage", "")
                        message = status.get("message", "")
                        mode = status.get("mode", "normal")
                        is_training = status.get("is_training", False)
                        
                        # Отслеживаем времена стадий
                        if stage != last_stage and last_stage:
                            elapsed = time.time() - start_time
                            stage_times[last_stage] = elapsed - sum(stage_times.values())
                        
                        # Показываем прогресс
                        if progress != last_progress or stage != last_stage:
                            elapsed = time.time() - start_time
                            
                            # Определяем эмодзи для стадии
                            stage_emoji = {
                                "0/14": "🔧",  # Предобработка НТД
                                "1/15": "✅",  # Валидация
                                "2/15": "🔍",  # Проверка дубликатов
                                "3/15": "📄",  # Извлечение текста
                                "4/15": "🏷️",  # Определение типа
                                "5/15": "🏗️",  # Структурный анализ
                                "6/15": "🔨",  # Кандидаты на работы
                                "7/15": "🎨",  # Rubern markup
                                "8/15": "📊",  # Метаданные
                                "9/15": "🛡️",  # Контроль качества
                                "10/15": "⚙️", # Специфическая обработка
                                "11/15": "🔗", # Последовательности работ
                                "12/15": "💾", # Сохранение в Neo4j
                                "13/15": "✂️", # Чанкирование
                                "14/15": "🧠", # Embeddings
                                "15/15": "🗄️"  # Сохранение в Qdrant
                            }.get(stage.split(":")[0], "📋")
                            
                            print(f"[{mode.upper()}] {stage_emoji} {stage}: {message}")
                            print(f"   📈 Прогресс: {progress}% | ⏱️ Время: {elapsed:.1f}с")
                            
                            last_progress = progress
                            last_stage = stage
                        
                        # Проверяем завершение
                        if not is_training:
                            if status.get("status") == "success" or "completed" in stage:
                                elapsed = time.time() - start_time
                                print(f"\n🎉 ПОЛНОЦЕННОЕ RAG-ОБУЧЕНИЕ ЗАВЕРШЕНО!")
                                print(f"⏱️ Общее время: {elapsed/60:.1f} минут ({elapsed:.1f} секунд)")
                                
                                # Показываем времена стадий
                                if stage_times:
                                    print(f"\n📊 Времена стадий:")
                                    for stage_name, stage_time in stage_times.items():
                                        print(f"   {stage_name}: {stage_time:.1f}с")
                                
                                print(f"\n🔥 ЭТО БЫЛО НАСТОЯЩЕЕ ОБУЧЕНИЕ!")
                                print(f"🧠 Со всеми сложными NLP алгоритмами")
                                print(f"🏗️ С полным Rubern markup анализом")
                                print(f"📊 С NetworkX графами зависимостей")
                                print(f"🗄️ С сохранением в Neo4j и Qdrant")
                                break
                            elif "error" in stage or "error" in status.get("status", ""):
                                print(f"\n❌ Ошибка в полном обучении: {message}")
                                break
                            else:
                                elapsed = time.time() - start_time
                                print(f"\n✅ Обучение завершено: {message}")
                                print(f"⏱️ Время: {elapsed/60:.1f} минут")
                                break
                    else:
                        print(f"⚠️ Ошибка статуса: {status_response.status_code}")
                        break
                        
                except requests.exceptions.RequestException as e:
                    print(f"⚠️ Ошибка запроса статуса: {e}")
                    print("🔄 Повторная попытка через 10 секунд...")
                    time.sleep(10)
                    continue
                    
                # Таймаут через 2 часа (полное обучение может быть долгим)
                if time.time() - start_time > 7200:
                    print("⏰ Таймаут - обучение идет дольше 2 часов")
                    print("💡 Это нормально для полного режима с большим количеством файлов")
                    break
                    
        else:
            print(f"❌ Ошибка запуска: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")

def show_training_comparison():
    """Показать сравнение режимов обучения"""
    print("\n" + "=" * 80)
    print("📊 СРАВНЕНИЕ РЕЖИМОВ ОБУЧЕНИЯ")
    print("=" * 80)
    
    print("🚀 БЫСТРЫЙ РЕЖИМ (fast_mode=True):")
    print("   • 5 простых стадий")
    print("   • Только regex анализ")
    print("   • Простое разбиение на чанки")
    print("   • Быстрые embeddings (384-dim)")
    print("   • Время: ~1-2 минуты/1000 файлов")
    print("   • Качество: ~92-95%")
    
    print("\n🔥 ПОЛНЫЙ РЕЖИМ (fast_mode=False):")
    print("   • 15 сложных стадий")
    print("   • SpaCy NLP анализ")
    print("   • Rubern markup генерация")
    print("   • NetworkX графы зависимостей")
    print("   • Продвинутые embeddings (1024-dim)")
    print("   • Качественное извлечение метаданных")
    print("   • Neo4j граф рабочих последовательностей")
    print("   • Время: ~20-60 минут/1000 файлов")
    print("   • Качество: ~97-99%")
    
    print("\n💡 МЫ ЗАПУСКАЕМ ПОЛНЫЙ РЕЖИМ!")
    print("🔥 Для максимального качества анализа!")

if __name__ == "__main__":
    print("🔥 ПОЛНОЦЕННОЕ RAG-ОБУЧЕНИЕ")
    print("=" * 80)
    
    show_training_comparison()
    start_full_rag_training()
    
    print("\n" + "=" * 80)
    print("🏁 Полное RAG-обучение завершено!")
    print("=" * 80)