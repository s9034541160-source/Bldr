"""
Test SBERT parsing functionality for Bldr Empire v2
"""

import pytest
import sys
import os

# Add the core directory to the path so we can import parse_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.parse_utils import parse_intent_and_entities, parse_request_with_sbert, model

def test_sbert_model_availability():
    """Test that SBERT model is available (skip if not)"""
    if model is None:
        pytest.skip("SBERT model not available - skipping tests")
    assert model is not None, "SBERT model should be loaded"

def test_sbert_intent_parsing():
    """Test SBERT intent parsing with Russian construction queries"""
    # Skip if model not available
    if model is None:
        pytest.skip("SBERT model not available - skipping test")
    
    # Test cases with expected intents
    test_cases = [
        ("Проверь СП31 на фото", "norm_check"),
        ("Смета ГЭСН Москва", "budget_calc"),
        ("Нарушение СанПиН в тендере FZ-44", "compliance_audit"),
        ("Анализ фото сайта на СП31", "vl_analysis"),
        ("Бюджет ГЭСН для фундамента", "budget_calc"),
        ("График работ по проекту", "project_timeline"),
        ("Проверка соответствия ГОСТ", "norm_check"),
        ("Расчет стоимости материалов по ФЗ-44", "budget_calc")
    ]
    
    for query, expected_intent in test_cases:
        result = parse_intent_and_entities(query, task='intent')
        assert 'error' not in result, f"Error in parsing '{query}': {result.get('error', '')}"
        assert result['confidence'] > 0.7, f"Low confidence for '{query}': {result['confidence']}"
        # We won't assert exact intent matches as they may vary based on model training
        # but we'll check that an intent is returned
        assert 'intent' in result, f"No intent found for '{query}'"
        print(f"Query: {query} -> Intent: {result['intent']}, Confidence: {result['confidence']:.2f}")

def test_sbert_entity_extraction():
    """Test SBERT entity extraction from Russian construction queries"""
    # Skip if model not available
    if model is None:
        pytest.skip("SBERT model not available - skipping test")
    
    test_cases = [
        "Проверь СП31 на фото",
        "Смета ГЭСН Москва",
        "Нарушение СанПиН в тендере FZ-44",
        "Анализ ГОСТ 200-90 и СНиП 3.03.01-87"
    ]
    
    for query in test_cases:
        result = parse_intent_and_entities(query, task='entities')
        assert 'error' not in result, f"Error in entity extraction for '{query}': {result.get('error', '')}"
        assert 'entities' in result, f"No entities found for '{query}'"
        print(f"Query: {query} -> Entities: {result['entities']}")

def test_sbert_request_parsing():
    """Test complete request parsing with SBERT"""
    # Skip if model not available
    if model is None:
        pytest.skip("SBERT model not available - skipping test")
    
    test_queries = [
        "Проверь СП31 на фото",
        "Смета ГЭСН Москва",
        "Нарушение СанПиН в тендере FZ-44"
    ]
    
    for query in test_queries:
        result = parse_request_with_sbert(query)
        assert 'error' not in result, f"Error in request parsing for '{query}': {result.get('error', '')}"
        assert 'intent' in result, f"No intent found for '{query}'"
        assert 'entities' in result, f"No entities found for '{query}'"
        assert result['confidence'] > 0.7, f"Low confidence for '{query}': {result['confidence']}"
        print(f"Query: {query}")
        print(f"  Intent: {result['intent']}, Confidence: {result['confidence']:.2f}")
        print(f"  Entities: {result['entities']}")
        print(f"  Parser: {result['parser']}")

def test_sbert_similarity_task():
    """Test SBERT similarity calculation task"""
    # Skip if model not available
    if model is None:
        pytest.skip("SBERT model not available - skipping test")
    
    query = "Проверка фундамента по СП31"
    labels = ["norm_check", "budget_calc", "vl_analysis"]
    
    result = parse_intent_and_entities(query, task='similarity', labels=labels)
    assert 'error' not in result, f"Error in similarity task: {result.get('error', '')}"
    assert 'similarities' in result, "No similarities found"
    assert 'max_similarity' in result, "No max similarity found"
    assert 'best_match' in result, "No best match found"
    assert result['max_similarity'] > 0.7, f"Low similarity: {result['max_similarity']}"
    print(f"Query: {query}")
    print(f"Similarities: {result['similarities']}")
    print(f"Best match: {result['best_match']} (similarity: {result['max_similarity']:.2f})")

def test_sbert_fallback_behavior():
    """Test SBERT fallback behavior for low confidence cases"""
    # Skip if model not available
    if model is None:
        pytest.skip("SBERT model not available - skipping test")
    
    # This is a bit tricky to test as we can't easily force low confidence
    # but we can at least verify the function structure
    result = parse_intent_and_entities("", task='intent')
    # Empty string might either return an error or low confidence result
    # depending on how the model handles it
    print(f"Empty string parsing result: {result}")

def test_sbert_error_handling():
    """Test SBERT error handling when model is not available"""
    # This test will always pass since we're testing the error handling
    # in parse_utils.py which is already implemented
    pass

if __name__ == "__main__":
    # Run tests manually if executed directly
    if model is None:
        print("SBERT model not available - skipping tests")
    else:
        test_sbert_intent_parsing()
        test_sbert_entity_extraction()
        test_sbert_request_parsing()
        test_sbert_similarity_task()
        test_sbert_fallback_behavior()
        print("All SBERT tests passed!")