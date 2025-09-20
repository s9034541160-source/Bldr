"""
Unit tests for pro-features
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import pro-feature modules
from core.official_letters import generate_official_letter
from core.budget_auto import auto_budget, SAMPLE_GESN_RATES
from core.ppr_generator import generate_ppr, SAMPLE_PROJECT_DATA
from core.gpp_creator import create_gpp, SAMPLE_WORKS_SEQ
from core.estimate_parser_enhanced import parse_estimate_gesn

def test_official_letter_generation():
    """Test official letter generation"""
    template = "compliance_sp31"
    data = {
        "recipient": "ООО СтройПроект",
        "sender": "АО БЛДР",
        "subject": "Соответствие проектной документации СП 45.13330.2017",
        "compliance_details": [
            "Соответствие организации строительного контроля",
            "Соответствие требованиям безопасности труда",
            "Соответствие экологическим требованиям"
        ],
        "violations": []
    }
    
    file_path = generate_official_letter(template, data)
    assert file_path is not None
    assert isinstance(file_path, str)
    assert file_path.endswith('.docx')
    assert os.path.exists(file_path)
    
    # Clean up
    if os.path.exists(file_path):
        os.remove(file_path)

def test_auto_budget_generation():
    """Test automatic budget generation"""
    estimate_data = {
        "project_name": "Строительство административного здания",
        "positions": [
            {
                "code": "ГЭСН 8-1-1",
                "name": "Устройство бетонной подготовки",
                "unit": "м3",
                "quantity": 100.0,
                "unit_cost": 15000.0,
                "description": "Бетонная подготовка под фундамент"
            },
            {
                "code": "ГЭСН 8-1-2",
                "name": "Устройство монолитных бетонных конструкций",
                "unit": "м3",
                "quantity": 200.0,
                "unit_cost": 25000.0,
                "description": "Монолитные бетонные конструкции фундамента"
            }
        ],
        "regional_coefficients": {
            "ekaterinburg": 10.0
        },
        "overheads_percentage": 15.0,
        "profit_percentage": 10.0
    }
    
    budget = auto_budget(estimate_data, SAMPLE_GESN_RATES)
    assert budget is not None
    assert isinstance(budget, dict)
    assert "total_cost" in budget
    assert budget["total_cost"] > 0
    assert len(budget["sections"]) > 0

def test_ppr_generation():
    """Test PPR generation"""
    project_data = {
        "project_name": "Строительство административного здания",
        "project_code": "ADM-2025-001",
        "location": "Екатеринбург",
        "client": "ООО СтройПроект"
    }
    
    # Create enough works to satisfy the >10 stages requirement
    works_seq = []
    work_names = [
        "Подготовительные работы",
        "Земляные работы", 
        "Фундаментные работы",
        "Каркасные работы",
        "Кровельные работы",
        "Отделочные работы",
        "Благоустройство",
        "Инженерные сети",
        "Электромонтажные работы",
        "Сантехнические работы",
        "Вентиляционные работы",
        "Пусконаладочные работы"
    ]
    
    for i, name in enumerate(work_names):
        work = {
            "name": name,
            "description": f"Описание работ: {name}",
            "duration": float(10 + i * 5),  # Varying durations
            "deps": [] if i == 0 else [work_names[i-1]],  # Sequential dependencies
            "resources": {
                "manpower": 5 + i,
                "equipment": [f"Оборудование {i+1}"]
            }
        }
        works_seq.append(work)
    
    ppr = generate_ppr(project_data, works_seq)
    assert ppr is not None
    assert isinstance(ppr, dict)
    assert "stages" in ppr
    assert len(ppr["stages"]) > 10  # As per requirement
    assert ppr["compliance_check"]["status"] in ["compliant", "warning"]

def test_gpp_creation():
    """Test GPP creation"""
    # Create enough works for a meaningful GPP
    works_seq = []
    work_names = [
        "Подготовка площадки",
        "Устройство фундамента", 
        "Возведение стен",
        "Монтаж перекрытий",
        "Устройство кровли",
        "Отделочные работы",
        "Благоустройство"
    ]
    
    for i, name in enumerate(work_names):
        work = {
            "name": name,
            "description": f"Описание работ: {name}",
            "duration": float(10 + i * 3),  # Varying durations
            "deps": [] if i == 0 else [work_names[i-1]],  # Sequential dependencies
            "resources": {
                "manpower": 5 + i,
                "equipment": [f"Оборудование {i+1}"]
            }
        }
        works_seq.append(work)
    
    gpp = create_gpp(works_seq)
    assert gpp is not None
    assert isinstance(gpp, dict)
    assert "tasks" in gpp
    assert "links" in gpp
    assert "critical_path" in gpp
    assert len(gpp["tasks"]) > 0
    assert len(gpp["links"]) >= 0

def test_estimate_parser_enhanced():
    """Test enhanced estimate parser"""
    # For testing purposes, we'll use a dummy file path
    estimate_file = "dummy_estimate.xlsx"
    region = "ekaterinburg"
    
    estimate_data = parse_estimate_gesn(estimate_file, region)
    assert estimate_data is not None
    assert isinstance(estimate_data, dict)
    assert "positions" in estimate_data
    assert "regional_coefficients" in estimate_data
    assert "total_cost" in estimate_data
    assert estimate_data["total_cost"] >= 0

if __name__ == "__main__":
    test_official_letter_generation()
    test_auto_budget_generation()
    test_ppr_generation()
    test_gpp_creation()
    test_estimate_parser_enhanced()
    print("🎉 All pro-features tests passed!")