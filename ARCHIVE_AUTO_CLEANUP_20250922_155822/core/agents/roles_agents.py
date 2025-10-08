"""Role-based agents using LangChain for SuperBuilder"""

import json
import os
import time
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate

# Import configuration
from core.config import MODELS_CONFIG, get_capabilities_prompt

# Import compressed conversation history
from core.agents.conversation_history_compressed import compressed_conversation_history

class RoleAgent:
    """LangChain-based role agent for SuperBuilder"""
    
    def __init__(self, role: str, lm_studio_url: str = "http://localhost:1234/v1", tools_system=None):
        """
        Initialize role agent with specific role and LLM.
        
        Args:
            role: Role name (e.g., 'chief_engineer', 'project_manager')
            lm_studio_url: URL for LM Studio API
            tools_system: Optional ToolsSystem instance for real tool execution
        """
        self.role = role
        self.tools_system = tools_system
        
        # Set environment variable for OpenAI API key (not actually needed for LM Studio)
        os.environ["OPENAI_API_KEY"] = "not-needed"
        
        # Initialize LLM for this role with configurable model
        model_name = MODELS_CONFIG.get(role, {}).get('model', "deepseek/deepseek-r1-0528-qwen3-8b")
        self.llm = ChatOpenAI(
            base_url=lm_studio_url,
            model=model_name,  # Configurable model per role
            temperature=0.1
        )
        
        # Get capabilities prompt for this role from config
        system_prompt = get_capabilities_prompt(role)
        self.system_prompt = system_prompt if system_prompt else f"You are the {role} agent for Bldr Empire v2."
        
        # Get tools for this role
        self.tools = self._get_role_tools()
        
        # Create agent with proper prompt template
        self.agent_executor = self._create_agent()
    
    def _execute_master_tool(self, tool_name: str, params_str: str) -> str:
        """Universal method to execute tools through Master Tools System."""
        try:
            # Parse parameters
            if isinstance(params_str, str):
                try:
                    params = json.loads(params_str)
                except json.JSONDecodeError:
                    params = {"input": params_str}
            else:
                params = params_str if isinstance(params_str, dict) else {}
            
            # If we have Master Tools System adapter, use it
            if self.tools_system:
                # Try direct method call first (for adapter methods)
                if hasattr(self.tools_system, tool_name):
                    method = getattr(self.tools_system, tool_name)
                    if callable(method):
                        result = method(**params)
                    else:
                        result = {"error": f"Method {tool_name} is not callable"}
                
                # Try execute_tool method (for Master Tools System)
                elif hasattr(self.tools_system, 'execute_tool'):
                    result = self.tools_system.execute_tool(tool_name, **params)
                
                else:
                    result = {"error": "Master Tools System not properly configured"}
                
                # Process result
                if isinstance(result, dict):
                    if result.get("status") == "success":
                        return json.dumps(result.get("data", result), ensure_ascii=False)
                    elif "error" in result:
                        return f"Error in {tool_name}: {result.get('error', 'Unknown error')}"
                    else:
                        return json.dumps(result, ensure_ascii=False)
                else:
                    return json.dumps(result, ensure_ascii=False) if result else "No result"
            
            else:
                # Fallback mock implementation
                return f"Mock result for {tool_name} with params: {params}"
                
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    # Tool implementations (these would connect to actual tools in the system)
    def _search_rag_database(self, query_params: str) -> str:
        """Search RAG database tool through Master Tools System."""
        try:
            # If we have a real tools system (Master Tools System adapter), use it
            if self.tools_system:
                params = json.loads(query_params) if isinstance(query_params, str) else query_params
                
                # Use Master Tools System adapter
                if hasattr(self.tools_system, 'search_rag_database'):
                    result = self.tools_system.search_rag_database(params.get('query', ''), **params)
                elif hasattr(self.tools_system, 'execute_tool'):
                    result = self.tools_system.execute_tool("search_rag_database", **params)
                else:
                    return f"Error: Master Tools System not properly configured"
                
                if isinstance(result, dict) and result.get("status") == "success":
                    return json.dumps(result.get("data", result), ensure_ascii=False)
                elif isinstance(result, dict) and "error" in result:
                    return f"Error in RAG search: {result.get('error', 'Unknown error')}"
                else:
                    return json.dumps(result, ensure_ascii=False) if result else "No results"
            else:
                # Fallback to mock implementation
                params = json.loads(query_params) if isinstance(query_params, str) else query_params
                return f"RAG search results for query: {params.get('query', '')}"
        except Exception as e:
            return f"Error in RAG search: {str(e)}"
    
    def _gen_docx(self, params: str) -> str:
        """Generate DOCX document tool through Master Tools System."""
        return self._execute_master_tool("create_document", params)
    
    def _vl_analyze_photo(self, params: str) -> str:
        """VL analyze photo tool through Master Tools System."""
        return self._execute_master_tool("analyze_image", params)
    
    def _gen_diagram(self, params: str) -> str:
        """Generate diagram tool through Master Tools System."""
        # Try both pie chart and bar chart based on params
        try:
            params_dict = json.loads(params) if isinstance(params, str) else params
            diagram_type = params_dict.get('type', 'pie')
            if diagram_type in ['pie', 'круговая']:
                return self._execute_master_tool("create_pie_chart", params)
            elif diagram_type in ['bar', 'столбчатая']:
                return self._execute_master_tool("create_bar_chart", params)
            else:
                return self._execute_master_tool("create_pie_chart", params)  # Default
        except:
            return self._execute_master_tool("create_pie_chart", params)
    
    def _calc_estimate(self, params: str) -> str:
        """Calculate estimate tool through Master Tools System."""
        return self._execute_master_tool("calculate_financial_metrics", params)
    
    def _gen_excel(self, params: str) -> str:
        """Generate Excel file tool through Master Tools System."""
        return self._execute_master_tool("create_document", params)
    
    def _gen_gantt(self, params: str) -> str:
        """Generate Gantt chart tool through Master Tools System."""
        return self._execute_master_tool("create_gantt_chart", params)
    
    def _gen_project_plan(self, params: str) -> str:
        """Generate project plan tool through Master Tools System."""
        try:
            return self._execute_master_tool("generate_ppr", params)
        except Exception as e:
            return f"Error generating project plan: {str(e)}"
    
    def _gen_safety_report(self, params: str) -> str:
        """Generate safety report tool."""
        try:
            # If we have a real tools system, use it
            if self.tools_system:
                params_dict = json.loads(params) if isinstance(params, str) else params
                # Execute the real gen_safety_report tool
                result = self.tools_system.execute_tool("gen_safety_report", params_dict)
                if result.get("status") == "success":
                    return json.dumps(result.get("data", {}), ensure_ascii=False)
                else:
                    return f"Error generating safety report: {result.get('error', 'Unknown error')}"
            else:
                # Fallback to mock implementation
                params_dict = json.loads(params) if isinstance(params, str) else params
                return f"Generated safety report: {params_dict.get('filename', 'safety.pdf')}"
        except Exception as e:
            return f"Error generating safety report: {str(e)}"
    
    def _gen_qc_report(self, params: str) -> str:
        """Generate QC report tool."""
        try:
            # If we have a real tools system, use it
            if self.tools_system:
                params_dict = json.loads(params) if isinstance(params, str) else params
                # Execute the real gen_qc_report tool
                result = self.tools_system.execute_tool("gen_qc_report", params_dict)
                if result.get("status") == "success":
                    return json.dumps(result.get("data", {}), ensure_ascii=False)
                else:
                    return f"Error generating QC report: {result.get('error', 'Unknown error')}"
            else:
                # Fallback to mock implementation
                params_dict = json.loads(params) if isinstance(params, str) else params
                return f"Generated QC report: {params_dict.get('filename', 'qc.pdf')}"
        except Exception as e:
            return f"Error generating QC report: {str(e)}"
    
    def _gen_checklist(self, params: str) -> str:
        """Generate checklist tool."""
        try:
            # If we have a real tools system, use it
            if self.tools_system:
                params_dict = json.loads(params) if isinstance(params, str) else params
                # Execute the real gen_checklist tool
                result = self.tools_system.execute_tool("gen_checklist", params_dict)
                if result.get("status") == "success":
                    return json.dumps(result.get("data", {}), ensure_ascii=False)
                else:
                    return f"Error generating checklist: {result.get('error', 'Unknown error')}"
            else:
                # Fallback to mock implementation
                params_dict = json.loads(params) if isinstance(params, str) else params
                return f"Generated checklist: {params_dict.get('filename', 'checklist.pdf')}"
        except Exception as e:
            return f"Error generating checklist: {str(e)}"
    
    def _bim_code_gen(self, params: str) -> str:
        """Generate BIM code tool."""
        try:
            # If we have a real tools system, use it
            if self.tools_system:
                params_dict = json.loads(params) if isinstance(params, str) else params
                # Execute the real bim_code_gen tool
                result = self.tools_system.execute_tool("bim_code_gen", params_dict)
                if result.get("status") == "success":
                    return json.dumps(result.get("data", {}), ensure_ascii=False)
                else:
                    return f"Error generating BIM code: {result.get('error', 'Unknown error')}"
            else:
                # Fallback to mock implementation
                params_dict = json.loads(params) if isinstance(params, str) else params
                return f"Generated BIM code for task: {params_dict.get('task', 'unknown')}"
        except Exception as e:
            return f"Error generating BIM code: {str(e)}"
    
    def _gen_script(self, params: str) -> str:
        """Generate script tool."""
        try:
            # If we have a real tools system, use it
            if self.tools_system:
                params_dict = json.loads(params) if isinstance(params, str) else params
                # Execute the real gen_script tool
                result = self.tools_system.execute_tool("gen_script", params_dict)
                if result.get("status") == "success":
                    return json.dumps(result.get("data", {}), ensure_ascii=False)
                else:
                    return f"Error generating script: {result.get('error', 'Unknown error')}"
            else:
                # Fallback to mock implementation
                params_dict = json.loads(params) if isinstance(params, str) else params
                return f"Generated script: {params_dict.get('filename', 'script.py')}"
        except Exception as e:
            return f"Error generating script: {str(e)}"
    
    def _direct_response(self, query_params: str) -> str:
        """
        Generate direct response for greeting and self-introduction queries.
        
        Args:
            query_params: Query parameters as JSON string or dict
            
        Returns:
            Direct response string
        """
        try:
            params = json.loads(query_params) if isinstance(query_params, str) else query_params
            query = params.get('query', '') if isinstance(params, dict) else str(params)
            
            query_lower = query.lower()
            if any(keyword in query_lower for keyword in ["привет", "здравствуй", "hello", "hi", "hey"]):
                return "Привет! Я ваш ассистент в строительной сфере. Рад помочь с вашими вопросами по строительству, сметам, проектам и нормативной документации."
            elif any(keyword in query_lower for keyword in ["расскажи о себе", "что ты умеешь", "кто ты", "what do you know", "what can you do", "tell me about yourself"]):
                return "Я - многофункциональный строительный ассистент, созданный для помощи в различных аспектах строительства. Я могу помочь с:\n\n1. Поиском и анализом строительных норм и правил (СП, ГОСТ, СНиП)\n2. Расчетом смет и бюджетов\n3. Созданием проектной документации\n4. Анализом изображений строительных объектов\n5. Генерацией официальных писем и документов\n6. Планированием строительных работ\n\nМоя цель - сделать вашу работу в строительной сфере более эффективной и точной."
            else:
                return f"Я получил ваш запрос: '{query}'. Я готов помочь с этим вопросом."
        except Exception as e:
            return f"Error in direct response: {str(e)}"
    
    def _get_role_tools(self) -> List[Tool]:
        """Get tools available for this specific role."""
        # Map roles to their available tools
        role_tool_mapping = {
            "coordinator": [
                Tool(
                    name="search_rag_database",
                    func=self._search_rag_database,
                    description="Search in clean_base (Nomic embed). Params: query, n_results, min_relevance, doc_types, etc."
                ),
                Tool(
                    name="gen_docx",
                    func=self._gen_docx,
                    description="Generate reports/letters (docx/PDF). Params: content, filename, format."
                ),
                Tool(
                    name="direct_response",
                    func=self._direct_response,
                    description="Generate direct response for greeting and self-introduction queries. Params: query."
                )
            ],
            "chief_engineer": [
                Tool(
                    name="search_rag_database",
                    func=self._search_rag_database,
                    description="Search in clean_base (Nomic embed). Params: query, n_results, min_relevance, doc_types, etc."
                ),
                Tool(
                    name="vl_analyze_photo",
                    func=self._vl_analyze_photo,
                    description="Analyze images/plans. Params: image_path, query."
                ),
                Tool(
                    name="gen_diagram",
                    func=self._gen_diagram,
                    description="Generate diagrams/PDF from VL. Params: content, type."
                )
            ],
            "structural_geotech_engineer": [
                Tool(
                    name="search_rag_database",
                    func=self._search_rag_database,
                    description="Search in clean_base (Nomic embed). Params: query, n_results, min_relevance, doc_types, etc."
                ),
                Tool(
                    name="calc_estimate",
                    func=self._calc_estimate,
                    description="Pandas GESN/FER calc. Params: rate_code, region, quantity."
                ),
                Tool(
                    name="gen_excel",
                    func=self._gen_excel,
                    description="Generate calcs/CSV. Params: data, filename."
                )
            ],
            "project_manager": [
                Tool(
                    name="search_rag_database",
                    func=self._search_rag_database,
                    description="Search in clean_base (Nomic embed). Params: query, n_results, min_relevance, doc_types, etc."
                ),
                Tool(
                    name="gen_gantt",
                    func=self._gen_gantt,
                    description="Generate project schedules. Params: tasks, timeline."
                ),
                Tool(
                    name="gen_project_plan",
                    func=self._gen_project_plan,
                    description="Generate PDF project plans. Params: content, filename."
                )
            ],
            "construction_safety": [
                Tool(
                    name="search_rag_database",
                    func=self._search_rag_database,
                    description="Search in clean_base (Nomic embed). Params: query, n_results, min_relevance, doc_types, etc."
                ),
                Tool(
                    name="vl_analyze_photo",
                    func=self._vl_analyze_photo,
                    description="Analyze safety images. Params: image_path, query."
                ),
                Tool(
                    name="gen_safety_report",
                    func=self._gen_safety_report,
                    description="Generate safety reports. Params: content, filename."
                )
            ],
            "qc_compliance": [
                Tool(
                    name="search_rag_database",
                    func=self._search_rag_database,
                    description="Search in clean_base (Nomic embed). Params: query, n_results, min_relevance, doc_types, etc."
                ),
                Tool(
                    name="gen_qc_report",
                    func=self._gen_qc_report,
                    description="Generate QC reports. Params: content, filename."
                ),
                Tool(
                    name="gen_checklist",
                    func=self._gen_checklist,
                    description="Generate inspection checklists. Params: items, filename."
                )
            ],
            "analyst": [
                Tool(
                    name="search_rag_database",
                    func=self._search_rag_database,
                    description="Search in clean_base (Nomic embed). Params: query, n_results, min_relevance, doc_types, etc."
                ),
                Tool(
                    name="calc_estimate",
                    func=self._calc_estimate,
                    description="Pandas GESN/FER calc. Params: rate_code, region, quantity."
                ),
                Tool(
                    name="gen_excel",
                    func=self._gen_excel,
                    description="Generate budgets/CSV. Params: data, filename."
                )
            ],
            "tech_coder": [
                Tool(
                    name="search_rag_database",
                    func=self._search_rag_database,
                    description="Search in clean_base (Nomic embed). Params: query, n_results, min_relevance, doc_types, etc."
                ),
                Tool(
                    name="bim_code_gen",
                    func=self._bim_code_gen,
                    description="Generate Python scripts. Params: task, requirements."
                ),
                Tool(
                    name="gen_script",
                    func=self._gen_script,
                    description="Generate automation scripts. Params: code, filename."
                )
            ]
        }
        
        return role_tool_mapping.get(self.role, [])
    
    def _create_agent(self) -> AgentExecutor:
        """Create LangChain agent with proper prompt template."""
        # Create prompt template for the agent
        prompt_template = """{system_prompt}

Available tools:
{tools}

Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate.from_template(prompt_template).partial(
            system_prompt=self.system_prompt
        )

        # Create agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        return AgentExecutor(
            agent=agent,  # type: ignore
            tools=self.tools,
            verbose=False,  # Turn off verbose for speed
            handle_parsing_errors=True,
            max_iterations=3,  # Reduced from 5 to 3
            max_execution_time=300.0  # Reduced from 3h to 5min (300 seconds)
        )
    
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

class RolesAgentsManager:
    """Manager for all role agents"""
    
    def __init__(self, lm_studio_url: str = "http://localhost:1234/v1", tools_system=None):
        """
        Initialize roles agents manager.
        
        Args:
            lm_studio_url: URL for LM Studio API
            tools_system: Optional ToolsSystem instance for real tool execution
        """
        self.lm_studio_url = lm_studio_url
        self.tools_system = tools_system
        self.agents = {}
    
    def get_agent(self, role: str) -> RoleAgent:
        """
        Get or create role agent for role.
        
        Args:
            role: Role name
            
        Returns:
            Role agent instance
        """
        if role not in self.agents:
            self.agents[role] = RoleAgent(role, self.lm_studio_url, self.tools_system)
        return self.agents[role]
    
    def execute_task(self, role: str, task_input: str, tool_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute task with role agent.
        
        Args:
            role: Role name
            task_input: Task description
            tool_results: Results from previous tool executions
            
        Returns:
            Dictionary with task execution results
        """
        try:
            agent = self.get_agent(role)
            return agent.execute_task(task_input, tool_results)
        except Exception as e:
            return {
                "role": role,
                "task_input": task_input,
                "error": str(e),
                "status": "error"
            }