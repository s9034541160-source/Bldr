"""
Integration test for coordinator and tools system
"""

import json
from core.tools_system import ToolsSystem
from core.coordinator import Coordinator
from core.model_manager import ModelManager

# Mock classes for testing
class MockRAGSystem:
    def query(self, query_text):
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
        pass
    
    def get_model_client(self, role):
        return f"Модель для {role}"

def test_coordinator_tool_execution():
    """Test that coordinator can execute tools from a plan"""
    # Initialize components
    rag_system = MockRAGSystem()
    model_manager = MockModelManager()
    tools_system = ToolsSystem(rag_system, model_manager)
    coordinator = Coordinator(model_manager, tools_system, rag_system)
    
    # Create a test plan with tools
    test_plan = {
        "status": "planning",
        "query_type": "financial",
        "requires_tools": True,
        "tools": [
            {"name": "search_knowledge_base", "arguments": {"query": "cl.5.2 СП31", "doc_types": ["norms"]}},
            {"name": "calculate_estimate", "arguments": {"query": "Расчет стоимости фундамента"}}
        ],
        "roles_involved": ["analyst"],
        "required_data": ["расценки"],
        "next_steps": ["Поиск расценок", "Расчет стоимости"]
    }
    
    # Execute tools
    results = coordinator.execute_tools(test_plan)
    
    # Verify results
    assert len(results) == 2
    assert results[0]["tool"] == "search_knowledge_base"
    assert results[1]["tool"] == "calculate_estimate"
    assert "result" in results[0]
    assert "result" in results[1]
    
    print("✅ Coordinator tool execution test passed!")

def test_coordinator_process_request():
    """Test that coordinator can process a request and execute tools"""
    # Initialize components
    rag_system = MockRAGSystem()
    model_manager = MockModelManager()
    tools_system = ToolsSystem(rag_system, model_manager)
    coordinator = Coordinator(model_manager, tools_system, rag_system)
    
    # Process a request that should trigger tool execution
    user_input = "Рассчитайте стоимость устройства фундамента по ГЭСН 8-6-1.1"
    response = coordinator.process_request(user_input)
    
    # Verify response
    assert response is not None
    assert "найдена следующая информация" in response
    assert len(response) > 50  # Should be a substantial response
    
    print("✅ Coordinator process request test passed!")

if __name__ == "__main__":
    test_coordinator_tool_execution()
    test_coordinator_process_request()
    print("🎉 All integration tests passed!")