"""Multi-agent coordinator using LangChain for SuperBuilder"""

import json
import os
import re  # For JSON extraction
import logging
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field

# Import configuration and model manager
from core.config import MODELS_CONFIG, get_capabilities_prompt

# Local logger
logger = logging.getLogger(__name__)

# Import Meta-Tools System
try:
    from core.meta_tools.meta_tools_system import MetaToolsSystem, MetaToolCategory
    from core.meta_tools.dag_orchestrator import DAGOrchestrator
    from core.meta_tools.celery_integration import CeleryIntegration, CeleryMetaToolsSystem
    META_TOOLS_AVAILABLE = True
except ImportError:
    print("Meta-Tools System не найдена")
    META_TOOLS_AVAILABLE = False

# Import conversation history (using compressed version as requested)
try:
    from core.agents.conversation_history_compressed import compressed_conversation_history as conversation_history
except ImportError:
    print("Warning: compressed_conversation_history not found — using standard version")
    try:
        from core.agents.conversation_history import conversation_history
    except ImportError:
        print("Warning: conversation_history not found — using empty fallback")
        conversation_history = None  # Fallback: No history

class Plan(BaseModel):
    """JSON schema for coordinator plan"""
    complexity: str = Field(description="Complexity level: low/medium/high")
    time_est: int = Field(description="Estimated time in minutes")
    roles: List[str] = Field(description="Roles involved in execution")
    tasks: List[Dict[str, Any]] = Field(description="List of tasks to execute")

