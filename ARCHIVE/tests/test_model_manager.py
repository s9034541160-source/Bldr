"""
Test file for model_manager.py with real Ollama client integration
"""

import sys
import os

# Add the parent directory to the path to import core modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.model_manager import ModelManager

def test_model_loading():
    """Test model loading with real Ollama client"""
    # Initialize model manager
    model_manager = ModelManager(cache_size=12, ttl_minutes=30)
    
    # Test loading a model client
    client = model_manager.get_model_client("coordinator")
    
    # Verify client structure
    if client is not None:
        # Check if it's a real client or mock
        if isinstance(client, dict) and client.get("is_mock", False):
            print("⚠️  Model manager returned mock client (Ollama not available)")
            assert "role" in client
            assert "model_name" in client
            assert "config" in client
        else:
            print("✅ Model manager returned real client")
            # For real client, we can't do much testing without Ollama running
            # But we can verify it's not None
            assert client is not None
    
    print("✅ Model loading test passed")
    return client

def test_model_query():
    """Test model query functionality"""
    # Initialize model manager
    model_manager = ModelManager(cache_size=12, ttl_minutes=30)
    
    # Test querying a model
    messages = [
        {"role": "user", "content": "Тестовый запрос для проверки модели"}
    ]
    
    response = model_manager.query("coordinator", messages)
    
    # Verify response
    assert response is not None
    assert isinstance(response, str)
    
    print(f"✅ Model query test passed - response length: {len(response)}")
    return response

def test_model_stats():
    """Test model statistics functionality"""
    # Initialize model manager
    model_manager = ModelManager(cache_size=12, ttl_minutes=30)
    
    # Get model stats
    stats = model_manager.get_model_stats()
    
    # Verify stats structure
    assert "loaded_models" in stats
    assert "max_cache_size" in stats
    assert "ttl_minutes" in stats
    assert "model_details" in stats
    
    print(f"✅ Model stats test passed - loaded models: {stats['loaded_models']}")
    return stats

def test_role_responsibilities():
    """Test role responsibilities functionality"""
    # Initialize model manager
    model_manager = ModelManager(cache_size=12, ttl_minutes=30)
    
    # Get responsibilities for coordinator role
    responsibilities = model_manager.get_role_responsibilities("coordinator")
    
    # Verify responsibilities
    assert isinstance(responsibilities, list)
    assert len(responsibilities) > 0
    
    print(f"✅ Role responsibilities test passed - coordinator has {len(responsibilities)} responsibilities")
    return responsibilities

if __name__ == "__main__":
    print("Running model manager tests...")
    
    # Run model loading test
    client_result = test_model_loading()
    
    # Run model query test
    query_result = test_model_query()
    
    # Run model stats test
    stats_result = test_model_stats()
    
    # Run role responsibilities test
    responsibilities_result = test_role_responsibilities()
    
    print(f"\n📊 Test Results:")
    print(f"  Model Loading: {'✅ Passed' if client_result else '❌ Failed'}")
    print(f"  Model Query: {'✅ Passed' if query_result else '❌ Failed'}")
    print(f"  Model Stats: {'✅ Passed' if stats_result else '❌ Failed'}")
    print(f"  Role Responsibilities: {'✅ Passed' if responsibilities_result else '❌ Failed'}")
    
    if client_result and query_result and stats_result and responsibilities_result:
        print("\n🎉 All model manager tests PASSED!")
    else:
        print("\n❌ Some model manager tests FAILED!")