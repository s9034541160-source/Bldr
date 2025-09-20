import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Test that all required categories are present in regex_patterns
def test_document_type_patterns():
    from regex_patterns import DOCUMENT_TYPE_PATTERNS
    
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
    
    print("✅ All document type patterns are present")

def test_seed_work_patterns():
    from regex_patterns import SEED_WORK_PATTERNS
    
    # Check that all required categories are present
    required_categories = [
        'norms', 'ppr', 'smeta', 'rd', 'educational',
        'finance', 'safety', 'ecology', 'accounting', 'hr',
        'logistics', 'procurement', 'insurance'
    ]
    
    for category in required_categories:
        assert category in SEED_WORK_PATTERNS, f"Missing category: {category}"
        assert len(SEED_WORK_PATTERNS[category]) > 0, f"No patterns for {category}"
    
    print("✅ All seed work patterns are present")

def test_norms_updater_sources():
    from core.norms_updater import NormsUpdater
    
    # Check that norms updater has all required sources
    updater = NormsUpdater()
    required_sources = [
        "minstroyrf.ru", "consultant.ru", "rosstat.gov.ru",
        "mintrud.gov.ru", "rospotrebnadzor.ru", "nalog.gov.ru",
        "minfin.ru", "minprirody.ru"
    ]
    
    for source in required_sources:
        assert source in updater.sources, f"Missing source: {source}"
    
    print("✅ All norms updater sources are present")

if __name__ == "__main__":
    test_document_type_patterns()
    test_seed_work_patterns()
    test_norms_updater_sources()
    print("🎉 All tests passed! Russian NTD full spectrum coverage is implemented.")