class CoordinatorAgent:
    """LangChain-based coordinator agent for SuperBuilder"""
    
    def __init__(self, lm_studio_url: str = "http://localhost:1234/v1", tools_system=None, enable_meta_tools: bool = True):
        """
        Initialize coordinator agent with LLM and optional ToolsSystem.
        
        Args:
            lm_studio_url: URL for LM Studio API (overridden by config if present)
            tools_system: Optional ToolsSystem instance for enhanced tool awareness
            enable_meta_tools: Enable Meta-Tools System integration
        """
        # Ensure logger handler
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Store tools system for enhanced tool awareness
        self.tools_system = tools_system
        
        # Initialize Meta-Tools System if available and enabled
        self.meta_tools_system = None
        self.celery_integration = None
        if enable_meta_tools and META_TOOLS_AVAILABLE and tools_system:
            try:
                # Create Meta-Tools System
                self.meta_tools_system = MetaToolsSystem(tools_system)
                
                # Optionally create Celery integration (if Redis is available)
                try:
                    self.celery_integration = CeleryIntegration()
                    self.meta_tools_system = CeleryMetaToolsSystem(
                        tools_system,
                        celery_integration=self.celery_integration
                    )
                    logger.info("Meta-Tools System с Celery интеграцией инициализирована")
                except Exception as e:
                    logger.warning(f"Celery недоступен, используем базовую Meta-Tools System: {e}")
                    self.meta_tools_system = MetaToolsSystem(tools_system)
                    
            except Exception as e:
                logger.error(f"Ошибка инициализации Meta-Tools System: {e}")
                self.meta_tools_system = None
        
        # Store request context for file delivery
        self.request_context = None
        
        # Set environment variable for OpenAI API key (not actually needed for LM Studio)
        os.environ["OPENAI_API_KEY"] = "not-needed"
        
        # Initialize LLM for coordinator with configurable model and base URL
        cfg = MODELS_CONFIG.get('coordinator', {})
        model_name = os.getenv('COORDINATOR_MODEL', cfg.get('model', 'qwen/qwen2.5-vl-7b'))
        base_url = cfg.get('base_url', lm_studio_url)
        try:
            self.llm = ChatOpenAI(
                base_url=base_url,
                model=model_name,
                temperature=cfg.get('temperature', 0.1)
            )
            logger.info(f"Coordinator LLM ready: {model_name} @ {base_url}")
        except Exception as e:
            logger.error(f"LLM init failed for coordinator: {e}")
            raise
        
        # Get capabilities prompt for coordinator from config
        system_prompt = get_capabilities_prompt("coordinator")
        self.system_prompt = system_prompt if system_prompt else "You are the coordinator agent for Bldr Empire v2."
        
        # Define tools for coordinator
        self.tools = [
            Tool(
                name="plan_analysis",
                func=self._analyze_and_plan,
                description="Analyze user query and generate execution plan"
            ),
            Tool(
                name="direct_response",
                func=self._direct_response,
                description="Generate direct response for greeting and self-introduction queries"
            ),
            Tool(
                name="transcribe_audio",
                func=self._transcribe_audio,
                description="Transcribe audio file and analyze content"
            )
        ]
        
        # Add Meta-Tools if available
        if self.meta_tools_system:
            self.tools.extend([
                Tool(
                    name="execute_meta_tool",
                    func=self._execute_meta_tool,
                    description="Execute complex meta-tool for comprehensive analysis"
                ),
                Tool(
                    name="list_meta_tools",
                    func=self._list_meta_tools,
                    description="List available meta-tools with descriptions"
                ),
                Tool(
                    name="search_meta_tools",
                    func=self._search_meta_tools,
                    description="Search meta-tools by query or category"
                )
            ])
        
        # Create agent with proper prompt template
        self.agent_executor = self._create_agent()
    
    def _direct_response(self, query: str) -> str:
        """
        Generate direct response for greeting and self-introduction queries.
        
        Args:
            query: User query
            
        Returns:
            Direct response string
        """
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in ["привет", "здравствуй", "hello", "hi", "hey"]):
            return "Привет! Я ваш ассистент в строительной сфере. Рад помочь с вашими вопросами по строительству, сметам, проектам и нормативной документации."
        elif any(keyword in query_lower for keyword in ["расскажи о себе", "что ты умеешь", "кто ты", "what do you know", "what can you do", "tell me about yourself"]):
            return "Я - многофункциональный строительный ассистент, созданный для помощи в различных аспектах строительства. Я могу помочь с:\n\n1. Поиском и анализом строительных норм и правил (СП, ГОСТ, СНиП)\n2. Расчетом смет и бюджетов\n3. Созданием проектной документации\n4. Анализом изображений строительных объектов\n5. Генерацией официальных писем и документов\n6. Планированием строительных работ\n\nМоя цель - сделать вашу работу в строительной сфере более эффективной и точной."
        else:
            return f"Я получил ваш запрос: '{query}'. Я готов помочь с этим вопросом."
    
    def _execute_meta_tool(self, params: str) -> str:
        """
        Execute meta-tool for complex analysis.
        
        Args:
            params: JSON string with meta_tool_name and parameters
            
        Returns:
            Meta-tool execution result
        """
        try:
            if not self.meta_tools_system:
                return "Meta-Tools System недоступна"
            
            # Parse parameters
            import json
            params_dict = json.loads(params) if isinstance(params, str) else params
            
            meta_tool_name = params_dict.get('meta_tool_name', '')
            meta_params = params_dict.get('params', {})
            
            if not meta_tool_name:
                return "Ошибка: не указано имя мета-инструмента"
            
            # Check if Celery integration is available for async execution
            if hasattr(self.meta_tools_system, 'execute_meta_tool_async_celery'):
                # For complex tasks, suggest async execution
                meta_info = self.meta_tools_system.get_meta_tool_info(meta_tool_name)
                if meta_info and meta_info.get('estimated_time', 0) > 5:  # More than 5 minutes
                    return f"""Мета-инструмент '{meta_tool_name}' требует длительного выполнения ({meta_info['estimated_time']} мин).
                    
Рекомендую запустить асинхронно через Celery. Используйте API endpoint для асинхронного выполнения.
                    
Параметры: {json.dumps(meta_params, ensure_ascii=False, indent=2)}"""
            
            # Execute meta-tool synchronously (for quick tools)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.meta_tools_system.execute_meta_tool(meta_tool_name, **meta_params)
            )
            
            if result.get('status') == 'success':
                return f"Мета-инструмент '{meta_tool_name}' выполнен успешно:\n\n{json.dumps(result.get('result', {}), ensure_ascii=False, indent=2)}"
            else:
                return f"Ошибка выполнения мета-инструмента '{meta_tool_name}': {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Ошибка выполнения мета-инструмента: {str(e)}"
    
    def _list_meta_tools(self, params: str = "") -> str:
        """
        List available meta-tools.
        
        Returns:
            List of meta-tools with descriptions
        """
        try:
            if not self.meta_tools_system:
                return "Meta-Tools System недоступна"
            
            meta_tools = self.meta_tools_system.list_meta_tools()
            
            result = "Доступные мета-инструменты:\n\n"
            
            for tool in meta_tools['meta_tools']:
                result += f"📋 **{tool['name']}**\n"
                result += f"   Категория: {tool['category']}\n"
                result += f"   Описание: {tool['description']}\n"
                result += f"   Время выполнения: ~{tool['estimated_time']} мин\n"
                result += f"   Сложность: {tool['complexity']}\n"
                result += f"   Обязательные параметры: {', '.join(tool['required_params'])}\n"
                if tool['optional_params']:
                    result += f"   Опциональные параметры: {', '.join(tool['optional_params'])}\n"
                result += "\n"
            
            result += f"\nВсего доступно: {meta_tools['total']} мета-инструментов"
            return result
            
        except Exception as e:
            return f"Ошибка получения списка мета-инструментов: {str(e)}"
    
    def _search_meta_tools(self, params: str) -> str:
        """
        Search meta-tools by query.
        
        Args:
            params: Search query or JSON with query and category
            
        Returns:
            Search results
        """
        try:
            if not self.meta_tools_system:
                return "Meta-Tools System недоступна"
            
            # Parse search parameters
            if isinstance(params, str) and params.strip().startswith('{'):
                import json
                search_params = json.loads(params)
                query = search_params.get('query', '')
                category = search_params.get('category')
                if category:
                    category = MetaToolCategory(category)
            else:
                query = params
                category = None
            
            if not query:
                return "Ошибка: не указан поисковый запрос"
            
            results = self.meta_tools_system.search_meta_tools(query, category)
            
            if not results:
                return f"По запросу '{query}' мета-инструменты не найдены"
            
            result_text = f"Результаты поиска по запросу '{query}':\n\n"
            
            for tool in results:
                result_text += f"🔍 **{tool['name']}** (релевантность: {tool['relevance']})\n"
                result_text += f"   {tool['description']}\n"
                result_text += f"   Категория: {tool['category']}, Время: {tool['estimated_time']} мин\n\n"
            
            return result_text
            
        except Exception as e:
            return f"Ошибка поиска мета-инструментов: {str(e)}"
    
    def _transcribe_audio(self, params: str):
        """
        Transcribe audio file using Whisper.
        
        Args:
            params: JSON string with audio_path parameter
            
        Returns:
            Transcription result string
        """
        try:
            # Local import to avoid issues if not installed
            import whisper
            import json
            
            # Parse parameters
            params_dict = json.loads(params) if isinstance(params, str) else params
            audio_path = params_dict.get('audio_path', '')
            
            if not audio_path or not os.path.exists(audio_path):
                return "Ошибка: Не указан путь к аудиофайлу или файл не существует"
            
            # Load Whisper model (base for speed/balance)
            model = whisper.load_model("base")
            
            # Transcribe
            result = model.transcribe(audio_path)
            transcription = result["text"]
            
            # Simple norm check
            norm_check = self._simple_norm_check(str(transcription))
            
            return {"status": "success", "transcription": transcription, "quick_analysis": norm_check}
        except ImportError:
            return {"status": "error", "error": "Whisper не установлен (pip install openai-whisper)"}
        except Exception as e:
            return {"status": "error", "error": f"Ошибка транскрипции аудио: {str(e)}"}
    
    def _simple_norm_check(self, text: str) -> str:
        """
        Simple keyword check for construction norms in text.
        
        Args:
            text: Text to check
            
        Returns:
            Analysis string
        """
        if not isinstance(text, str):
            text = str(text)
            
        norm_keywords = ["СП ", "ГОСТ ", "СНиП ", "ГЭСН ", "ФЗ-", "Постановление правительства"]
        found_norms = [kw for kw in norm_keywords if kw in text.upper()]
        
        if found_norms:
            return f"Найдены упоминания норм: {', '.join(found_norms)}. Проверьте в базе знаний."
        else:
            return "Явных норм не найдено. Опишите детали для глубокого анализа."
    
    def _analyze_and_plan(self, query: str) -> str:  # Return str for Tool
        """
        Analyze query and generate execution plan.
        
        Args:
            query: User query
            
        Returns:
            JSON string with plan
        """
        # Get conversation history (limited)
        conversation_context = ""
        if self.request_context and "user_id" in self.request_context and conversation_history:
            user_id = self.request_context["user_id"]
            conversation_context = conversation_history.get_formatted_history(user_id, max_tokens=500) if conversation_history else ""
        
        # Shortened prompt (anti-bloat)
        available_tools_short = self.get_available_tools_list()[:1500]  # Truncate
        prompt = f"""Analyze the query and generate a JSON execution plan.

Query: {query}

Context: {conversation_context}

Structure:
{{
    "complexity": "low|medium|high",
    "time_est": minutes,
    "roles": ["role1", ...],
    "tasks": [
        {{"id": 1, "agent": "role", "input": "desc", "tool": "tool_name"}},
        ...
    ]
}}

Roles: coordinator (planning), chief_engineer (norms/analysis), analyst (estimates), project_manager (scheduling).

Tools: {available_tools_short}

Return ONLY valid JSON. No extra text."""

        try:
            print(f"Sending plan prompt: {prompt[:100]}...")
            response = self.llm.invoke(prompt)
            response_str = response.content if hasattr(response, 'content') else str(response)
            
            # Parse/validate JSON
            try:
                plan_json = json.loads(str(response_str))
                return json.dumps(plan_json, ensure_ascii=False)  # Str for Tool
            except json.JSONDecodeError:
                print("JSON parse failed in _analyze_and_plan")
        except Exception as e:
            print(f"Error in _analyze_and_plan: {e}")
        
        # Fallback
        fallback = self._generate_fallback_plan(query)
        return fallback  # str
    
    def _generate_fallback_plan(self, query: str) -> str:  # Return str (JSON)
        """
        Generate fallback plan (keyword-based).
        
        Args:
            query: User query
            
        Returns:
            JSON string
        """
        query_lower = query.lower()
        greeting_keywords = ["привет", "здравствуй", "hello", "hi", "hey"]
        self_intro_keywords = ["расскажи о себе", "что ты умеешь", "кто ты"]
        voice_keywords = ["транскрибируй", "transcribe", "голосовое", "voice", "аудио"]
        
        if any(kw in query_lower for kw in voice_keywords):
            plan = {
                "complexity": "medium",
                "time_est": 2,
                "roles": ["coordinator"],
                "tasks": [
                    {"id": 1, "agent": "coordinator", "input": query, "tool": "transcribe_audio"},
                    {"id": 2, "agent": "chief_engineer", "input": "Анализ транскрипта", "tool": "search_rag_database"}
                ]
            }
            return json.dumps(plan, ensure_ascii=False)
        
        is_greeting = any(kw in query_lower for kw in greeting_keywords)
        is_self_intro = any(kw in query_lower for kw in self_intro_keywords)
        
        if is_greeting or is_self_intro:
            plan = {
                "complexity": "low",
                "time_est": 1,
                "roles": ["coordinator"],
                "tasks": [{"id": 1, "agent": "coordinator", "input": query, "tool": "direct_response"}]
            }
        elif any(kw in query_lower for kw in ["стоимость", "смета", "расчет"]):
            plan = {
                "complexity": "medium",
                "time_est": 2,
                "roles": ["analyst"],
                "tasks": [
                    {"id": 1, "agent": "analyst", "input": f"Estimates for: {query}", "tool": "search_rag_database"},
                    {"id": 2, "agent": "analyst", "input": query, "tool": "calc_estimate"}
                ]
            }
        elif any(keyword in query_lower for keyword in ["комплексный анализ", "comprehensive analysis", "полный анализ проекта"]):
            # Комплексный анализ проекта через мета-инструмент
            if self.meta_tools_system:
                plan = {
                    "complexity": "high",
                    "time_est": 15,
                    "roles": ["coordinator"],
                    "tasks": [{
                        "id": 1, 
                        "agent": "coordinator", 
                        "input": query, 
                        "tool": "execute_meta_tool",
                        "meta_tool_name": "comprehensive_analysis_project"
                    }]
                }
                return json.dumps(plan, ensure_ascii=False)
        elif any(keyword in query_lower for keyword in ["автоматическое планирование", "automated planning", "план проекта"]):
            # Автоматическое планирование через мета-инструмент
            if self.meta_tools_system:
                plan = {
                    "complexity": "high",
                    "time_est": 20,
                    "roles": ["coordinator"],
                    "tasks": [{
                        "id": 1, 
                        "agent": "coordinator", 
                        "input": query, 
                        "tool": "execute_meta_tool",
                        "meta_tool_name": "automated_project_planning"
                    }]
                }
                return json.dumps(plan, ensure_ascii=False)
        elif any(keyword in query_lower for keyword in ["проверка соответствия", "compliance check", "проверка норм"]):
            # Проверка соответствия нормам через мета-инструмент
            if self.meta_tools_system:
                plan = {
                    "complexity": "medium",
                    "time_est": 10,
                    "roles": ["coordinator"],
                    "tasks": [{
                        "id": 1, 
                        "agent": "coordinator", 
                        "input": query, 
                        "tool": "execute_meta_tool",
                        "meta_tool_name": "comprehensive_compliance_check"
                    }]
                }
                return json.dumps(plan, ensure_ascii=False)
        elif any(keyword in query_lower for keyword in ["список мета-инструментов", "meta tools list", "что умеют мета-инструменты"]):
            # Список мета-инструментов
            plan = {
                "complexity": "low",
                "time_est": 1,
                "roles": ["coordinator"],
                "tasks": [{"id": 1, "agent": "coordinator", "input": query, "tool": "list_meta_tools"}]
            }
            return json.dumps(plan, ensure_ascii=False)
        elif any(keyword in query_lower for keyword in ["норма", "сп", "гост"]):
            plan = {
                "complexity": "medium",
                "time_est": 2,
                "roles": ["chief_engineer"],
                "tasks": [
                    {"id": 1, "agent": "chief_engineer", "input": f"Norms for: {query}", "tool": "search_rag_database"},
                    {"id": 2, "agent": "chief_engineer", "input": query, "tool": "check_normative"}
                ]
            }
        elif any(kw in query_lower for kw in ["проект", "ппр", "график"]):
            plan = {
                "complexity": "high",
                "time_est": 5,
                "roles": ["project_manager"],
                "tasks": [
                    {"id": 1, "agent": "project_manager", "input": f"Project docs for: {query}", "tool": "search_rag_database"},
                    {"id": 2, "agent": "project_manager", "input": query, "tool": "generate_construction_schedule"}
                ]
            }
        else:
            plan = {
                "complexity": "low",
                "time_est": 1,
                "roles": ["coordinator"],
                "tasks": [{"id": 1, "agent": "coordinator", "input": query, "tool": "search_rag_database"}]
            }
        
        return json.dumps(plan, ensure_ascii=False)
    
    def get_available_tools_list(self) -> str:
        """
        Get formatted tools list from Master Tools System.
        """
        if self.tools_system:
            try:
                # Try to get tools list from Master Tools System adapter
                if hasattr(self.tools_system, 'list_available_tools'):
                    tools_info = self.tools_system.list_available_tools()
                    if isinstance(tools_info, dict) and 'tools' in tools_info:
                        tools_list = []
                        for tool in tools_info['tools'][:15]:  # Limit to prevent prompt bloat
                            name = tool.get('name', 'unknown')
                            desc = tool.get('description', '')[:80]  # Truncate long descriptions
                            tools_list.append(f"- {name}: {desc}")
                        return "\n".join(tools_list)
                # Legacy fallback
                elif hasattr(self.tools_system, 'tool_methods'):
                    tools_list = [f"- {name}: {desc}" for name, desc in self.tools_system.tool_methods.items()]
                    return "\n".join(sorted(tools_list)[:15])  # Limit to prevent prompt bloat
            except Exception as e:
                print(f"Error getting tools list: {e}")
        
        # Include Meta-Tools in the list if available
        tools_list = """Core: search_rag_database, analyze_image, check_normative, extract_text_from_pdf.
Financial: calculate_financial_metrics, auto_budget, extract_financial_data.
Project: create_gantt_chart, calculate_critical_path, generate_ppr.
Docs: generate_letter, improve_letter, create_document.
Analysis: analyze_tender, comprehensive_analysis, extract_works_nlp.
Visualization: create_pie_chart, create_bar_chart.
Super: analyze_bentley_model, monte_carlo_sim, autocad_export."""
        
        if self.meta_tools_system:
            meta_tools = self.meta_tools_system.list_meta_tools()
            meta_tools_list = []
            for tool in meta_tools['meta_tools'][:5]:  # Limit to prevent prompt bloat
                name = tool['name']
                desc = tool['description'][:60] + '...' if len(tool['description']) > 60 else tool['description']
                meta_tools_list.append(f"- {name}: {desc}")
            
            if meta_tools_list:
                tools_list += "\nMeta-Tools: " + "\n".join(meta_tools_list)
        
        return tools_list
    
    def _create_agent(self) -> AgentExecutor:
        """Create ReAct agent."""
        prompt_template = """{system_prompt}

Tools: {tools}
Tool Names: {tool_names}

Format (ReAct exactly):
Question: {input}
Thought: ...
Action: [tool_name]
Action Input: ...
Observation: ...
... (repeat)
Thought: Final answer
Final Answer: ...

Begin! Thought: {agent_scratchpad}"""

        tools_str = "\n".join([f"{t.name}: {t.description}" for t in self.tools])
        tool_names_str = ", ".join([t.name for t in self.tools])
        prompt = PromptTemplate.from_template(prompt_template).partial(
            system_prompt=self.system_prompt,
            tools=tools_str,
            tool_names=tool_names_str
        )

        agent = create_react_agent(self.llm, self.tools, prompt)

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False,  # Speed
            handle_parsing_errors=True,
            max_iterations=4,
            max_execution_time=3600.0
        )
    
    def generate_plan(self, query: str) -> Dict[str, Any]:
        """
        Generate plan (Dict).
        """
        import json
        
        query_lower = query.lower()
        greeting_keywords = ["привет", "здравствуй", "hello", "hi", "hey"]
        self_intro_keywords = ["расскажи о себе", "что ты умеешь", "кто ты"]
        voice_keywords = ["транскрибируй", "transcribe", "голосовое", "voice", "аудио"]
        
        if any(kw in query_lower for kw in greeting_keywords + self_intro_keywords):
            return json.loads(self._generate_fallback_plan(query))
        
        # Modalities from context
        if self.request_context and isinstance(self.request_context, dict):
            if self.request_context.get("audio_path"):
                return {
                    "complexity": "medium",
                    "time_est": 2,
                    "roles": ["coordinator"],
                    "tasks": [
                        {"id": 1, "agent": "coordinator", "input": {"audio_path": self.request_context.get("audio_path")}, "tool": "transcribe_audio"}
                    ]
                }
            if self.request_context.get("image_path"):
                # Branch: unknown image type → do OCR + objects + dimensions in one pass
                return {
                    "complexity": "medium",
                    "time_est": 3,
                    "roles": ["chief_engineer"],
                    "tasks": [
                        {
                            "id": 1,
                            "agent": "chief_engineer",
                            "input": {
                                "image_path": self.request_context.get("image_path"),
                                "analysis_type": "comprehensive",
                                "detect_objects": True,
                                "extract_dimensions": True,
                                "recognize_text": True,
                                "confidence_threshold": 0.7
                            },
                            "tool": "analyze_image"
                        }
                    ]
                }
        
        if any(kw in query_lower for kw in voice_keywords):
            return {
                "complexity": "medium",
                "time_est": 3,
                "roles": ["coordinator", "chief_engineer"],
                "tasks": [
                    {"id": 1, "agent": "coordinator", "input": {"audio_path": self.request_context.get("audio_path", "")}, "tool": "transcribe_audio"},
                    # Post-transcription analysis step: feed transcript to RAG if needed
                    {"id": 2, "agent": "chief_engineer", "input": {"from_prev": "transcription"}, "tool": "search_rag_database"}
                ]
            }
        
        # Agent for complex
        try:
            result = self.agent_executor.invoke({"input": query})
            plan_text = str(result["output"])
            
            if plan_text.strip().startswith('{'):
                return json.loads(plan_text)
            
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"generate_plan error: {e}")
        
        # Fallback
        return json.loads(self._generate_fallback_plan(query))
    
    def _convert_plan_to_natural_language(self, plan: Dict[str, Any], query: str) -> str:
        """
        Convert JSON plan to natural response.
        """
        try:
            # Check for direct
            tasks = plan.get("tasks", [])
            if len(tasks) == 1 and tasks[0].get("tool") == "direct_response":
                return self._direct_response(query)
            
            # History
            conversation_context = ""
            if self.request_context and "user_id" in self.request_context and conversation_history:
                user_id = self.request_context["user_id"]
                conversation_context = conversation_history.get_formatted_history(user_id, max_tokens=1000) if conversation_history else ""
            
            # LLM convert (short prompt)
            prompt = f"""Convert plan to natural RU response (friendly, explain steps).

Query: {query}

Context: {conversation_context}

Plan: {json.dumps(plan, ensure_ascii=False, indent=2)}

Response (explain: how addressed, roles, steps, time):"""
            
            response = self.llm.invoke(prompt)
            result = str(response.content).strip() if hasattr(response, 'content') else str(response)
            
            # Clean
            if result.startswith("```") and result.endswith("```"):
                result = result[3:-3].strip()
            return result
            
        except Exception as e:
            print(f"Convert error: {e}")
            return self._generate_fallback_natural_language_response(plan, query)
    
    def _generate_fallback_natural_language_response(self, plan: Dict[str, Any], query: str) -> str:
        """
        Fallback natural response.
        """
        complexity = plan.get("complexity", "unknown")
        time_est = plan.get("time_est", 0)
        roles = ", ".join(plan.get("roles", []))
        tasks_desc = "\n".join([f"{t.get('id', '')}. {t.get('agent', '')}: {t.get('input', '')}" for t in plan.get("tasks", [])])
        
        # RU/EN auto-detect (simple)
        if any(char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for char in query):
            response = f"Анализ запроса: '{query}'\n\nСложность: {complexity}\nВремя: {time_est} мин\nРоли: {roles}\n\nПлан:\n{tasks_desc}\n\nНачинаю..."
        else:
            response = f"Analyzed: '{query}'\n\nComplexity: {complexity}\nTime: {time_est} min\nRoles: {roles}\n\nPlan:\n{tasks_desc}\n\nStarting..."
        
        return response
    
    def process_query(self, query: str) -> str:
        """
        Main entry: Plan → Response.
        """
        try:
            # Add to history
            if self.request_context and "user_id" in self.request_context and conversation_history:
                user_id = self.request_context["user_id"]
                conversation_history.add_message(user_id, {"role": "user", "content": query})
            
            # Generate plan
            plan = self.generate_plan(query)
            
            # Early direct/voice
            tasks = plan.get("tasks", [])
            if len(tasks) == 1:
                task = tasks[0]
                if task.get("tool") == "direct_response":
                    response = self._direct_response(query)
                    # Add to history
                    if self.request_context and "user_id" in self.request_context and conversation_history:
                        conversation_history.add_message(user_id, {"role": "assistant", "content": response})
                    return response
                
                if task.get("tool") == "transcribe_audio":
                    params = task.get("input", {}) or {"audio_path": self.request_context.get("audio_path", "")}
                    response = self._transcribe_audio(json.dumps(params))
                    # Add to history
                    if self.request_context and "user_id" in self.request_context and conversation_history:
                        conversation_history.add_message(user_id, {"role": "assistant", "content": response})
                    return response
            
            # Complex: Convert to natural
            response = self._convert_plan_to_natural_language(plan, query)
            
            # Add to history
            if self.request_context and "user_id" in self.request_context and conversation_history:
                conversation_history.add_message(user_id, {"role": "assistant", "content": response})
            
            return response
            
        except Exception as e:
            print(f"process_query error: {e}")
            # Fallback direct if greeting
            query_lower = query.lower()
            greeting_keywords = ["привет", "здравствуй", "hello", "hi", "hey"]
            self_intro_keywords = ["расскажи о себе", "что ты умеешь", "кто ты"]
            if any(kw in query_lower for kw in greeting_keywords + self_intro_keywords):
                return self._direct_response(query)
            return f"Ошибка обработки: {str(e)[:100]}. Перефразируйте запрос."
    
    def generate_response(self, query: str) -> Dict[str, Any]:
        """
        API entry-point (for bldr_api.py): Generate response with status/plan.
        
        Args:
            query: User query
            
        Returns:
            Dict: {response: str, plan: Dict|None, status: 'success'|'error', error: str|None}
        """
        try:
            # Set dummy context if none (for API)
            if not self.request_context:
                self.set_request_context({"user_id": "api_user", "channel": "api"})
            
            response = self.process_query(query)
            plan = self.generate_plan(query)  # Optional: Include plan for debug
            
            return {
                "response": response,
                "plan": plan,
                "status": "success",
                "error": None
            }
        except Exception as e:
            print(f"generate_response error: {e}")
            return {
                "response": f"API Error: {str(e)[:100]}. Try again.",
                "plan": None,
                "status": "error",
                "error": str(e)
            }
    
    def set_request_context(self, context):
        """Set request context."""
        self.request_context = context
    
    def clear_request_context(self):
        """Clear context."""
        self.request_context = None
    
    def deliver_file(self, file_path: str, description: str = "") -> str:
        """Deliver file via channel."""
        if not self.request_context:
            return "❌ No context for delivery"
        
        channel = self.request_context.get("channel", "unknown")
        if channel == "telegram":
            return self._deliver_file_to_telegram(file_path, description)
        elif channel == "ai_shell":
            return self._deliver_file_to_ai_shell(file_path, description)
        else:
            return f"❌ Unsupported channel: {channel}"
    
    def _deliver_file_to_telegram(self, file_path: str, description: str = "") -> str:
        """Telegram delivery."""
        try:
            if not os.path.exists(file_path):
                return f"❌ File not found: {file_path}"
            
            if not self.request_context or 'chat_id' not in self.request_context:
                return "❌ No chat_id"
            
            chat_id = self.request_context['chat_id']
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from integrations.telegram_bot import send_file_to_user
            
            success = send_file_to_user(chat_id, file_path, description)
            return f"✅ Sent to Telegram: {file_path}" if success else f"❌ Send failed: {file_path}"
        except Exception as e:
            return f"❌ Telegram error: {str(e)}"
    
    def _deliver_file_to_ai_shell(self, file_path: str, description: str = "") -> str:
        """AI Shell delivery via WebSocket."""
        try:
            if not os.path.exists(file_path):
                return f"❌ File not found: {file_path}"
            
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from core.websocket_manager import manager
            import json
            from datetime import datetime
            import asyncio
            
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            message = {
                "type": "file_delivery",
                "file_path": file_path,
                "file_name": file_name,
                "file_size": file_size,
                "description": description,
                "timestamp": datetime.now().isoformat()
            }
            
            message_json = json.dumps(message, ensure_ascii=False)
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast(message_json))
            else:
                loop.run_until_complete(manager.broadcast(message_json))
            
            return f"📁 Ready in AI Shell: {file_path}"
        except Exception as e:
            return f"❌ AI Shell error: {str(e)}"

# Optional: Test block (run python coordinator_agent.py for quick test)
if __name__ == "__main__":
    agent = CoordinatorAgent()
    print("Test greeting:", agent.process_query("привет"))
    print("Test self-intro:", agent.process_query("расскажи о себе"))
    print("Test API response:", agent.generate_response("анализ нормы СП 48"))