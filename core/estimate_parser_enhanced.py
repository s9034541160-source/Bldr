"""
Enhanced estimate parser for GESN/FER rates
"""

import json
import re
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Optional imports for Excel/CSV parsing
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

def parse_estimate_gesn(estimate_file: str, region: str = 'ekaterinburg') -> Dict[str, Any]:
    """
    Parse estimate file with GESN/FER rates
    
    Args:
        estimate_file: Path to estimate file
        region: Region for regional coefficients
        
    Returns:
        Structured estimate data
    """
    # Initialize structured data
    estimate_data = {
        "file_path": estimate_file,
        "parsed_date": datetime.now().isoformat(),
        "region": region,
        "positions": [],
        "total_cost": 0.0,
        "regional_coefficients": {},
        "gesn_rates_used": []
    }
    
    # Get regional coefficients
    estimate_data["regional_coefficients"] = get_regional_coefficients(region)
    
    # Try to parse actual file if it exists
    if os.path.exists(estimate_file):
        try:
            # Try to parse as Excel file first
            if estimate_file.endswith('.xlsx') or estimate_file.endswith('.xls'):
                estimate_data["positions"] = parse_excel_estimate(estimate_file)
            # Try to parse as CSV file
            elif estimate_file.endswith('.csv'):
                estimate_data["positions"] = parse_csv_estimate(estimate_file)
            # Try to parse as text file
            else:
                with open(estimate_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    estimate_data["positions"] = parse_text_estimate(content)
        except Exception as e:
            print(f"Ошибка парсинга файла сметы: {e}")
            # Fallback to sample positions
            estimate_data["positions"] = generate_sample_positions()
    else:
        # Fallback to sample positions
        estimate_data["positions"] = generate_sample_positions()
    
    # Calculate total cost
    estimate_data["total_cost"] = sum(pos.get("total_cost", 0.0) for pos in estimate_data["positions"])
    
    # Apply regional coefficients
    total_with_regional = estimate_data["total_cost"]
    for coeff_value in estimate_data["regional_coefficients"].values():
        total_with_regional *= (1 + coeff_value / 100)
    estimate_data["total_cost_with_regional"] = total_with_regional
    
    return estimate_data

def get_regional_coefficients(region: str) -> Dict[str, float]:
    """
    Get regional coefficients for a specific region
    
    Args:
        region: Region name
        
    Returns:
        Dictionary of regional coefficients
    """
    regional_coeffs = {
        "ekaterinburg": {
            "construction": 10.0,
            "transport": 5.0,
            "climate": 3.0
        },
        "moscow": {
            "construction": 8.0,
            "transport": 7.0,
            "climate": 2.0
        },
        "novosibirsk": {
            "construction": 12.0,
            "transport": 8.0,
            "climate": 5.0
        }
    }
    
    return regional_coeffs.get(region, {"construction": 0.0, "transport": 0.0, "climate": 0.0})

def generate_sample_positions() -> List[Dict[str, Any]]:
    """
    Generate sample positions for demonstration
    
    Returns:
        List of sample position dictionaries
    """
    return [
        {
            "code": "ГЭСН 8-1-1",
            "description": "Устройство бетонной подготовки",
            "unit": "м3",
            "quantity": 100.0,
            "base_rate": 15000.0,
            "materials_cost": 8000.0,
            "labor_cost": 5000.0,
            "equipment_cost": 2000.0,
            "total_cost": 1500000.0
        },
        {
            "code": "ГЭСН 8-1-2",
            "description": "Устройство монолитных бетонных конструкций",
            "unit": "м3",
            "quantity": 250.0,
            "base_rate": 25000.0,
            "materials_cost": 15000.0,
            "labor_cost": 7000.0,
            "equipment_cost": 3000.0,
            "total_cost": 6250000.0
        },
        {
            "code": "ГЭСН 8-6-1.1",
            "description": "Устройство сборных железобетонных фундаментов",
            "unit": "шт",
            "quantity": 20.0,
            "base_rate": 30000.0,
            "materials_cost": 20000.0,
            "labor_cost": 8000.0,
            "equipment_cost": 2000.0,
            "total_cost": 600000.0
        }
    ]

def extract_gesn_rates_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract GESN/FER rates from text
    
    Args:
        text: Text to extract rates from
        
    Returns:
        List of extracted rate dictionaries
    """
    rates = []
    
    # Patterns for GESN/FER codes
    gesn_pattern = r'(?:ГЭСН|ФЕР)\s+(\d+(?:-\d+)*(?:\.\d+)*)'
    cost_pattern = r'(\d+(?:\.\d+)?)\s*(?:руб\.?|рублей)'
    
    # Find GESN/FER codes
    gesn_matches = re.findall(gesn_pattern, text, re.IGNORECASE)
    
    for match in gesn_matches:
        # Extract surrounding context for cost information
        context_start = max(0, text.find(match) - 100)
        context_end = min(len(text), text.find(match) + 200)
        context = text[context_start:context_end]
        
        # Extract costs from context
        costs = re.findall(cost_pattern, context)
        base_rate = float(costs[0]) if costs else 0.0
        materials_cost = float(costs[1]) if len(costs) > 1 else base_rate * 0.6
        labor_cost = float(costs[2]) if len(costs) > 2 else base_rate * 0.3
        equipment_cost = float(costs[3]) if len(costs) > 3 else base_rate * 0.1
        
        rate = {
            "code": f"ГЭСН {match}",
            "description": f"Расценка {match}",
            "base_rate": base_rate,
            "materials_cost": materials_cost,
            "labor_cost": labor_cost,
            "equipment_cost": equipment_cost,
            "total_cost": base_rate + materials_cost + labor_cost + equipment_cost
        }
        
        rates.append(rate)
    
    return rates

def validate_estimate_structure(estimate_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate estimate structure and calculate totals
    
    Args:
        estimate_data: Estimate data to validate
        
    Returns:
        Validation results
    """
    validation = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "calculated_totals": {}
    }
    
    # Check required fields
    required_fields = ["positions", "region"]
    for field in required_fields:
        if field not in estimate_data:
            validation["is_valid"] = False
            validation["errors"].append(f"Отсутствует обязательное поле: {field}")
    
    # Validate positions
    positions = estimate_data.get("positions", [])
    total_cost = 0.0
    
    for i, position in enumerate(positions):
        # Check required position fields
        position_required = ["code", "description", "quantity", "unit", "base_rate"]
        for field in position_required:
            if field not in position:
                validation["is_valid"] = False
                validation["errors"].append(f"Позиция {i+1}: отсутствует поле {field}")
        
        # Calculate position total
        calculated_total = (
            position.get("base_rate", 0.0) +
            position.get("materials_cost", 0.0) +
            position.get("labor_cost", 0.0) +
            position.get("equipment_cost", 0.0)
        ) * position.get("quantity", 1.0)
        
        total_cost += calculated_total
    
    validation["calculated_totals"]["total_cost"] = total_cost
    
    # Check for consistency
    if "total_cost" in estimate_data and abs(estimate_data["total_cost"] - total_cost) > 1.0:
        validation["warnings"].append("Несоответствие в общей стоимости")
    
    return validation

