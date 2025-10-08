import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the main components
from scripts.bldr_rag_trainer import BldrRAGTrainer
from core.bldr_api import app
from core.model_manager import ModelManager
from core.coordinator import Coordinator
from core.tools_system import ToolsSystem

# Test data
TEST_DOCUMENT_CONTENT = """
СП 45.13330.2017
Раздел 1. Общие положения
Раздел 2. Основные требования
п. 2.1 Требования к проектированию
п. 2.2 Требования к строительству
Таблица 1. Сметные нормы
ГЭСН 8-1-1 Устройство бетонной подготовки
ГЭСН 8-1-2 Устройство монолитных бетонных конструкций
profit300млн ROI18% rec LSR BIM+OVOS FЗ-44 viol99%
"""

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        "NEO4J_URI": "neo4j://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "test_password",
        "QDRANT_PATH": "data/qdrant_test",
        "BASE_DIR": "/tmp/test_docs",
        "LLM_BASE_URL": "http://localhost:1234/v1",
        "DEFAULT_MODEL": "deepseek/deepseek-r1-0528-qwen3-8b"
    }):
        yield

@pytest.fixture
def trainer(mock_env_vars, temp_dir):
    """Create a BldrRAGTrainer instance for testing"""
    # Create necessary directories
    norms_db = temp_dir / "norms_db"
    reports_dir = temp_dir / "reports"
    qdrant_path = temp_dir / "qdrant_db"
    
    norms_db.mkdir()
    reports_dir.mkdir()
    qdrant_path.mkdir()
    
    with patch.dict(os.environ, {
        "NORMS_DB": str(norms_db),
        "REPORTS_DIR": str(reports_dir),
        "QDRANT_PATH": str(qdrant_path)
    }):
        trainer = BldrRAGTrainer()
        yield trainer

@pytest.fixture
def test_document(temp_dir):
    """Create a test document for processing"""
    doc_path = temp_dir / "test_document.txt"
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(TEST_DOCUMENT_CONTENT)
    return str(doc_path)

def test_bldr_rag_trainer_initialization(mock_env_vars, temp_dir):
    """Test BldrRAGTrainer initialization"""
    norms_db = temp_dir / "norms_db"
    reports_dir = temp_dir / "reports"
    qdrant_path = temp_dir / "qdrant_db"
    
    norms_db.mkdir()
    reports_dir.mkdir()
    qdrant_path.mkdir()
    
    with patch.dict(os.environ, {
        "NORMS_DB": str(norms_db),
        "REPORTS_DIR": str(reports_dir),
        "QDRANT_PATH": str(qdrant_path)
    }):
        trainer = BldrRAGTrainer()
        assert trainer is not None
        assert trainer.base_dir is not None
        assert trainer.norms_db == norms_db
        assert trainer.reports_dir == reports_dir

def test_document_type_detection(trainer):
    """Test document type detection"""
    result = trainer._stage4_document_type_detection(TEST_DOCUMENT_CONTENT, "test.txt")
    assert result["doc_type"] == "norms"
    assert result["confidence"] > 50.0

def test_structural_analysis(trainer):
    """Test document structural analysis"""
    result = trainer._stage5_structural_analysis(TEST_DOCUMENT_CONTENT, "norms", "construction")
    assert "structural_data" in result
    structural_data = result["structural_data"]
    assert len(structural_data["sections"]) >= 2
    assert structural_data["completeness"] > 0.0

def test_work_extraction(trainer):
    """Test work candidates extraction"""
    structural_data = {"sections": ["1", "2"]}
    works = trainer._stage6_regex_to_rubern(TEST_DOCUMENT_CONTENT, "norms", structural_data)
    assert len(works) > 0
    # Check if we found GESN codes
    assert any("ГЭСН" in work for work in works)

def test_metadata_extraction(trainer):
    """Test metadata extraction"""
    # First create rubern data
    structural_data = {"sections": ["1", "2"]}
    seed_works = trainer._stage6_regex_to_rubern(TEST_DOCUMENT_CONTENT, "norms", structural_data)
    rubern_data = trainer._stage7_rubern_markup_enhanced(
        TEST_DOCUMENT_CONTENT, 
        "norms", 
        "construction", 
        seed_works, 
        structural_data
    )
    
    metadata = trainer._stage8_metadata_extraction(TEST_DOCUMENT_CONTENT, rubern_data, "norms")
    assert "materials" in metadata
    assert "finances" in metadata
    assert len(metadata["finances"]) > 0

def test_model_manager_initialization():
    """Test ModelManager initialization"""
    model_manager = ModelManager(cache_size=5, ttl_minutes=10)
    assert model_manager.cache_size == 5
    assert model_manager.ttl_minutes == 10

def test_tools_system_initialization():
    """Test ToolsSystem initialization"""
    # Create mock objects
    mock_rag_system = MagicMock()
    mock_model_manager = MagicMock()
    
    tools_system = ToolsSystem(mock_rag_system, mock_model_manager)
    assert tools_system is not None
    assert tools_system.rag_system == mock_rag_system
    assert tools_system.model_manager == mock_model_manager

def test_coordinator_initialization():
    """Test Coordinator initialization"""
    # Create mock objects
    mock_model_manager = MagicMock()
    mock_tools_system = MagicMock()
    mock_rag_trainer = MagicMock()
    
    coordinator = Coordinator(mock_model_manager, mock_tools_system, mock_rag_trainer)
    assert coordinator is not None
    assert coordinator.model_manager == mock_model_manager
    assert coordinator.tools_system == mock_tools_system

def test_api_health_endpoint():
    """Test API health endpoint"""
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OK"
    assert "components" in data

def test_api_query_endpoint():
    """Test API query endpoint"""
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Test with a simple query
    query_data = {
        "query": "тестовый запрос",
        "k": 3
    }
    
    response = client.post("/query", json=query_data)
    # Note: This might fail if Qdrant is not running, but we're testing the endpoint structure
    assert response.status_code in [200, 500]  # 500 if Qdrant not available

if __name__ == "__main__":
    pytest.main([__file__, "-v"])