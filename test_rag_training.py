#!/usr/bin/env python3
"""
Прямое тестирование RAG обучения на базе НТД без веб-интерфейса
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Set environment variables
os.environ["NEO4J_URI"] = "neo4j://localhost:7687"
os.environ["NEO4J_USER"] = "neo4j"  
os.environ["NEO4J_PASSWORD"] = "neopassword"
os.environ["BASE_DIR"] = "I:/docs"
os.environ["SKIP_NEO4J"] = "false"

def progress_callback(stage: str, log: str, progress: int = 0):
    """Callback для отображения прогресса обучения"""
    print(f"📊 [{stage}] {log} ({progress}%)")

def main():
    print("🚀 Запуск прямого тестирования RAG обучения")
    
    try:
        # Import the RAG trainer
        from scripts.bldr_rag_trainer import BldrRAGTrainer
        
        print("✅ BldrRAGTrainer импортирован успешно")
        
        # Initialize trainer
        trainer = BldrRAGTrainer(
            base_dir="I:/docs/clean_base",
            neo4j_uri="neo4j://localhost:7687",
            neo4j_user="neo4j",
            neo4j_pass="neopassword",
            qdrant_path="C:/Bldr/data/qdrant_db",
            norms_db="I:/docs/clean_base", 
            reports_dir="I:/docs/reports",
            use_advanced_embeddings=True
        )
        
        print("✅ Trainer инициализирован")
        
        # Test with one specific file first
        test_file = "I:/docs/БАЗА/3. sp-45.pdf"
        
        if os.path.exists(test_file):
            print(f"🧪 Тестирование на файле: {test_file}")
            
            try:
                # Process single document
                success = trainer.process_document(test_file, update_callback=progress_callback)
                
                if success:
                    print("✅ Файл успешно обработан!")
                    
                    # Test query
                    print("\n🔍 Тестирование поиска...")
                    results = trainer.query("СП 45", k=3)
                    
                    if results and "results" in results:
                        print(f"📋 Найдено результатов: {len(results['results'])}")
                        for i, result in enumerate(results['results'][:2], 1):
                            print(f"  {i}. {result.get('chunk', '')[:100]}...")
                            print(f"     Score: {result.get('score', 0):.3f}")
                    else:
                        print("❌ Поиск не вернул результатов")
                        
                else:
                    print("❌ Файл НЕ обработан (возможно, дубликат)")
                    
            except Exception as e:
                print(f"❌ Ошибка при обработке файла: {e}")
                import traceback
                traceback.print_exc()
                
        else:
            print(f"❌ Тестовый файл не найден: {test_file}")
            print("📁 Доступные файлы:")
            
            base_path = "I:/docs/БАЗА"
            if os.path.exists(base_path):
                files = list(Path(base_path).glob("*.pdf"))[:5]
                for file in files:
                    print(f"  - {file}")
                    
                if files:
                    # Try first available file
                    first_file = str(files[0])
                    print(f"\n🧪 Тестирование на первом доступном файле: {first_file}")
                    
                    try:
                        success = trainer.process_document(first_file, update_callback=progress_callback)
                        if success:
                            print("✅ Первый файл успешно обработан!")
                        else:
                            print("❌ Первый файл НЕ обработан")
                    except Exception as e:
                        print(f"❌ Ошибка: {e}")
            else:
                print(f"❌ Базовая папка не найдена: {base_path}")
                
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Проверьте, что все зависимости установлены")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()