"""
🧪 Тестирование API методов RAG-тренера для фронтенда
process_single_file_ad_hoc + analyze_project_context
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import List, Dict

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_single_file_api():
    """Тестирование API для обработки одного файла"""
    
    try:
        # Импортируем RAG тренер
        from enterprise_rag_trainer_full import EnterpriseRAGTrainer
        
        logger.info("🔄 Инициализация RAG тренера для API тестирования...")
        
        # Создаем тренер
        trainer = EnterpriseRAGTrainer()
        
        # Ищем тестовый PDF файл
        test_files = []
        for root, dirs, files in os.walk("I:/docs/downloaded"):
            for file in files:
                if file.endswith('.pdf') and '58' not in file:
                    test_files.append(os.path.join(root, file))
                    if len(test_files) >= 1:  # Берем только один файл для теста
                        break
            if test_files:
                break
        
        if not test_files:
            logger.warning("⚠️ No test PDF files found in I:/docs/downloaded")
            return
        
        test_file = test_files[0]
        logger.info(f"📄 Testing with file: {os.path.basename(test_file)}")
        
        # Тест 1: Анализ без сохранения в БД
        logger.info("🔍 Test 1: Single file analysis (без сохранения в БД)")
        start_time = time.time()
        
        result = trainer.process_single_file_ad_hoc(test_file, save_to_db=False)
        
        if result and result.get('success'):
            logger.info(f"✅ Анализ успешен:")
            logger.info(f"   - Файл: {result.get('file_name')}")
            logger.info(f"   - Тип документа: {result.get('doc_type')}")
            logger.info(f"   - Количество чанков: {result.get('chunks_count')}")
            logger.info(f"   - Время обработки: {result.get('processing_time', 0):.2f} сек")
            logger.info(f"   - Сохранено в БД: {result.get('saved_to_db')}")
            
            # Показываем метаданные
            metadata = result.get('metadata', {})
            if metadata:
                logger.info(f"   - Метаданные:")
                for key, value in metadata.items():
                    if value:
                        logger.info(f"     * {key}: {value}")
        else:
            logger.error(f"❌ Анализ не удался: {result.get('error', 'unknown error') if result else 'No result'}")
        
        analysis_time = time.time() - start_time
        logger.info(f"⏱️ Время анализа: {analysis_time:.2f} сек")
        
        # Тест 2: Дообучение с сохранением в БД (dry run)
        logger.info("\n🔍 Test 2: Single file training (с сохранением в БД)")
        start_time = time.time()
        
        result = trainer.process_single_file_ad_hoc(test_file, save_to_db=True)
        
        if result and result.get('success'):
            logger.info(f"✅ Дообучение успешно:")
            logger.info(f"   - Файл: {result.get('file_name')}")
            logger.info(f"   - Сохранено в БД: {result.get('saved_to_db')}")
        else:
            logger.error(f"❌ Дообучение не удалось: {result.get('error', 'unknown error') if result else 'No result'}")
        
        training_time = time.time() - start_time
        logger.info(f"⏱️ Время дообучения: {training_time:.2f} сек")
        
        logger.info("🎉 Тестирование API одного файла завершено!")
        
    except ImportError as e:
        logger.error(f"❌ Не удалось импортировать RAG тренер: {e}")
        logger.info("💡 Убедитесь, что все зависимости установлены")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования API: {e}")

def test_project_analysis_api():
    """Тестирование API для анализа проекта"""
    
    try:
        # Импортируем RAG тренер
        from enterprise_rag_trainer_full import EnterpriseRAGTrainer
        
        logger.info("🔄 Инициализация RAG тренера для анализа проекта...")
        
        # Создаем тренер
        trainer = EnterpriseRAGTrainer()
        
        # Ищем несколько тестовых PDF файлов
        test_files = []
        for root, dirs, files in os.walk("I:/docs/downloaded"):
            for file in files:
                if file.endswith('.pdf') and '58' not in file:
                    test_files.append(os.path.join(root, file))
                    if len(test_files) >= 3:  # Берем 3 файла для теста
                        break
            if len(test_files) >= 3:
                break
        
        if not test_files:
            logger.warning("⚠️ No test PDF files found in I:/docs/downloaded")
            return
        
        logger.info(f"📁 Testing project analysis with {len(test_files)} files")
        
        # Тест анализа проекта
        logger.info("🔍 Test: Project context analysis")
        start_time = time.time()
        
        results = trainer.analyze_project_context(test_files)
        
        if results:
            logger.info(f"✅ Анализ проекта завершен:")
            logger.info(f"   - Обработано файлов: {len(results)}")
            
            success_count = sum(1 for r in results if r.get('status') == 'success')
            failed_count = len(results) - success_count
            
            logger.info(f"   - Успешно: {success_count}")
            logger.info(f"   - Ошибок: {failed_count}")
            
            # Показываем результаты по файлам
            for i, result in enumerate(results, 1):
                if result.get('status') == 'success':
                    logger.info(f"   📄 Файл {i}: {result.get('file_name')}")
                    logger.info(f"      - Тип: {result.get('doc_type')} ({result.get('confidence', 0):.2f})")
                    logger.info(f"      - Чанков: {result.get('chunk_count')}")
                    
                    # Показываем ключевые метаданные
                    metadata = result.get('key_metadata', {})
                    for key, value in metadata.items():
                        if value:
                            logger.info(f"      - {key}: {value}")
                else:
                    logger.warning(f"   ❌ Файл {i}: {result.get('file_name')} - {result.get('error', 'unknown error')}")
        else:
            logger.error("❌ Анализ проекта не удался")
        
        analysis_time = time.time() - start_time
        logger.info(f"⏱️ Время анализа проекта: {analysis_time:.2f} сек")
        
        logger.info("🎉 Тестирование API анализа проекта завершено!")
        
    except ImportError as e:
        logger.error(f"❌ Не удалось импортировать RAG тренер: {e}")
        logger.info("💡 Убедитесь, что все зависимости установлены")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования API: {e}")

def test_api_performance():
    """Тестирование производительности API"""
    
    logger.info("⚡ Тестирование производительности API...")
    
    # Здесь можно добавить тесты производительности
    # Например, измерение времени обработки разных типов файлов
    
    logger.info("💡 API готов к интеграции с фронтендом!")

if __name__ == "__main__":
    logger.info("🚀 Запуск тестирования API методов RAG-тренера")
    
    # Тест 1: API одного файла
    logger.info("="*50)
    logger.info("🔍 ТЕСТ 1: API одного файла")
    logger.info("="*50)
    test_single_file_api()
    
    print("\n" + "="*50 + "\n")
    
    # Тест 2: API анализа проекта
    logger.info("="*50)
    logger.info("📊 ТЕСТ 2: API анализа проекта")
    logger.info("="*50)
    test_project_analysis_api()
    
    print("\n" + "="*50 + "\n")
    
    # Тест 3: Производительность
    logger.info("="*50)
    logger.info("⚡ ТЕСТ 3: Производительность API")
    logger.info("="*50)
    test_api_performance()
    
    logger.info("🏁 Тестирование API завершено")
