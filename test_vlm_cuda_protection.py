#!/usr/bin/env python3
"""
Изолированный тест VLM обработки с защитой от CUDA ошибок
Тестирует только VLMProcessor без полного RAG тренера
"""

import sys
import os
import logging
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vlm_processor import VLMProcessor
from pdf2image import convert_from_path
import torch

def test_vlm_cuda_protection():
    """Тест VLM обработки с проблемными PDF"""
    
    print("TEST VLM CUDA PROTECTION")
    print("=" * 50)
    
    # Настройка логирования
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # Инициализация VLM процессора
        print("Initializing VLM processor...")
        vlm_processor = VLMProcessor()
        
        if not vlm_processor.is_available():
            print("ERROR: VLM not available, test skipped")
            return False
            
        print("SUCCESS: VLM processor initialized")
        
        # Test 1: Real PDF with Cyrillic
        print("\nTest 1: Real PDF with Cyrillic")
        
        # Find any PDF file in the directory
        pdf_files = []
        for root, dirs, files in os.walk("I:/docs/downloaded"):
            for file in files:
                if file.endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
                    if len(pdf_files) >= 3:  # Take first 3 PDFs
                        break
            if len(pdf_files) >= 3:
                break
        
        if pdf_files:
            test_pdf = pdf_files[0]
            print(f"Testing PDF: {os.path.basename(test_pdf)}")
            
            try:
                # Convert PDF to images
                images = convert_from_path(test_pdf, dpi=300)
                print(f"PDF converted: {len(images)} pages")
                
                # Test first page only
                if images:
                    image = images[0]
                    print(f"   Page size: {image.size}")
                    
                    # Test VLM analysis
                    try:
                        tables = vlm_processor._analyze_page_for_tables(image, 0)
                        print(f"   SUCCESS: VLM analysis completed: {len(tables)} tables found")
                        
                    except Exception as e:
                        print(f"   ERROR: VLM error: {e}")
                        if "CUDA" in str(e) or "assert" in str(e):
                            print(f"   CRITICAL: CUDA ERROR NOT CAUGHT!")
                            return False
                        else:
                            print(f"   WARNING: Other error (normal)")
                            
            except Exception as e:
                print(f"ERROR: PDF processing failed: {e}")
                return False
        else:
            print("WARNING: No PDF files found for testing")
            
        # Test 2: Empty image
        print("\nTest 2: Empty image")
        from PIL import Image
        
        # Create empty image
        empty_image = Image.new('RGB', (0, 0))
        print(f"   Empty image size: {empty_image.size}")
        
        try:
            tables = vlm_processor._analyze_page_for_tables(empty_image, 999)
            print(f"   SUCCESS: Empty image processed: {len(tables)} tables")
        except Exception as e:
            print(f"   ERROR: Empty image error: {e}")
            return False
            
        print("\nALL TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"CRITICAL: Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_vlm_cuda_protection()
    if success:
        print("\nSUCCESS: VLM protection works correctly!")
        sys.exit(0)
    else:
        print("\nFAILED: VLM protection DOES NOT WORK!")
        sys.exit(1)
