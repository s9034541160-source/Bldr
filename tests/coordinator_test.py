"""
Test suite for the Coordinator component
"""

import sys
import os
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.coordinator import Coordinator
from core.model_manager import ModelManager

# Mock classes for testing
class MockToolsSystem:
    def execute_tool_call(self, tool_plan):
        """Mock tool execution"""
        results = []
        for tool_call in tool_plan:
            tool_name = tool_call.get("name", "")
            arguments = tool_call.get("arguments", {})
            
            # Simulate tool execution results
            if tool_name == "search_rag_database":
                result = {
                    "status": "success",
                    "results": [
                        {
                            "chunk": "Результат поиска для запроса: cl.5.2 СП31",
                            "meta": {"conf": 0.99, "entities": {"ORG": ["СП31", "BIM"], "MONEY": ["300млн"]}},
                            "score": 0.99,
                            "tezis": "profit300млн ROI18% rec LSR BIM+OVOS FЗ-44 conf0.99",
                            "viol": 99
                        }
                    ],
                    "ndcg": 0.95
                }
            else:
                result = {
                    "status": "success",
                    "result": f"Результат выполнения инструмента {tool_name}"
                }
            
            results.append({
                "tool": tool_name,
                "arguments": arguments,
                "result": result,
                "status": "success"
            })
        return results

class MockRAGSystem:
    def query(self, query_text, k=5):
        return {
            "results": [
                {
                    "chunk": f"Результат поиска для запроса: {query_text}",
                    "meta": {"conf": 0.99, "entities": {"ORG": ["СП31", "BIM"], "MONEY": ["300млн"]}},
                    "score": 0.99,
                    "tezis": "profit300млн ROI18% rec LSR BIM+OVOS FЗ-44 conf0.99",
                    "viol": 99
                }
            ],
            "ndcg": 0.95
        }

class MockModelManager(ModelManager):
    def __init__(self):
        # Initialize with minimal configuration for testing
        super().__init__(cache_size=5, ttl_minutes=10)
    
    def get_model_client(self, role):
        """Mock model client retrieval"""
        return f"Модель для {role}"

def test_coordinator_plan_generation():
    """Test that coordinator generates correct plan for 'cl.5.2 СП31' query"""
    # Arrange
    model_manager = MockModelManager()
    tools_system = MockToolsSystem()
    rag_system = MockRAGSystem()
    coordinator = Coordinator(model_manager, tools_system, rag_system)
    
    # Act
    plan = coordinator.analyze_request("cl.5.2 СП31")
    
    # Assert
    assert plan["status"] == "planning"
    assert "tools" in plan
    assert len(plan["tools"]) > 0
    
    # Check that search_rag_database is in the tools
    tool_names = [tool["name"] for tool in plan["tools"]]
    assert "search_rag_database" in tool_names

def test_coordinator_tool_execution():
    """Test that coordinator executes tools correctly"""
    # Arrange
    model_manager = MockModelManager()
    tools_system = MockToolsSystem()
    rag_system = MockRAGSystem()
    coordinator = Coordinator(model_manager, tools_system, rag_system)
    
    plan = {
        "tools": [
            {"name": "search_rag_database", "arguments": {"query": "cl.5.2 СП31", "doc_types": ["norms"]}}
        ]
    }
    
    # Act
    tool_results = coordinator.execute_tools(plan)
    
    # Assert
    assert len(tool_results) == 1
    assert tool_results[0]["tool"] == "search_rag_database"
    assert tool_results[0]["status"] == "success"
    assert "result" in tool_results[0]

