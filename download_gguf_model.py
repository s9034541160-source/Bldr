"""
Скачивание GGUF модели Qwen3-8B для гибридного ансамбля
"""

import os
import requests
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_file(url: str, filepath: str):
    """Скачивание файла с прогресс-баром"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filepath, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=os.path.basename(filepath)) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        logger.info(f"✅ Файл скачан: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка скачивания: {e}")
        return False

def main():
    """Скачивание GGUF модели Qwen3-8B"""
    
    # Создаем директорию для моделей
    models_dir = "I:/models_cache"
    os.makedirs(models_dir, exist_ok=True)
    
    # URL для Qwen3-8B GGUF (Q4_K_M - оптимальный баланс качества/размера)
    gguf_url = "https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/main/qwen3-8b-q4_k_m.gguf"
    gguf_path = os.path.join(models_dir, "Qwen3-8B-Q4_K_M.gguf")
    
    # Проверяем, есть ли уже файл
    if os.path.exists(gguf_path):
        logger.info(f"✅ Модель уже существует: {gguf_path}")
        return
    
    logger.info(f"🔄 Скачивание Qwen3-8B GGUF...")
    logger.info(f"📁 Путь: {gguf_path}")
    logger.info(f"🌐 URL: {gguf_url}")
    
    # Скачиваем файл
    success = download_file(gguf_url, gguf_path)
    
    if success:
        file_size = os.path.getsize(gguf_path) / (1024**3)  # GB
        logger.info(f"✅ Модель скачана успешно!")
        logger.info(f"📊 Размер: {file_size:.2f} GB")
        logger.info(f"🎯 Готово для гибридного ансамбля!")
    else:
        logger.error("❌ Ошибка скачивания модели")

if __name__ == "__main__":
    main()
