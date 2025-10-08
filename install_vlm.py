#!/usr/bin/env python3
"""
ENTERPRISE RAG 3.0: VLM Installation Script
Устанавливает все необходимые зависимости для Vision-Language Model
"""

import subprocess
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_package(package):
    """Устанавливает пакет через pip"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        logger.info(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install {package}: {e}")
        return False

def check_gpu():
    """Проверяет доступность GPU"""
    try:
        import torch
        if torch.cuda.is_available():
            logger.info(f"🚀 CUDA available: {torch.cuda.get_device_name(0)}")
            return True
        elif torch.backends.mps.is_available():
            logger.info("🍎 MPS (Apple Silicon) available")
            return True
        else:
            logger.warning("⚠️ No GPU acceleration available, using CPU")
            return False
    except ImportError:
        logger.warning("⚠️ PyTorch not installed, cannot check GPU")
        return False

def main():
    """Основная функция установки VLM"""
    
    logger.info("🚀 ENTERPRISE RAG 3.0: Installing VLM Dependencies")
    
    # Базовые зависимости
    basic_packages = [
        "torch>=2.0.0",
        "torchvision>=0.15.0", 
        "transformers>=4.30.0",
        "Pillow>=9.0.0",
        "opencv-python>=4.8.0",
        "pdf2image>=1.16.0",
        "pytesseract>=0.3.10",
        "accelerate>=0.20.0"
    ]
    
    # Опциональные зависимости для GPU
    gpu_packages = [
        "bitsandbytes>=0.39.0"
    ]
    
    # Проверяем GPU
    has_gpu = check_gpu()
    
    # Устанавливаем базовые пакеты
    logger.info("📦 Installing basic packages...")
    success_count = 0
    for package in basic_packages:
        if install_package(package):
            success_count += 1
    
    # Устанавливаем GPU пакеты если доступно
    if has_gpu:
        logger.info("🚀 Installing GPU acceleration packages...")
        for package in gpu_packages:
            if install_package(package):
                success_count += 1
    
    # Проверяем установку
    logger.info("🔍 Testing VLM installation...")
    
    try:
        from vlm_processor import VLMProcessor
        vlm = VLMProcessor()
        if vlm.is_available():
            logger.info("✅ VLM processor is ready!")
        else:
            logger.warning("⚠️ VLM processor not fully available")
    except Exception as e:
        logger.error(f"❌ VLM test failed: {e}")
    
    # Итоговая статистика
    total_packages = len(basic_packages) + (len(gpu_packages) if has_gpu else 0)
    logger.info(f"📊 Installation complete: {success_count}/{total_packages} packages installed")
    
    if success_count == total_packages:
        logger.info("🎉 VLM installation successful!")
        logger.info("💡 You can now use VLM features in your RAG trainer")
    else:
        logger.warning("⚠️ Some packages failed to install")
        logger.info("💡 You can still use the RAG trainer without VLM (fallback mode)")

if __name__ == "__main__":
    main()
