"""
Comprehensive End-to-End Tests for Bldr Empire v2 Multi-Agent System
"""

import pytest
import json
import os
import time
import requests
from pathlib import Path
import pandas as pd

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 60  # Increased timeout for comprehensive tests
REAL_LM_TESTS = os.getenv('REAL_LM', 'false').lower() == 'true'

@pytest.fixture(scope="session")
def api_client():
    """Create a session for API requests"""
    session = requests.Session()
    return session

def test_health_check_comprehensive(api_client):
    """Test API health endpoint with detailed component status"""
    response = api_client.get(f"{API_BASE_URL}/health", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OK"
    assert "components" in data
    
    # Check individual component statuses
    components = data["components"]
    assert "api" in components
    assert "neo4j" in components
    assert "redis" in components
    assert "celery" in components
    assert "lm_studio" in components

def test_frontend_query_e2e(api_client):
    """Test complete frontend query flow"""
    if not REAL_LM_TESTS:
        pytest.skip("Skipping real LM tests. Set REAL_LM=true to run.")
    
    # Prepare query data
    query_data = {
        "query": "Проверь фото на СП31 + смета ГЭСН Екатеринбург",
        "source": "frontend"
    }
    
    try:
        # Submit query
        response = api_client.post(
            f"{API_BASE_URL}/submit_query",
            json=query_data,
            timeout=TEST_TIMEOUT
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "query_id" in data
        assert "status" in data
        
    except requests.exceptions.ConnectionError:
        pytest.skip("API not running, skipping frontend query test")

def test_queue_view_endpoint():
    """Test /queue view endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/queue", timeout=TEST_TIMEOUT)
        # Should return 200 or proper authentication error
        assert response.status_code in [200, 401, 403]
    except requests.exceptions.ConnectionError:
        pytest.skip("API not running, skipping queue view test")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])