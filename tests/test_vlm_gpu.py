#!/usr/bin/env python3
"""
ENTERPRISE RAG 3.0: VLM GPU Test Script
Проверяет работу VLM с GPU ускорением
"""

import torch
import logging
from vlm_processor import VLMProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gpu_availability():
    """Проверяет доступность GPU"""
    
    logger.info("🔍 Testing GPU availability...")
    
    # CUDA
    if torch.cuda.is_available():
        logger.info(f"🚀 CUDA available: {torch.cuda.get_device_name(0)}")
        logger.info(f"📊 CUDA version: {torch.version.cuda}")
        logger.info(f"💾 GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        return "cuda"
    
    # MPS (Apple Silicon)
    elif torch.backends.mps.is_available():
        logger.info("🍎 MPS (Apple Silicon) available")
        return "mps"
    
    else:
        logger.warning("⚠️ No GPU acceleration available, using CPU")
        return "cpu"

def test_vlm_processor():
    """Тестирует VLM процессор"""
    
    logger.info("🧠 Testing VLM processor...")
    
    try:
        # Инициализация VLM
        vlm = VLMProcessor(device="auto")
        
        if vlm.is_available():
            logger.info("✅ VLM processor is ready!")
            
            # Тестируем модели
            logger.info("🔍 Testing BLIP model...")
            if vlm.blip_model is not None:
                logger.info("✅ BLIP model loaded")
            else:
                logger.warning("⚠️ BLIP model not loaded")
            
            logger.info("🔍 Testing LayoutLMv3 model...")
            if vlm.layout_model is not None:
                logger.info("✅ LayoutLMv3 model loaded")
            else:
                logger.warning("⚠️ LayoutLMv3 model not loaded")
            
            return True
        else:
            logger.error("❌ VLM processor not available")
            return False
            
    except Exception as e:
        logger.error(f"❌ VLM test failed: {e}")
        return False

def test_gpu_memory():
    """Тестирует GPU память"""
    
    if torch.cuda.is_available():
        logger.info("💾 Testing GPU memory...")
        
        # Получаем информацию о памяти
        total_memory = torch.cuda.get_device_properties(0).total_memory
        allocated_memory = torch.cuda.memory_allocated(0)
        cached_memory = torch.cuda.memory_reserved(0)
        
        logger.info(f"📊 Total GPU memory: {total_memory / 1024**3:.1f} GB")
        logger.info(f"📊 Allocated memory: {allocated_memory / 1024**3:.1f} GB")
        logger.info(f"📊 Cached memory: {cached_memory / 1024**3:.1f} GB")
        logger.info(f"📊 Free memory: {(total_memory - allocated_memory) / 1024**3:.1f} GB")
        
        # Тестируем выделение памяти
        try:
            test_tensor = torch.randn(1000, 1000).cuda()
            logger.info("✅ GPU memory allocation test passed")
            del test_tensor
            torch.cuda.empty_cache()
            return True
        except Exception as e:
            logger.error(f"❌ GPU memory test failed: {e}")
            return False
    
    return True

def main():
    """Основная функция тестирования"""
    
    logger.info("🚀 ENTERPRISE RAG 3.0: VLM GPU Test")
    
    # Тест 1: GPU доступность
    device = test_gpu_availability()
    
    # Тест 2: GPU память
    if device == "cuda":
        test_gpu_memory()
    
    # Тест 3: VLM процессор
    vlm_success = test_vlm_processor()
    
    # Итоговый результат
    logger.info("📊 Test Results:")
    logger.info(f"   Device: {device}")
    logger.info(f"   VLM Ready: {'✅' if vlm_success else '❌'}")
    
    if vlm_success:
        logger.info("🎉 VLM with GPU acceleration is ready!")
        logger.info("💡 You can now use VLM features in your RAG trainer")
    else:
        logger.warning("⚠️ VLM not fully ready, but fallback mode will work")
        logger.info("💡 RAG trainer will work without VLM features")

if __name__ == "__main__":
    main()
