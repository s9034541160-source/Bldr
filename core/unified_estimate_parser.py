"""
Unified estimate parser - consolidates all estimate parsing functionality
"""

import os
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging

# Import existing parsers
from core.estimate_parser_enhanced import (
    parse_estimate_gesn, 
    parse_excel_estimate,
    parse_csv_estimate, 
    parse_text_estimate,
    get_regional_coefficients
)

logger = logging.getLogger(__name__)

class UnifiedEstimateParser:
    """
    Unified parser for all estimate formats (GESN, Excel, CSV, Text, Batch)
    Consolidates: parse_gesn_estimate, parse_excel_estimate, parse_csv_estimate, 
                 parse_text_estimate, parse_batch_estimates
    """
    
    def __init__(self):
        self.supported_formats = {
            '.xlsx': 'excel',
            '.xls': 'excel', 
            '.csv': 'csv',
            '.txt': 'text',
            '.pdf': 'text',  # Will extract text first
            '.docx': 'text'  # Will extract text first
        }
    
    def parse_estimate_unified(self, 
                             input_data: Union[str, List[str], Dict[str, Any]], 
                             **kwargs) -> Dict[str, Any]:
        """
        Unified estimate parsing method with auto-format detection
        
        Args:
            input_data: Can be:
                - str: file path or text content
                - List[str]: multiple files (batch processing)
                - Dict: structured data
            **kwargs: Additional parameters:
                - region: Regional coefficients
                - format_hint: Force specific format
                - batch_mode: Process multiple files
                
        Returns:
            Standardized estimate parsing result
        """
        try:
            # Handle different input types
            if isinstance(input_data, list):
                return self._parse_batch(input_data, **kwargs)
            elif isinstance(input_data, dict):
                return self._parse_structured_data(input_data, **kwargs)
            elif isinstance(input_data, str):
                return self._parse_single_input(input_data, **kwargs)
            else:
                raise ValueError(f"Unsupported input type: {type(input_data)}")
                
        except Exception as e:
            logger.error(f"Error in unified estimate parsing: {e}")
            return {
                "status": "error",
                "error": str(e),
                "positions": [],
                "total_cost": 0.0,
                "metadata": {"parser": "unified", "input_type": type(input_data).__name__}
            }
    
    def _parse_single_input(self, input_str: str, **kwargs) -> Dict[str, Any]:
        """Parse single input (file or text)"""
        region = kwargs.get("region", "ekaterinburg")
        format_hint = kwargs.get("format_hint")
        
        # Check if it's a file path
        if os.path.exists(input_str):
            return self._parse_file(input_str, region, format_hint)
        else:
            # Treat as text content
            return self._parse_text_content(input_str, region)
    
    def _parse_file(self, file_path: str, region: str, format_hint: Optional[str] = None) -> Dict[str, Any]:
        """Parse estimate from file with auto-format detection"""
        file_path = Path(file_path)
        
        # Determine format
        if format_hint:
            format_type = format_hint
        else:
            format_type = self.supported_formats.get(file_path.suffix.lower(), 'text')
        
        logger.info(f"Parsing {file_path} as {format_type} format")
        
        try:
            # Route to appropriate parser
            if format_type == 'excel':
                result = parse_excel_estimate(str(file_path))
            elif format_type == 'csv':
                result = parse_csv_estimate(str(file_path))
            elif format_type == 'text':
                # Read file content first
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                result = parse_text_estimate(content)
            else:
                # Fallback to GESN parser
                result = parse_estimate_gesn(str(file_path), region)
            
            # Standardize result format
            return self._standardize_result(result, {
                "source_file": str(file_path),
                "format": format_type,
                "region": region,
                "parser": "unified"
            })
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return {
                "status": "error",
                "error": f"Failed to parse {file_path}: {str(e)}",
                "positions": [],
                "total_cost": 0.0,
                "metadata": {
                    "source_file": str(file_path),
                    "format": format_type,
                    "parser": "unified"
                }
            }
    
    def _parse_text_content(self, content: str, region: str) -> Dict[str, Any]:
        """Parse estimate from text content"""
        try:
            result = parse_text_estimate(content)
            return self._standardize_result(result, {
                "source": "text_content",
                "region": region,
                "parser": "unified"
            })
        except Exception as e:
            logger.error(f"Error parsing text content: {e}")
            return {
                "status": "error", 
                "error": f"Failed to parse text: {str(e)}",
                "positions": [],
                "total_cost": 0.0,
                "metadata": {"source": "text_content", "parser": "unified"}
            }
    
    def _parse_structured_data(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Parse structured estimate data"""
        try:
            # Extract positions from structured data
            positions = data.get("positions", [])
            region = kwargs.get("region", data.get("region", "ekaterinburg"))
            
            # Apply regional coefficients if needed
            regional_coeffs = get_regional_coefficients(region)
            
            total_cost = 0.0
            processed_positions = []
            
            for pos in positions:
                if isinstance(pos, dict):
                    cost = pos.get("cost", 0.0)
                    quantity = pos.get("quantity", 1.0)
                    
                    # Apply regional coefficients
                    adjusted_cost = cost * (1 + regional_coeffs.get("construction", 0.0))
                    total_cost += adjusted_cost * quantity
                    
                    processed_positions.append({
                        **pos,
                        "adjusted_cost": adjusted_cost,
                        "total": adjusted_cost * quantity
                    })
            
            return {
                "status": "success",
                "positions": processed_positions,
                "total_cost": total_cost,
                "regional_coefficients": regional_coeffs,
                "metadata": {
                    "source": "structured_data",
                    "region": region,
                    "parser": "unified"
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing structured data: {e}")
            return {
                "status": "error",
                "error": f"Failed to parse structured data: {str(e)}",
                "positions": [],
                "total_cost": 0.0,
                "metadata": {"source": "structured_data", "parser": "unified"}
            }
    
    def _parse_batch(self, file_list: List[str], **kwargs) -> Dict[str, Any]:
        """Parse multiple estimate files (batch processing)"""
        results = []
        total_files = len(file_list)
        successful = 0
        failed = 0
        
        logger.info(f"Starting batch processing of {total_files} files")
        
        for i, file_path in enumerate(file_list):
            try:
                result = self._parse_file(file_path, kwargs.get("region", "ekaterinburg"))
                if result["status"] == "success":
                    successful += 1
                else:
                    failed += 1
                results.append(result)
                
                # Log progress
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{total_files} files")
                    
            except Exception as e:
                failed += 1
                results.append({
                    "status": "error",
                    "error": str(e),
                    "source_file": file_path,
                    "positions": [],
                    "total_cost": 0.0
                })
        
        # Aggregate results
        all_positions = []
        total_cost = 0.0
        
        for result in results:
            if result["status"] == "success":
                all_positions.extend(result.get("positions", []))
                total_cost += result.get("total_cost", 0.0)
        
        return {
            "status": "success",
            "batch_results": results,
            "summary": {
                "total_files": total_files,
                "successful": successful,
                "failed": failed,
                "success_rate": successful / total_files if total_files > 0 else 0
            },
            "aggregated": {
                "positions": all_positions,
                "total_cost": total_cost,
                "position_count": len(all_positions)
            },
            "metadata": {
                "parser": "unified_batch",
                "region": kwargs.get("region", "ekaterinburg")
            }
        }
    
    def _standardize_result(self, result: Any, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize result format from different parsers"""
        if isinstance(result, dict):
            # Already in dict format
            standardized = result.copy()
        elif isinstance(result, list):
            # List of positions
            standardized = {
                "status": "success",
                "positions": result,
                "total_cost": sum(pos.get("cost", 0) * pos.get("quantity", 1) for pos in result if isinstance(pos, dict))
            }
        else:
            # Other format
            standardized = {
                "status": "success",
                "data": result,
                "positions": [],
                "total_cost": 0.0
            }
        
        # Ensure required fields
        if "status" not in standardized:
            standardized["status"] = "success"
        if "positions" not in standardized:
            standardized["positions"] = []
        if "total_cost" not in standardized:
            standardized["total_cost"] = 0.0
        
        # Add metadata
        standardized["metadata"] = {**standardized.get("metadata", {}), **metadata}
        
        return standardized

# Global instance
unified_parser = UnifiedEstimateParser()

# Unified API functions

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

# Backward compatibility functions (delegate to unified parser)

def parse_gesn_estimate_unified(estimate_file: str, region: str = 'ekaterinburg') -> Dict[str, Any]:
    """Backward compatible GESN parser"""
    return parse_estimate_unified(estimate_file, region=region, format_hint='gesn')


def parse_excel_estimate_unified(file_path: str) -> Dict[str, Any]:
    """Backward compatible Excel parser"""
    return parse_estimate_unified(file_path, format_hint='excel')


def parse_csv_estimate_unified(file_path: str) -> Dict[str, Any]:
    """Backward compatible CSV parser"""
    return parse_estimate_unified(file_path, format_hint='csv')


def parse_text_estimate_unified(content: str) -> Dict[str, Any]:
    """Backward compatible text parser"""
    return parse_estimate_unified(content)


def parse_batch_estimates_unified(file_list: List[str], region: str = 'ekaterinburg') -> Dict[str, Any]:
    """Backward compatible batch parser"""
    return parse_estimate_unified(file_list, region=region, batch_mode=True)
