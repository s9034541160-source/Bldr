"""
Unit tests for the ToolsSystem
"""

import pytest
import json
from core.tools_system import ToolsSystem

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

class MockModelManager:
    def get_model_client(self, role):
        return f"Модель для {role}"

def test_tools_system_initialization():
    """Test that ToolsSystem initializes correctly"""
    rag_system = MockRAGSystem()
    model_manager = MockModelManager()
    
    tools_system = ToolsSystem(rag_system, model_manager)
    
    assert tools_system is not None
    assert tools_system.rag_system == rag_system
    assert tools_system.model_manager == model_manager

def test_get_available_tools():
    """Test that get_available_tools returns the correct list of tools"""
    rag_system = MockRAGSystem()
    model_manager = MockModelManager()
    
    tools_system = ToolsSystem(rag_system, model_manager)
    tools = tools_system.get_available_tools()
    
    # Check that we have the expected number of tools
    assert len(tools) > 10  # Should have at least 10 tools
    
    # Check that specific tools are present
    tool_names = [tool["name"] for tool in tools]
    assert "search_knowledge_base" in tool_names
    assert "calculate_estimate" in tool_names
    assert "create_document" in tool_names
    assert "analyze_image" in tool_names
    assert "financial_calculator" in tool_names

def test_execute_tool_search_knowledge_base():
    """Test executing the search_knowledge_base tool"""
    rag_system = MockRAGSystem()
    model_manager = MockModelManager()
    
    tools_system = ToolsSystem(rag_system, model_manager)
    
    # Test with valid arguments
    arguments = {
        "query": "cl.5.2 СП31",
        "doc_types": ["norms"]
    }
    
    result = tools_system.execute_tool("search_knowledge_base", arguments)
    
    assert result is not None
    assert "results" in result
    assert len(result["results"]) > 0
    assert result["results"][0]["chunk"] == "Результат поиска для запроса: cl.5.2 СП31"

def test_execute_tool_calculate_estimate():
    """Test executing the calculate_estimate tool"""
    rag_system = MockRAGSystem()
    model_manager = MockModelManager()
    
    tools_system = ToolsSystem(rag_system, model_manager)
    
    # Test with valid arguments
    arguments = {
        "query": "Расчет стоимости фундамента",
        "rate_code": "ГЭСН 8-6-1.1",
        "region": "Москва"
    }
    
    result = tools_system.execute_tool("calculate_estimate", arguments)
    
    assert result is not None
    assert "estimate" in result
    assert "rate_code" in result
    assert result["rate_code"] == "ГЭСН 8-6-1.1"

def test_execute_tool_create_document():
    """Test executing the create_document tool"""
    rag_system = MockRAGSystem()
    model_manager = MockModelManager()
    
    tools_system = ToolsSystem(rag_system, model_manager)
    
    # Test with valid arguments
    arguments = {
        "title": "Тестовый документ",
        "content": "Содержимое тестового документа",
        "format": "txt"
    }
    
    result = tools_system.execute_tool("create_document", arguments)
    
    assert result is not None
    assert "file_path" in result
    assert "format" in result
    assert result["format"] == "txt"

def test_execute_tool_financial_calculator():
    """Test executing the financial_calculator tool"""
    rag_system = MockRAGSystem()
    model_manager = MockModelManager()
    
    tools_system = ToolsSystem(rag_system, model_manager)
    
    # Test addition
    arguments = {
        "operation": "add",
        "values": [100, 200, 300]
    }
    
    result = tools_system.execute_tool("financial_calculator", arguments)
    
    assert result is not None
    assert "result" in result
    assert result["result"] == 600
    
    # Test multiplication
    arguments = {
        "operation": "multiply",
        "values": [2, 3, 4]
    }
    
    result = tools_system.execute_tool("financial_calculator", arguments)
    
    assert result is not None
    assert "result" in result
    assert result["result"] == 24
    
    # Test ROI calculation
    arguments = {
        "operation": "calculate_roi",
        "values": [1000, 5000]  # profit, investment
    }
    
    result = tools_system.execute_tool("financial_calculator", arguments)
    
    assert result is not None
    assert "result" in result
    assert result["result"] == 20.0  # (1000/5000)*100 = 20%

def test_execute_tool_extract_works_nlp():
    """Test executing the extract_works_nlp tool"""
    rag_system = MockRAGSystem()
    model_manager = MockModelManager()
    
    tools_system = ToolsSystem(rag_system, model_manager)
    
    # Test with sample text containing work descriptions
    arguments = {
        "text": "Работа по подготовке площадки. Задача по установке опалубки. Элемент конструкции фундамента.",
        "doc_type": "ppr"
    }
    
    result = tools_system.execute_tool("extract_works_nlp", arguments)
    
    assert result is not None
    assert "works" in result
    assert "type" in result
    assert result["type"] == "ppr"

def test_execute_tool_generate_mermaid_diagram():
    """Test executing the generate_mermaid_diagram tool"""
    rag_system = MockRAGSystem()
    model_manager = MockModelManager()
    
    tools_system = ToolsSystem(rag_system, model_manager)
    
    # Test with flow diagram data
    arguments = {
        "type": "flow",
        "data": {
            "nodes": [
                {"id": "A", "label": "Start"},
                {"id": "B", "label": "Process"},
                {"id": "C", "label": "End"}
            ],
            "edges": [
                {"from": "A", "to": "B", "label": "next"},
                {"from": "B", "to": "C", "label": "finish"}
            ]
        }
    }
    
    result = tools_system.execute_tool("generate_mermaid_diagram", arguments)
    
    assert result is not None
    assert "mermaid_code" in result
    assert "type" in result
    assert "graph TD" in result["mermaid_code"]

def test_execute_tool_create_charts():
    """Test executing chart creation tools"""
    rag_system = MockRAGSystem()
    model_manager = MockModelManager()
    
    tools_system = ToolsSystem(rag_system, model_manager)
    
    # Test Gantt chart creation
    arguments = {
        "tasks": [
            {"name": "Task 1", "start": "2023-01-01", "end": "2023-01-10", "duration": 10},
            {"name": "Task 2", "start": "2023-01-11", "end": "2023-01-20", "duration": 10}
        ],
        "title": "Project Schedule"
    }
    
    result = tools_system.execute_tool("create_gantt_chart", arguments)
    
    assert result is not None
    assert "chart_data" in result
    assert "title" in result
    assert result["title"] == "Project Schedule"
    
    # Test pie chart creation
    arguments = {
        "data": [
            {"name": "Category A", "value": 30},
            {"name": "Category B", "value": 70}
        ],
        "title": "Distribution Chart"
    }
    
    result = tools_system.execute_tool("create_pie_chart", arguments)
    
    assert result is not None
    assert "chart_data" in result
    assert len(result["chart_data"]) == 2

def test_invalid_tool_execution():
    """Test that executing an invalid tool raises an exception"""
    rag_system = MockRAGSystem()
    model_manager = MockModelManager()
    
    tools_system = ToolsSystem(rag_system, model_manager)
    
    # Test with invalid tool name
    arguments = {"query": "test"}
    
    with pytest.raises(ValueError, match="Неизвестный инструмент: invalid_tool"):
        tools_system.execute_tool("invalid_tool", arguments)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])