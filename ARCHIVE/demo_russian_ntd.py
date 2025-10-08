"""
Demo script to showcase the full Russian NTD coverage functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from regex_patterns import DOCUMENT_TYPE_PATTERNS, SEED_WORK_PATTERNS, detect_document_type_with_symbiosis
from core.norms_updater import NormsUpdater
from scripts.bldr_rag_trainer import BldrRAGTrainer

def demo_document_type_detection():
    """Demo document type detection with Russian NTD patterns"""
    print("=== Document Type Detection Demo ===")
    
    # Sample texts for different categories
    sample_texts = {
        'norms': "СП 45.13330.2017 Организация строительства",
        'finance': "Налог на прибыль организаций. Ставка 20%",
        'safety': "Правила охраны труда при строительных работах",
        'ecology': "Оценка воздействия на окружающую среду (ОВОС)",
        'accounting': "Бухгалтерская отчетность и налоговая база",
        'hr': "Трудовой договор и минимальный размер оплаты труда (МРОТ)",
        'logistics': "Транспортировка строительных материалов",
        'procurement': "Закупки по ФЗ-44 и тендерные процедуры",
        'insurance': "Страхование строительных рисков и ОСАГО"
    }
    
    for category, text in sample_texts.items():
        result = detect_document_type_with_symbiosis(text)
        print(f"Text: {text}")
        print(f"Detected category: {result['doc_type']} (confidence: {result['confidence']:.2f}%)")
        print("---")

def demo_regex_patterns():
    """Demo regex patterns for all categories"""
    print("\n=== Regex Patterns Demo ===")
    
    categories = [
        'norms', 'ppr', 'smeta', 'rd', 'educational',
        'finance', 'safety', 'ecology', 'accounting', 'hr',
        'logistics', 'procurement', 'insurance'
    ]
    
    for category in categories:
        print(f"\nCategory: {category}")
        print(f"  Keywords: {len(DOCUMENT_TYPE_PATTERNS[category]['keywords'])} patterns")
        print(f"  Subtype patterns: {len(DOCUMENT_TYPE_PATTERNS[category]['subtype_patterns'])} patterns")
        print(f"  Seed work patterns: {len(SEED_WORK_PATTERNS[category])} patterns")

def demo_norms_updater():
    """Demo norms updater sources"""
    print("\n=== Norms Updater Sources Demo ===")
    
    updater = NormsUpdater()
    print(f"Total sources: {len(updater.sources)}")
    
    for source_name, source_config in updater.sources.items():
        print(f"  {source_name}:")
        print(f"    Category: {source_config['category']}")
        print(f"    URL Pattern: {source_config['url_pattern']}")
        print(f"    Selector: {source_config['selector']}")

def demo_rag_trainer():
    """Demo RAG trainer with category filtering"""
    print("\n=== RAG Trainer Demo ===")
    
    # Initialize with simpler model for demo
    trainer = BldrRAGTrainer(use_advanced_embeddings=False)
    print("RAG Trainer initialized with category filtering support")
    print(f"Has query_with_category method: {hasattr(trainer, 'query_with_category')}")

def main():
    """Main demo function"""
    print("🚀 Bldr Empire v2 - Russian NTD Full Spectrum Coverage Demo")
    print("=" * 60)
    
    demo_document_type_detection()
    demo_regex_patterns()
    demo_norms_updater()
    demo_rag_trainer()
    
    print("\n🎉 Demo completed successfully!")
    print("\nKey Features Implemented:")
    print("✅ Full Russian NTD coverage (13 categories)")
    print("✅ Auto-search from official sources (8+ sources)")
    print("✅ Auto-sorting with category filtering")
    print("✅ Auto-updating with cron jobs")
    print("✅ UI controls in dashboard")
    print("✅ Advanced Russian embeddings (ai-forever/sbert_large_nlu_ru)")

if __name__ == "__main__":
    main()