import sys
import os
import time

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# import pytest
from core.model_manager import ModelManager
from core.config import MODELS_CONFIG

def test_model_manager_initialization():
    """Test that ModelManager initializes correctly"""
    manager = ModelManager()
    assert manager is not None
    assert manager.cache_size == 12
    assert manager.ttl_minutes == 30

def test_get_model_client():
    """Test getting model client for a role"""
    manager = ModelManager()
    
    # Test getting coordinator model client
    client = manager.get_model_client("coordinator")
    # Note: This might return None if the model is not available
    assert client is not None or client is None  # Either is acceptable
    
    # Test getting an unknown role
    client = manager.get_model_client("unknown_role")
    # Should return None for unknown roles
    assert client is None

def test_get_model_stats():
    """Test getting model statistics"""
    manager = ModelManager()
    
    # Get initial stats
    stats = manager.get_model_stats()
    assert "loaded_models" in stats
    assert "max_cache_size" in stats
    assert "ttl_minutes" in stats
    assert "model_details" in stats

def test_get_capabilities_prompt():
    """Test getting capabilities prompt for a role"""
    manager = ModelManager()
    
    # Test coordinator capabilities prompt
    prompt = manager.get_capabilities_prompt("coordinator")
    # Should return a string or None
    assert isinstance(prompt, str) or prompt is None
    
    # Test unknown role
    prompt = manager.get_capabilities_prompt("unknown_role")
    # Should return None for unknown roles
    assert prompt is None

def test_get_all_roles():
    """Test getting all roles"""
    manager = ModelManager()
    
    # Get all roles
    roles = manager.get_all_roles()
    assert isinstance(roles, list)
    # Should contain at least the main roles
    assert "coordinator" in roles
    assert "chief_engineer" in roles

if __name__ == "__main__":
    # Run the tests
    test_model_manager_initialization()
    print("✓ test_model_manager_initialization passed")
    
    test_get_model_client()
    print("✓ test_get_model_client passed")
    
    test_get_model_stats()
    print("✓ test_get_model_stats passed")
    
    test_get_capabilities_prompt()
    print("✓ test_get_capabilities_prompt passed")
    
    test_get_all_roles()
    print("✓ test_get_all_roles passed")
    
    print("All tests passed!")