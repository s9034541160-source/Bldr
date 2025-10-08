# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: parse_estimate_unified
# Основной источник: C:\Bldr\core\unified_estimate_parser.py
# Дубликаты (для справки):
#================================================================================
def parse_estimate_unified(input_data: Union[str, List[str], Dict[str, Any]], **kwargs) -> Dict[str, Any]:
    """
    Unified estimate parsing function - replaces all individual parsers
    
    This function consolidates:
    - parse_gesn_estimate
    - parse_excel_estimate  
    - parse_csv_estimate
    - parse_text_estimate
    - parse_batch_estimates
    """
    return unified_parser.parse_estimate_unified(input_data, **kwargs)