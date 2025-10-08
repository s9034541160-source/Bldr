"""Multi-agent coordinator using LangChain for SuperBuilder"""

import json
import os
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field

# Import configuration and model manager
from core.config import MODELS_CONFIG, get_capabilities_prompt

class Plan(BaseModel):
    """JSON schema for coordinator plan"""
    complexity: str = Field(description="Complexity level: low/medium/high")
    time_est: int = Field(description="Estimated time in minutes")
    roles: List[str] = Field(description="Roles involved in execution")
    tasks: List[Dict[str, Any]] = Field(description="List of tasks to execute")

class CoordinatorAgent:
    """LangChain-based coordinator agent for SuperBuilder"""
    
    def __init__(self, lm_studio_url: str = "http://localhost:1234/v1", tools_system=None):
        """
        Initialize coordinator agent with LLM and optional ToolsSystem.
        
        Args:
            lm_studio_url: URL for LM Studio API
            tools_system: Optional ToolsSystem instance for enhanced tool awareness
        """
        # Store tools system for enhanced tool awareness
        self.tools_system = tools_system
        
        # Store request context for file delivery
        self.request_context = None
        
        # Set environment variable for OpenAI API key (not actually needed for LM Studio)
        os.environ["OPENAI_API_KEY"] = "not-needed"
        
        # Initialize LLM for coordinator
        self.llm = ChatOpenAI(
            base_url=lm_studio_url,
            model="deepseek/deepseek-r1-0528-qwen3-8b",  # Default model
            temperature=0.1
        )
        
        # Get capabilities prompt for coordinator from config
        system_prompt = get_capabilities_prompt("coordinator")
        self.system_prompt = system_prompt if system_prompt else "You are the coordinator agent for Bldr Empire v2."
        
        # Define tools for coordinator
        self.tools = [
            Tool(
                name="plan_analysis",
                func=self._analyze_and_plan,
                description="Analyze user query and generate execution plan"
            )
        ]
        
        # Create agent with proper prompt template
        self.agent_executor = self._create_agent()
    
    def _analyze_and_plan(self, query: str) -> str:
        """
        Analyze query and generate execution plan.
        
        Args:
            query: User query to analyze
            
        Returns:
            JSON string with plan
        """
        # Create prompt for plan generation with proper system context
        available_tools = self.get_available_tools_list()
        prompt = f"""Analyze the following user query and generate a detailed execution plan in JSON format:

Query: {query}

Generate a plan with the following structure:
{{
    "complexity": "low|medium|high",
    "time_est": estimated_time_in_minutes,
    "roles": ["role1", "role2", ...],
    "tasks": [
        {{
            "id": 1,
            "agent": "role_name",
            "input": "task_description",
            "tool": "tool_name"
        }},
        ...
    ]
}}

Available roles and their capabilities:
- coordinator: Strategic coordination, JSON plan generation, synthesis of responses. {', '.join(MODELS_CONFIG.get('coordinator', {}).get('responsibilities', []))}
- chief_engineer: Technical design, innovations, safety, regulations, VL photo/plans analysis. {', '.join(MODELS_CONFIG.get('chief_engineer', {}).get('responsibilities', []))}
- structural_geotech_engineer: Structural calculations, geotechnical analysis, FEM modeling. {', '.join(MODELS_CONFIG.get('structural_geotech_engineer', {}).get('responsibilities', []))}
- project_manager: Project planning, timeline management, resource allocation. {', '.join(MODELS_CONFIG.get('project_manager', {}).get('responsibilities', []))}
- construction_safety: Safety inspections, hazard identification, PPE recommendations. {', '.join(MODELS_CONFIG.get('construction_safety', {}).get('responsibilities', []))}
- qc_compliance: Quality inspections, compliance reporting, defect analysis. {', '.join(MODELS_CONFIG.get('qc_compliance', {}).get('responsibilities', []))}
- analyst: Estimates, budgets, cost management, financial forecasting. {', '.join(MODELS_CONFIG.get('analyst', {}).get('responsibilities', []))}
- tech_coder: BIM scripts, code generation, automation scripts. {', '.join(MODELS_CONFIG.get('tech_coder', {}).get('responsibilities', []))}

Available tools:
{available_tools}

Return ONLY valid JSON with the plan. No additional text."""

        try:
            print(f"Sending prompt to LLM: {prompt[:100]}...")
            # Get LLM response
            response = self.llm.invoke(prompt)
            print(f"Received response from LLM: {response}")
            if hasattr(response, 'content'):
                return str(response.content)
            else:
                return str(response)
        except Exception as e:
            print(f"Error in _analyze_and_plan: {e}")
            # Fallback plan if LLM fails
            return self._generate_fallback_plan(query)
    
    def _generate_fallback_plan(self, query: str) -> str:
        """
        Generate fallback plan when LLM fails.
        
        Args:
            query: User query
            
        Returns:
            JSON string with fallback plan
        """
        # Simple keyword-based plan generation as fallback
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ["стоимость", "смета", "расчет", "финанс", "бюджет"]):
            plan = {
                "complexity": "medium",
                "time_est": 2,
                "roles": ["analyst", "chief_engineer"],
                "tasks": [
                    {
                        "id": 1,
                        "agent": "analyst",
                        "input": f"Search for estimates related to: {query}",
                        "tool": "search_rag_database"
                    },
                    {
                        "id": 2,
                        "agent": "analyst",
                        "input": f"Calculate estimate for: {query}",
                        "tool": "calc_estimate"
                    }
                ]
            }
        elif any(keyword in query_lower for keyword in ["норма", "сп ", "гост", "снип", "фз", "пункт"]):
            plan = {
                "complexity": "medium",
                "time_est": 2,
                "roles": ["chief_engineer"],
                "tasks": [
                    {
                        "id": 1,
                        "agent": "chief_engineer",
                        "input": f"Search for norms related to: {query}",
                        "tool": "search_rag_database"
                    },
                    {
                        "id": 2,
                        "agent": "chief_engineer",
                        "input": f"Check normative compliance for: {query}",
                        "tool": "search_rag_database"
                    }
                ]
            }
        elif any(keyword in query_lower for keyword in ["проект", "ппр", "технологическая карта", "работы", "график"]):
            plan = {
                "complexity": "high",
                "time_est": 5,
                "roles": ["project_manager", "construction_worker"],
                "tasks": [
                    {
                        "id": 1,
                        "agent": "project_manager",
                        "input": f"Search for project documents related to: {query}",
                        "tool": "search_rag_database"
                    },
                    {
                        "id": 2,
                        "agent": "project_manager",
                        "input": f"Extract work sequences for: {query}",
                        "tool": "search_rag_database"
                    },
                    {
                        "id": 3,
                        "agent": "project_manager",
                        "input": f"Create Gantt chart for: {query}",
                        "tool": "gen_docx"
                    }
                ]
            }
        elif any(keyword in query_lower for keyword in ["письмо", "официальное", "деловое"]):
            plan = {
                "complexity": "low",
                "time_est": 1,
                "roles": ["chief_engineer"],
                "tasks": [
                    {
                        "id": 1,
                        "agent": "chief_engineer",
                        "input": f"Generate official letter for: {query}",
                        "tool": "gen_docx"
                    }
                ]
            }
        elif any(keyword in query_lower for keyword in ["фото", "изображение", "план", "site"]):
            plan = {
                "complexity": "medium",
                "time_est": 3,
                "roles": ["chief_engineer"],
                "tasks": [
                    {
                        "id": 1,
                        "agent": "chief_engineer",
                        "input": f"Analyze image for: {query}",
                        "tool": "vl_analyze_photo"
                    }
                ]
            }
        else:
            plan = {
                "complexity": "low",
                "time_est": 1,
                "roles": ["coordinator"],
                "tasks": [
                    {
                        "id": 1,
                        "agent": "coordinator",
                        "input": f"Search knowledge base for: {query}",
                        "tool": "search_rag_database"
                    }
                ]
            }
        
        import json
        return json.dumps(plan, ensure_ascii=False)
    
    def set_request_context(self, context):
        """
        Set the request context for file delivery.
        
        Args:
            context: Dictionary containing request context (channel, user_id, etc.)
        """
        self.request_context = context
    
    def clear_request_context(self):
        """Clear the request context."""
        self.request_context = None
    
    def deliver_file(self, file_path: str, description: str = ""):
        """
        Deliver a generated file to the user through the same channel where the request originated.
        
        Args:
            file_path: Path to the file to be delivered
            description: Optional description of the file
            
        Returns:
            Success message or error
        """
        if not self.request_context:
            return "❌ No request context available for file delivery"
        
        try:
            channel = self.request_context.get("channel", "unknown")
            
            if channel == "telegram":
                return self._deliver_file_to_telegram(file_path, description)
            elif channel == "ai_shell":
                return self._deliver_file_to_ai_shell(file_path, description)
            else:
                return f"❌ Unsupported delivery channel: {channel}"
        except Exception as e:
            return f"❌ Error delivering file: {str(e)}"
    
    def _deliver_file_to_telegram(self, file_path: str, description: str = ""):
        """
        Deliver a file to Telegram user.
        
        Args:
            file_path: Path to the file to be delivered
            description: Optional description of the file
            
        Returns:
            Success message
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return f"❌ File not found: {file_path}"
            
            # Get the chat_id from the request context
            if self.request_context and 'chat_id' in self.request_context:
                chat_id = self.request_context['chat_id']
                
                # Import the Telegram bot module to send the file
                import sys
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
                from integrations.telegram_bot import send_file_to_user
                
                # Send the file to the user
                success = send_file_to_user(chat_id, file_path, description)
                if success:
                    return f"✅ Файл успешно отправлен в Telegram (chat_id: {chat_id}): {file_path}"
                else:
                    return f"❌ Ошибка отправки файла в Telegram: {file_path}"
            else:
                return f"❌ Не удалось отправить файл в Telegram: отсутствует контекст чата"
        except Exception as e:
            return f"❌ Ошибка отправки файла в Telegram: {str(e)}"

    def _deliver_file_to_ai_shell(self, file_path: str, description: str = ""):
        """
        Deliver a file to AI Shell user via WebSocket.
        
        Args:
            file_path: Path to the file to be delivered
            description: Optional description of the file
            
        Returns:
            Success message
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return f"❌ File not found: {file_path}"
            
            # Import the WebSocket manager to send the file
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from core.websocket_manager import manager
            
            # Create a message to send to the AI Shell
            import json
            from datetime import datetime
            import asyncio
            
            # Get file information
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            file_message = {
                "type": "file_delivery",
                "file_path": file_path,
                "file_name": file_name,
                "file_size": file_size,
                "description": description,
                "timestamp": datetime.now().isoformat()
            }
            
            # Try to broadcast the file delivery message
            try:
                # Create a JSON message
                message_json = json.dumps(file_message, ensure_ascii=False)
                # In a real implementation, we properly integrate with the asyncio event loop
                # For now, we'll use the manager's broadcast method
                try:
                    # Try to get the current event loop
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, schedule the broadcast
                        loop.create_task(manager.broadcast(message_json))
                    else:
                        # If loop is not running, run the broadcast
                        loop.run_until_complete(manager.broadcast(message_json))
                except RuntimeError:
                    # If no event loop is available, create a new one
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(manager.broadcast(message_json))
                
                return f"📁 Файл готов к загрузке в AI Shell: {file_path}"
            except Exception as e:
                return f"❌ Ошибка отправки файла в AI Shell через WebSocket: {str(e)}"
        except Exception as e:
            return f"❌ Ошибка отправки файла в AI Shell: {str(e)}"
    
    def get_available_tools_list(self) -> str:
        """
        Get a formatted list of all available tools from ToolsSystem.
        
        Returns:
            Formatted string with tool descriptions
        """
        if self.tools_system and hasattr(self.tools_system, 'tool_methods'):
            tools_list = []
            for tool_name in sorted(self.tools_system.tool_methods.keys()):
                tools_list.append(f"- {tool_name}: Execute {tool_name} tool")
            return "\n".join(tools_list)
        else:
            # Fallback to static list if ToolsSystem not available
            return """**Core RAG & Analysis:**
- search_rag_database: Search knowledge base with SBERT
- analyze_image: OCR and object detection for construction images
- check_normative: Verify compliance with building codes
- extract_text_from_pdf: Extract text and images from PDFs
- semantic_parse: Advanced NLP parsing

**Financial & Estimates:**
- calculate_estimate: Real GESN/FER estimate calculations
- calculate_financial_metrics: ROI, NPV, IRR calculations
- find_normatives: Find relevant building standards
- extract_financial_data: Extract costs from documents

**Project Management:**
- generate_construction_schedule: CPM scheduling with NetworkX
- create_gantt_chart: Interactive Gantt charts
- calculate_critical_path: Critical path method analysis
- get_work_sequence: Work dependency analysis

**Pro Document Generation:**
- generate_letter: AI-powered official letters
- improve_letter: Enhance letter drafts
- auto_budget: Automated budget generation
- generate_ppr: Project production plan (ППР)
- create_gpp: Graphical production plan (ГПП)
- parse_gesn_estimate: Parse GESN/FER estimates
- create_document: Generate structured documents

**Advanced Analysis:**
- analyze_tender: Comprehensive tender analysis
- comprehensive_analysis: Full project analysis pipeline
- monte_carlo_sim: Risk analysis simulations
- analyze_bentley_model: IFC/BIM model analysis
- autocad_export: DWG export functionality

**Data Processing:**
- extract_works_nlp: NLP-based work extraction
- extract_construction_data: Construction material extraction
- generate_mermaid_diagram: Process flow diagrams
- create_pie_chart: Data visualization
- create_bar_chart: Statistical charts"""
    
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
