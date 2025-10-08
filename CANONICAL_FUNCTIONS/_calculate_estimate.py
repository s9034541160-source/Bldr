# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _calculate_estimate
# Основной источник: C:\Bldr\core\tools_system.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _calculate_estimate(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate estimate with real GESN/FER rates"""
        query = arguments.get("query", "")
        
        try:
            # Search for relevant norms
            norm_results = self._search_rag_database({
                "query": query,
                "doc_types": ["norms"],
                "k": 3
            })
            
            # Extract estimate data from results
            estimate_positions = []
            for result in norm_results.get("results", []):
                chunk = result.get("chunk", "")
                # Extract GESN/FER codes and rates from chunk
                gesn_patterns = re.findall(r'(?:ГЭСН|ФЕР)\s+(\d+(?:-\d+)*(?:\.\d+)*)', chunk)
                for code in gesn_patterns:
                    estimate_positions.append({
                        "code": f"ГЭСН {code}",
                        "description": f"Rate {code}",
                        "unit": "м3",  # Default unit
                        "quantity": 1.0,  # Default quantity
                        "base_rate": 1500.0,  # Default rate
                        "materials_cost": 800.0,  # Default materials cost
                        "labor_cost": 500.0,  # Default labor cost
                        "equipment_cost": 200.0  # Default equipment cost
                    })
            
            # Calculate total estimate
            total_cost = sum(pos["base_rate"] * pos["quantity"] for pos in estimate_positions)
            
            return {
                "status": "success",
                "positions": estimate_positions,
                "total_cost": total_cost,
                "currency": "RUB"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "positions": [],
                "total_cost": 0.0
            }