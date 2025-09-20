#!/usr/bin/env python3
"""
Safe RAG Training Launcher
Безопасный запуск обучения RAG с блокировкой
"""

import sys
import os
from rag_training_lock import RAGTrainingLock

def main():
    print("🚀 БЕЗОПАСНЫЙ ЗАПУСК RAG ОБУЧЕНИЯ")
    print("=" * 40)
    
    # Проверяем блокировку
    with RAGTrainingLock() as lock:
        print("✅ Блокировка получена, запускаем обучение...")
        
        # Импортируем и запускаем основной тренер
        try:
            # Здесь должен быть импорт вашего основного тренера
            # import enterprise_rag_trainer_full
            # enterprise_rag_trainer_full.main()
            
            # Пока что запускаем через subprocess для безопасности
            import subprocess
            
            cmd = [
                sys.executable, 
                "enterprise_rag_trainer_full.py",
                "--custom_dir", "I:/docs/downloaded",
                "--fast_mode"
            ]
            
            print(f"Выполняем команду: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=False)
            
            if result.returncode == 0:
                print("✅ Обучение завершено успешно!")
            else:
                print(f"❌ Обучение завершилось с ошибкой: код {result.returncode}")
                
        except KeyboardInterrupt:
            print("\n⚠️ Обучение прервано пользователем")
        except Exception as e:
            print(f"❌ Ошибка во время обучения: {e}")
        finally:
            print("🔓 Освобождаем блокировку...")

if __name__ == "__main__":
    main()
