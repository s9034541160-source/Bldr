#!/usr/bin/env python3
"""
ENTERPRISE RAG 3.0: File Renamer
Переименование файлов на основе канонических ID из Qdrant
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FileRenamer:
    """Переименование файлов на основе метаданных из RAG системы"""
    
    def __init__(self, base_dir: str = "I:\\docs\\downloaded"):
        self.base_dir = Path(base_dir)
        self.renamed_count = 0
        self.skipped_count = 0
        self.error_count = 0
        
    def get_file_hash(self, file_path: Path) -> str:
        """Получение хэша файла"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Ошибка получения хэша {file_path}: {e}")
            return ""
    
    def get_metadata_from_qdrant(self, file_hash: str) -> Optional[Dict]:
        """Получение метаданных из Qdrant по хэшу файла"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            
            client = QdrantClient(host="localhost", port=6333)
            
            # Поиск по хэшу файла
            search_result = client.scroll(
                collection_name="enterprise_docs",
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="file_hash",
                            match=models.MatchValue(value=file_hash)
                        )
                    ]
                ),
                limit=1
            )
            
            if search_result[0]:  # Если найдены результаты
                point = search_result[0][0]
                return point.payload
                
        except Exception as e:
            logger.error(f"Ошибка получения метаданных из Qdrant: {e}")
            
        return None
    
    def sanitize_filename(self, filename: str) -> str:
        """Очистка имени файла от недопустимых символов"""
        # Заменяем недопустимые символы
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Убираем множественные подчеркивания
        while '__' in filename:
            filename = filename.replace('__', '_')
        
        # Ограничиваем длину
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename.strip()
    
    def rename_file(self, file_path: Path) -> bool:
        """Переименование одного файла"""
        try:
            # Получаем хэш файла
            file_hash = self.get_file_hash(file_path)
            if not file_hash:
                return False
            
            # Получаем метаданные из Qdrant
            metadata = self.get_metadata_from_qdrant(file_hash)
            if not metadata:
                logger.warning(f"Метаданные не найдены для {file_path.name}")
                self.skipped_count += 1
                return False
            
            # Извлекаем канонический ID
            canonical_id = metadata.get('canonical_id', '')
            if not canonical_id or canonical_id == 'UNKNOWN':
                logger.warning(f"Канонический ID не найден для {file_path.name}")
                self.skipped_count += 1
                return False
            
            # Создаем новое имя файла
            new_name = self.sanitize_filename(f"{canonical_id}.pdf")
            new_path = file_path.parent / new_name
            
            # Проверяем, не существует ли уже файл с таким именем
            if new_path.exists() and new_path != file_path:
                logger.warning(f"Файл {new_name} уже существует, пропускаем {file_path.name}")
                self.skipped_count += 1
                return False
            
            # Переименовываем файл
            file_path.rename(new_path)
            logger.info(f"✅ Переименован: {file_path.name} -> {new_name}")
            self.renamed_count += 1
            return True
            
        except Exception as e:
            logger.error(f"Ошибка переименования {file_path.name}: {e}")
            self.error_count += 1
            return False
    
    def process_directory(self, directory: Optional[Path] = None) -> Dict:
        """Обработка всех файлов в директории"""
        if directory is None:
            directory = self.base_dir
        
        if not directory.exists():
            logger.error(f"Директория не найдена: {directory}")
            return {"error": "Directory not found"}
        
        logger.info(f"Начинаем переименование файлов в {directory}")
        
        # Находим все PDF файлы
        pdf_files = list(directory.glob("*.pdf"))
        logger.info(f"Найдено {len(pdf_files)} PDF файлов")
        
        # Обрабатываем каждый файл
        for file_path in pdf_files:
            self.rename_file(file_path)
        
        # Статистика
        result = {
            "total_files": len(pdf_files),
            "renamed": self.renamed_count,
            "skipped": self.skipped_count,
            "errors": self.error_count
        }
        
        logger.info(f"Обработка завершена: {result}")
        return result
    
    def create_rename_report(self, result: Dict, output_file: str = "rename_report.json"):
        """Создание отчета о переименовании"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"Отчет сохранен в {output_file}")
        except Exception as e:
            logger.error(f"Ошибка сохранения отчета: {e}")

def main():
    """Основная функция"""
    logger.info("=== ENTERPRISE RAG 3.0: FILE RENAMER ===")
    
    # Параметры командной строки
    base_dir = "I:\\docs\\downloaded"
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    
    try:
        # Создаем переименователь
        renamer = FileRenamer(base_dir)
        
        # Обрабатываем файлы
        result = renamer.process_directory()
        
        # Создаем отчет
        renamer.create_rename_report(result)
        
        logger.info("=== ПЕРЕИМЕНОВАНИЕ ЗАВЕРШЕНО ===")
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
