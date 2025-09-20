"""
Test script for the 14-stage symbiotic pipeline
"""

import os
import json
from pathlib import Path
from scripts.bldr_rag_trainer import BldrRAGTrainer

def create_dummy_pdf():
    """Create a dummy PDF file for testing"""
    dummy_content = """
    СП 45.13330.2017
    Организация строительного производства
    
    Раздел 1. Общие положения
    п. 1.1. Область применения
    п. 1.2. Нормативные ссылки
    
    Раздел 2. Основные требования
    п. 2.1. Технические требования
    п. 2.2. Требования безопасности
    
    Таблица 1. Сметные нормы
    Стоимость = 300 млн руб.
    Бетон класса B25
    Сталь класса A500
    
    Рисунок 1. Схема организации работ
    
    \\работа{Устройство фундамента}
    \\работа{Монтаж конструкций}
    \\зависимость{Устройство фундамента -> Монтаж конструкций}
    
    Нарушение требований п. 2.2 может привести к снижению качества.
    """
    
    # Create dummy PDF content file
    dummy_file = Path("data/norms_db/dummy_SP45.pdf")
    dummy_file.parent.mkdir(exist_ok=True, parents=True)
    
    with open(dummy_file, "w", encoding="utf-8") as f:
        f.write(dummy_content)
    
    return str(dummy_file)

def test_14_stage_pipeline():
    """Test the 14-stage symbiotic pipeline"""
    print("🚀 Testing 14-stage symbiotic pipeline...")
    
    # Create dummy PDF
    dummy_file = create_dummy_pdf()
    print(f"Created dummy file: {dummy_file}")
    
    # Initialize trainer
    trainer = BldrRAGTrainer()
    
    # Process document through all 14 stages
    success = trainer.process_document(dummy_file)
    
    if success:
        print("✅ Pipeline test completed successfully!")
        
        # Check if norms_full.json was created with 10K+ chunks
        norms_file = Path("data/reports/norms_full.json")
        if norms_file.exists():
            with open(norms_file, "r", encoding="utf-8") as f:
                norms_data = json.load(f)
            print(f"✅ norms_full.json created with {len(norms_data)} chunks")
            
            # Check if we have 10K+ chunks
            if len(norms_data) >= 10000:
                print("✅ 10K+ chunks requirement met")
            else:
                print(f"⚠️ Only {len(norms_data)} chunks (less than 10K)")
        else:
            print("❌ norms_full.json not found")
            
        # Check evaluation report
        eval_file = Path("data/reports/eval_report.json")
        if eval_file.exists():
            with open(eval_file, "r", encoding="utf-8") as f:
                eval_data = json.load(f)
            print(f"✅ Evaluation report created: {eval_data}")
            
            # Check NDCG
            ndcg = eval_data.get("avg_ndcg", 0)
            if ndcg >= 0.95:
                print(f"✅ NDCG requirement met: {ndcg}")
            else:
                print(f"⚠️ NDCG below requirement: {ndcg}")
        else:
            print("❌ Evaluation report not found")
            
    else:
        print("❌ Pipeline test failed!")

if __name__ == "__main__":
    test_14_stage_pipeline()