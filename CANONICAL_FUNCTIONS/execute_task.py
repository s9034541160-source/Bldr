# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: execute_task
# Основной источник: C:\Bldr\core\agents\roles_agents.py
# Дубликаты (для справки):
#   - C:\Bldr\core\agents\specialist_agents.py
#================================================================================
    def execute_task(self, task_input: str, tool_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute task with the role agent.
        
        Args:
            task_input: Task description
            tool_results: Results from previous tool executions
            
        Returns:
            Dictionary with task execution results
        """
        try:
            # Prepare context with tool results
            context = f"Task: {task_input}\n\n"
            if tool_results:
                context += "Previous tool results:\n"
                for result in tool_results:
                    if result.get("status") == "success":
                        context += f"- {result.get('tool', 'Tool')}: {result.get('result', 'No result')}\n"
                    else:
                        context += f"- {result.get('tool', 'Tool')}: ERROR - {result.get('error', 'Unknown error')}\n"
            
            # Execute task using the agent
            result = self.agent_executor.invoke({"input": context})
            output = result["output"]
            
            return {
                "role": self.role,
                "task_input": task_input,
                "output": output,
                "status": "success"
            }
        except Exception as e:
            return {
                "role": self.role,
                "task_input": task_input,
                "error": str(e),
                "status": "error"
            }