def test_coordinator_synthesis():
    """Test that coordinator synthesizes response with real tool results"""
    # Arrange
    model_manager = MockModelManager()
    tools_system = MockToolsSystem()
    rag_system = MockRAGSystem()
    coordinator = Coordinator(model_manager, tools_system, rag_system)
    
    user_query = "cl.5.2 СП31"
    tool_results = [
        {
            "tool": "search_rag_database",
            "arguments": {"query": "cl.5.2 СП31", "doc_types": ["norms"]},
            "result": {
                "status": "success",
                "results": [
                    {
                        "chunk": "Результат поиска для запроса: cl.5.2 СП31",
                        "meta": {"conf": 0.99, "entities": {"ORG": ["СП31", "BIM"], "MONEY": ["300млн"]}},
                        "score": 0.99,
                        "tezis": "profit300млн ROI18% rec LSR BIM+OVOS FЗ-44 conf0.99",
                        "viol": 99
                    }
                ],
                "ndcg": 0.95
            },
            "status": "success"
        }
    ]
    
    specialist_responses = [
        {
            "role": "chief_engineer",
            "response": "Технический анализ показывает соответствие нормам СП31",
            "tool_results": tool_results
        }
    ]
    
    # Act
    response = coordinator.synthesize_response(user_query, tool_results, specialist_responses)
    
    # Assert
    assert "[ИНСТРУМЕНТ: search_rag_database]" in response
    assert "[СПЕЦИАЛИСТ: chief_engineer]" in response

def test_analyze_request_complexity():
    """Test request complexity analysis"""
    # Arrange
    model_manager = MockModelManager()
    tools_system = MockToolsSystem()
    rag_system = MockRAGSystem()
    coordinator = Coordinator(model_manager, tools_system, rag_system)
    
    # Act & Assert
    assert coordinator.analyze_request_complexity("cl.5.2 СП31") == "norms"
    assert coordinator.analyze_request_complexity("Проект производства работ") == "ppr"
    assert coordinator.analyze_request_complexity("Расчет сметы по ГЭСН") == "estimate"
    assert coordinator.analyze_request_complexity("Рабочая документация") == "rd"
    assert coordinator.analyze_request_complexity("Учебные материалы") == "educational"
    assert coordinator.analyze_request_complexity("Общий запрос") == "general"

def test_history_management():
    """Test history management with locking and max length"""
    # Arrange
    model_manager = MockModelManager()
    tools_system = MockToolsSystem()
    rag_system = MockRAGSystem()
    coordinator = Coordinator(model_manager, tools_system, rag_system)
    
    # Act
    # Add multiple entries to test history management
    for i in range(10):
        coordinator._add_to_history({
            "type": "test_entry",
            "content": f"Test entry {i}",
            "timestamp": i
        })
    
    # Assert
    # Check that history is managed correctly
    assert len(coordinator.history) == 10
    assert coordinator.history[0]["content"] == "Test entry 0"
    assert coordinator.history[-1]["content"] == "Test entry 9"
    
    # Test max length limitation
    for i in range(100):
        coordinator._add_to_history({
            "type": "test_entry",
            "content": f"Test entry {i+10}",
            "timestamp": i+10
        })
    
    # Should be limited to max_history_length (100)
    assert len(coordinator.history) <= coordinator.max_history_length

def test_process_request_integration():
    """Test full request processing integration"""
    # Arrange
    model_manager = MockModelManager()
    tools_system = MockToolsSystem()
    rag_system = MockRAGSystem()
    coordinator = Coordinator(model_manager, tools_system, rag_system)
    
    # Act
    response = coordinator.process_request("cl.5.2 СП31")
    
    # Assert
    # Should contain instrument results
    assert "[ИНСТРУМЕНТ:" in response
    # Should not contain thinking/mind process text
    assert "мышление" not in response.lower()
    assert "thinking" not in response.lower()

if __name__ == "__main__":
    # Run all tests
    test_functions = [
        test_coordinator_plan_generation,
        test_coordinator_tool_execution,
        test_coordinator_synthesis,
        test_analyze_request_complexity,
        test_history_management,
        test_process_request_integration
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            print(f"Running {test_func.__name__}...")
            test_func()
            print(f"✓ {test_func.__name__} passed")
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            failed += 1
    
    print(f"\nTest Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL COORDINATOR TESTS PASSED!")
    else:
        print("❌ Some tests failed. Please check the implementation.")