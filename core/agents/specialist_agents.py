"""Specialist agents for SuperBuilder multi-agent system"""

from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
import json

# Import the new roles agents
from core.agents.roles_agents import RoleAgent, RolesAgentsManager

class SpecialistAgent:
    """Base class for specialist agents - now using the new role-based system"""
    
    def __init__(self, role: str, lm_studio_url: str = "http://localhost:1234/v1", tools_system=None):
        """
        Initialize specialist agent.
        
        Args:
            role: Role name for the agent
            lm_studio_url: URL for LM Studio API
            tools_system: Optional ToolsSystem instance for real tool execution
        """
        self.role = role
        self.lm_studio_url = lm_studio_url
        
        # Use the new roles agents manager
        self.roles_manager = RolesAgentsManager(lm_studio_url, tools_system)
    
    def execute_task(self, task_input: str, tool_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute task with the specialist agent.
        
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
            
            # Execute task using the new role-based system
            agent = self.roles_manager.get_agent(self.role)
            result = agent.execute_task(context, tool_results)
            return result
        except Exception as e:
            return {
                "role": self.role,
                "task_input": task_input,
                "error": str(e),
                "status": "error"
            }

class SpecialistAgentsManager:
    """Manager for all specialist agents - now using the new role-based system"""
    
    def __init__(self, lm_studio_url: str = "http://localhost:1234/v1", tools_system=None):
        """
        Initialize specialist agents manager.
        
        Args:
            lm_studio_url: URL for LM Studio API
            tools_system: Optional ToolsSystem instance for real tool execution
        """
        self.lm_studio_url = lm_studio_url
        self.tools_system = tools_system
        self.roles_manager = RolesAgentsManager(lm_studio_url, tools_system)
        self.agents = {}
    
    def get_agent(self, role: str) -> SpecialistAgent:
        """
        Get or create specialist agent for role.
        
        Args:
            role: Role name
            
        Returns:
            Specialist agent instance
        """
        if role not in self.agents:
            self.agents[role] = SpecialistAgent(role, self.lm_studio_url, self.tools_system)
        return self.agents[role]
    
    def execute_plan(self, plan: Dict[str, Any], tools_system: Any) -> List[Dict[str, Any]]:
        """
        Execute plan with specialist agents.
        
        Args:
            plan: Execution plan
            tools_system: Tools system for executing tools
            
        Returns:
            List of execution results
        """
        results = []
        
        # Execute tools first through Master Tools System
        tool_results = []
        if "tasks" in plan:
            for task in plan["tasks"]:
                if "tool" in task:
                    try:
                        tool_name = task["tool"]
                        tool_input = task.get("input", task.get("arguments", {}))
                        
                        # Execute tool through Master Tools System adapter
                        if hasattr(tools_system, 'execute_tool'):
                            tool_result = tools_system.execute_tool(tool_name, **tool_input)
                        elif hasattr(tools_system, tool_name):
                            method = getattr(tools_system, tool_name)
                            tool_result = method(**tool_input)
                        else:
                            tool_result = {"error": f"Tool {tool_name} not found in tools system"}
                        
                        # Format result for consistency
                        if isinstance(tool_result, dict):
                            tool_result["tool"] = tool_name
                        else:
                            tool_result = {
                                "tool": tool_name,
                                "data": tool_result,
                                "status": "success"
                            }
                        
                        tool_results.append(tool_result)
                        
                    except Exception as e:
                        tool_results.append({
                            "tool": task["tool"],
                            "error": str(e),
                            "status": "error"
                        })
        
        # Execute specialist tasks using the new role-based system
        if "tasks" in plan:
            for task in plan["tasks"]:
                if "agent" in task and task["agent"] != "coordinator":
                    try:
                        # Execute task using the new role-based system
                        agent = self.roles_manager.get_agent(task["agent"])
                        result = agent.execute_task(task.get("input", ""), tool_results)
                        results.append(result)
                    except Exception as e:
                        results.append({
                            "role": task["agent"],
                            "task_input": task.get("input", ""),
                            "error": str(e),
                            "status": "error"
                        })
        
        return results