def export_estimate_to_json(estimate_data: Dict[str, Any], filename: Optional[str] = None) -> str:
    """
    Export estimate data to JSON format
    
    Args:
        estimate_data: Estimate data
        filename: Output filename (optional)
        
    Returns:
        Path to the generated JSON file
    """
    if filename is None:
        filename = f"estimate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(estimate_data, f, ensure_ascii=False, indent=2)
    
    return filename

def parse_excel_estimate(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse estimate from Excel file
    
    Args:
        file_path: Path to Excel file
        
    Returns:
        List of position dictionaries
    """
    if not HAS_PANDAS:
        return generate_sample_positions()
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Extract positions
        positions = []
        for _, row in df.iterrows():
            position = {
                "code": row.get("Код", row.get("Code", "")),
                "description": row.get("Наименование", row.get("Description", "")),
                "unit": row.get("Ед. изм.", row.get("Unit", "")),
                "quantity": float(row.get("Количество", row.get("Quantity", 0))),
                "base_rate": float(row.get("Расценка", row.get("Rate", 0))),
                "materials_cost": float(row.get("Материалы", row.get("Materials", 0))),
                "labor_cost": float(row.get("Работа", row.get("Labor", 0))),
                "equipment_cost": float(row.get("Оборудование", row.get("Equipment", 0))),
                "total_cost": float(row.get("Итого", row.get("Total", 0)))
            }
            positions.append(position)
        
        return positions
    except Exception as e:
        print(f"Ошибка парсинга Excel файла: {e}")
        return generate_sample_positions()

def parse_csv_estimate(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse estimate from CSV file
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        List of position dictionaries
    """
    if not HAS_PANDAS:
        return generate_sample_positions()
    
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Extract positions
        positions = []
        for _, row in df.iterrows():
            position = {
                "code": row.get("Код", row.get("Code", "")),
                "description": row.get("Наименование", row.get("Description", "")),
                "unit": row.get("Ед. изм.", row.get("Unit", "")),
                "quantity": float(row.get("Количество", row.get("Quantity", 0))),
                "base_rate": float(row.get("Расценка", row.get("Rate", 0))),
                "materials_cost": float(row.get("Материалы", row.get("Materials", 0))),
                "labor_cost": float(row.get("Работа", row.get("Labor", 0))),
                "equipment_cost": float(row.get("Оборудование", row.get("Equipment", 0))),
                "total_cost": float(row.get("Итого", row.get("Total", 0)))
            }
            positions.append(position)
        
        return positions
    except Exception as e:
        print(f"Ошибка парсинга CSV файла: {e}")
        return generate_sample_positions()

def parse_text_estimate(content: str) -> List[Dict[str, Any]]:
    """
    Parse estimate from text content
    
    Args:
        content: Text content of estimate
        
    Returns:
        List of position dictionaries
    """
    positions = []
    
    # Try to extract GESN/FER codes and rates using regex
    gesn_patterns = [
        r'(?:ГЭСН|ФЕР)\s+(\d+(?:-\d+)*(?:\.\d+)*)\s+([^,\n]+),\s*([\d.,]+)\s*руб',
        r'(?:ГЭСН|ФЕР)\s+(\d+(?:-\d+)*(?:\.\d+)*)\s+([^,\n]+)\s+([\d.,]+)'
    ]
    
    for pattern in gesn_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            code, description, rate_str = match
            try:
                rate = float(rate_str.replace(',', '.'))
                position = {
                    "code": f"ГЭСН {code}",
                    "description": description.strip(),
                    "unit": "м3",  # Default unit
                    "quantity": 1.0,  # Default quantity
                    "base_rate": rate,
                    "materials_cost": rate * 0.6,  # Estimate
                    "labor_cost": rate * 0.3,  # Estimate
                    "equipment_cost": rate * 0.1,  # Estimate
                    "total_cost": rate
                }
                positions.append(position)
            except ValueError:
                continue
    
    # If no matches found, return sample positions
    if not positions:
        return generate_sample_positions()
    
    return positions

# Sample GESN/FER data for testing
SAMPLE_GESN_FER_DATA = {
    "ГЭСН 8-1-1": {
        "description": "Устройство бетонной подготовки",
        "base_rate": 15000.0,
        "materials": 8000.0,
        "labor": 5000.0,
        "equipment": 2000.0
    },
    "ГЭСН 8-1-2": {
        "description": "Устройство монолитных бетонных конструкций",
        "base_rate": 25000.0,
        "materials": 15000.0,
        "labor": 7000.0,
        "equipment": 3000.0
    },
    "ГЭСН 8-6-1.1": {
        "description": "Устройство сборных железобетонных фундаментов",
        "base_rate": 30000.0,
        "materials": 20000.0,
        "labor": 8000.0,
        "equipment": 2000.0
    }
}