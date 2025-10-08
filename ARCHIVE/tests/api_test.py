import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Test basic functionality without authentication
def test_basic_functionality():
    # Test regex patterns
    from regex_patterns import DOCUMENT_TYPE_PATTERNS, SEED_WORK_PATTERNS
    
    # Check that all required categories are present
    required_categories = [
        'norms', 'ppr', 'smeta', 'rd', 'educational',
        'finance', 'safety', 'ecology', 'accounting', 'hr',
        'logistics', 'procurement', 'insurance'
    ]
    
    for category in required_categories:
        assert category in DOCUMENT_TYPE_PATTERNS, f"Missing category: {category}"
        assert 'keywords' in DOCUMENT_TYPE_PATTERNS[category], f"Missing keywords for {category}"
        assert 'subtype_patterns' in DOCUMENT_TYPE_PATTERNS[category], f"Missing subtype_patterns for {category}"
        
        assert category in SEED_WORK_PATTERNS, f"Missing category in SEED_WORK_PATTERNS: {category}"
        assert len(SEED_WORK_PATTERNS[category]) > 0, f"No patterns for {category}"
    
    print("✅ All regex patterns are present and correct")
    
    # Test norms updater
    from core.norms_updater import NormsUpdater
    updater = NormsUpdater()
    required_sources = [
        "minstroyrf.ru", "consultant.ru", "rosstat.gov.ru",
        "mintrud.gov.ru", "rospotrebnadzor.ru", "nalog.gov.ru",
        "minfin.ru", "minprirody.ru"
    ]
    
    for source in required_sources:
        assert source in updater.sources, f"Missing source: {source}"
    
    print("✅ All norms updater sources are present")
    
    # Test RAG trainer
    from scripts.bldr_rag_trainer import BldrRAGTrainer
    trainer = BldrRAGTrainer(use_advanced_embeddings=False)  # Use simpler model for testing
    assert hasattr(trainer, 'query_with_category'), "Missing query_with_category method"
    
    print("✅ RAG trainer initialized successfully with query_with_category method")
    
    print("🎉 All basic functionality tests passed!")

if __name__ == "__main__":
    test_basic_functionality()