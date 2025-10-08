# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: execute_tool
# Основной источник: C:\Bldr\core\tools_system.py
# Дубликаты (для справки):
#   - C:\Bldr\core\tools_adapter.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#   - C:\Bldr\core\meta_tools\celery_integration.py
#   - C:\Bldr\core\meta_tools\celery_integration.py
#   - C:\Bldr\core\meta_tools\celery_integration.py
#   - C:\Bldr\core\meta_tools\celery_integration.py
#   - C:\Bldr\core\meta_tools\meta_tools_system.py
#================================================================================
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool by name with flexible parameter passing.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments dictionary (legacy support)
            **kwargs: Flexible keyword arguments for the tool
            
        Returns:
            Standardized result of tool execution
        """
        start_time = datetime.now()
        
        try:
            # Merge arguments and kwargs, with kwargs taking precedence
            if arguments is None:
                arguments = {}
            
            # Combine arguments dict with kwargs, filtering out None values
            final_args = {k: v for k, v in arguments.items() if v is not None}
            final_args.update({k: v for k, v in kwargs.items() if v is not None})
            
            # Validate parameters (existing validation)
            validate_tool_parameters(tool_name, final_args)
            
            # Execute tool
            if tool_name in self.tool_methods:
                result = self.executor.execute_with_retry(
                    self.tool_methods[tool_name], 
                    final_args, 
                    tool_name
                )
                
                # Standardize response format
                execution_time = (datetime.now() - start_time).total_seconds()
                return self._standardize_response(result, tool_name, execution_time, final_args)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._standardize_error_response(str(e), tool_name, execution_time, final_args)