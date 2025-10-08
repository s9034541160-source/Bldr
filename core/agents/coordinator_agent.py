#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adaptive Coordinator Agent
--------------------------
Single-entry coordinator that lets the model decide: short reply vs tools vs delegation.
Uses MODELS_CONFIG['coordinator'] prompt for behavior.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from core.model_manager import ModelManager
from core.config import MODELS_CONFIG
from core.exceptions import (
    ToolValidationError, ToolDependencyError, ToolExecutionTimeoutError,
    AgentPlanningError, AgentExecutionError, AgentCommunicationError,
    get_error_category, get_user_friendly_message
)
from core.structured_logging import get_logger
from core.tracing.execution_tracer import get_tracer, TraceType, TraceStatus


class CoordinatorAgent:
    def __init__(self) -> None:
        self.model_manager = ModelManager()
        self.tools_system = None  # type: ignore
        # Ensure attributes used by other variants exist
        self.meta_tools_system = None  # type: ignore
        self.system_prompt = "You are the coordinator agent for Bldr Empire v2."
        self.logger = get_logger("coordinator")  # 🚀 СТРУКТУРИРОВАННОЕ ЛОГИРОВАНИЕ
        self.tracer = get_tracer()  # 🚀 СИСТЕМА ТРАССИРОВКИ

    def set_tools_system(self, tools_system: Any) -> None:
        self.tools_system = tools_system

    def _get_available_tools_names(self) -> List[str]:
        try:
            if hasattr(self.tools_system, "list_tools"):
                return [sig.name for sig in self.tools_system.list_tools()]
        except Exception as e:
            logging.warning(f"[CoordinatorAgent] tools listing failed: {e}")
        return []

    def process_request_old(self, query: str) -> str:
        try:
            # Defensive: ensure system_prompt exists
            if not hasattr(self, "system_prompt") or not self.system_prompt:
                self.system_prompt = MODELS_CONFIG.get("coordinator", {}).get("description", "You are the coordinator agent for Bldr Empire v2.")
            
            # Убираем хардкодную детекцию - доверяем модели самой решать
            
            # If the input contains a transcription snippet, acknowledge concisely
            tr_text = self._extract_transcription_text(query)
            if tr_text:
                return f"Транскрипция распознана. Краткий ответ: {tr_text.strip()}"
            # Proactive: use request_context modalities if available
            if isinstance(getattr(self, 'request_context', None), dict):
                # Voice
                rc_audio = self.request_context.get('audio_path')
                if rc_audio:
                    tr_auto = self._transcribe_via_tools_or_local(rc_audio)
                    if tr_auto:
                        return f"🎤 Транскрипция: {tr_auto}"
                # Image
                rc_image = self.request_context.get('image_path')
                if rc_image and self.tools_system:
                    try:
                        t_res = self.tools_system.execute_tool('analyze_image', image_path=rc_image)
                        t_out = getattr(t_res, 'data', t_res)
                        vl = self._try_vl_image_analysis(rc_image)
                        if vl:
                            return f"✅ Анализ изображения (инструмент): {t_out}\n\n🧠 Анализ ИИ (VL): {vl}"
                        return f"✅ Анализ изображения (инструмент): {t_out}"
                    except Exception as e:
                        return f"❌ Ошибка анализа изображения: {e}"
            # If audio file path is present, transcribe first
            audio_path = self._extract_audio_path(query)
            if audio_path:
                tr = self._transcribe_via_tools_or_local(audio_path)
                if tr:
                    return f"🎤 Транскрипция: {tr}"
            system_prompt = MODELS_CONFIG.get("coordinator", {}).get("description", "")
            tools_list = self._get_available_tools_names()
            messages = [
                {
                    "role": "system",
                    "content": system_prompt + (f"\n\nДоступные инструменты: {', '.join(tools_list)}" if tools_list else "")
                },
                {"role": "user", "content": query},
            ]

            response_text = self.model_manager.query("coordinator", messages)
            text = str(response_text) if response_text is not None else ""

            # Try to detect tool call JSON in response (support name/tool, arguments/args)
            # Respect json_mode_enabled setting
            json_mode = True
            try:
                rc = self.request_context if isinstance(getattr(self, 'request_context', None), dict) else {}
                json_mode = bool(((rc.get('settings') or {}).get('coordinator') or {}).get('json_mode_enabled', True))
            except Exception:
                json_mode = True

            tool_call = self._extract_json_block(text) if json_mode else None
            if tool_call and isinstance(tool_call, dict) and (tool_call.get("tool") or tool_call.get("name")):
                tool_name = tool_call.get("tool") or tool_call.get("name")
                arguments = tool_call.get("arguments", {}) or tool_call.get("args", {}) or {}
                if self.tools_system:
                    try:
                        tool_res = self.tools_system.execute_tool(tool_name, **arguments)
                        tool_out = getattr(tool_res, 'data', tool_res)
                        # If image analysis, try parallel VL analysis by chief_engineer
                        if tool_name in ("analyze_image", "vl_analyze_photo") and isinstance(arguments, dict) and arguments.get("image_path"):
                            vl_text = self._try_vl_image_analysis(arguments.get("image_path"))
                            if vl_text:
                                return f"✅ Анализ изображения (инструмент): {tool_out}\n\n🧠 Анализ ИИ (VL): {vl_text}"
                        return f"✅ Инструмент '{tool_name}' выполнен. Результат: {tool_out}"
                    except Exception as e:
                        return f"❌ Ошибка выполнения инструмента '{tool_name}': {e}"
                return f"⚠️ Инструменты недоступны. Запрошен '{tool_name}'."

            # Detect function-like tool call e.g. analyze_image(image_path="...", param=1)
            fn_tool = self._extract_function_call(text) if json_mode else None
            if fn_tool and fn_tool.get("tool"):
                tool_name = fn_tool.get("tool")
                arguments = fn_tool.get("arguments", {}) or {}
                if self.tools_system:
                    try:
                        tool_res = self.tools_system.execute_tool(tool_name, **arguments)
                        tool_out = getattr(tool_res, 'data', tool_res)
                        if tool_name in ("analyze_image", "vl_analyze_photo") and isinstance(arguments, dict) and arguments.get("image_path"):
                            vl_text = self._try_vl_image_analysis(arguments.get("image_path"))
                            if vl_text:
                                return f"✅ Анализ изображения (инструмент): {tool_out}\n\n🧠 Анализ ИИ (VL): {vl_text}"
                        return f"✅ Инструмент '{tool_name}' выполнен. Результат: {tool_out}"
                    except Exception as e:
                        # 🚀 УМНАЯ ОБРАБОТКА ОШИБОК: Определяем тип ошибки и реагируем соответственно
                        error_category = get_error_category(e)
                        user_message = get_user_friendly_message(e)
                        
                        if error_category == "validation_error":
                            return f"⚠️ {user_message}\n\nПроверьте параметры инструмента '{tool_name}' и попробуйте еще раз."
                        elif error_category == "dependency_error":
                            return f"⚠️ {user_message}\n\nИнструмент '{tool_name}' временно недоступен. Попробуйте позже."
                        elif error_category == "timeout_error":
                            return f"⚠️ {user_message}\n\nИнструмент '{tool_name}' работает медленно. Попробуйте упростить запрос."
                        elif error_category == "resource_error":
                            return f"⚠️ {user_message}\n\nНедоступен необходимый ресурс для '{tool_name}'. Проверьте подключение."
                        else:
                            return f"❌ Ошибка выполнения инструмента '{tool_name}': {user_message}"
                return f"⚠️ Инструменты недоступны. Запрошен '{tool_name}'."

            # 🚨 НОВЫЙ СТАНДАРТ: Честная обработка пустого ответа
            if not text.strip():
                logger.error("❌ LLM-координатор вернул пустой ответ. Сбой генерации.")
                return "⚠️ Сбой обработки. Не удалось сгенерировать ответ. Требуется проверка логов."
            return text.strip()

        except Exception as e:
            logging.error(f"[CoordinatorAgent] processing error: {e}")
            return "Извините, произошла ошибка при обработке запроса. Попробуйте переформулировать."

    @staticmethod
    def _extract_json_block(text: str) -> Optional[Dict[str, Any]]:
        """Extract first JSON object from free-form text, if any."""
        try:
            import re
            m = re.search(r"\{[\s\S]*\}", text)
            if not m:
                return None
            candidate = m.group(0)
            return json.loads(candidate)
        except Exception:
            return None

    @staticmethod
    def _extract_function_call(text: str) -> Optional[Dict[str, Any]]:
        """Extract function-like tool call: tool_name(arg1=..., arg2="...")"""
        try:
            import re
            m = re.search(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)", text)
            if not m:
                return None
            tool = m.group(1)
            args_src = m.group(2).strip()
            if not args_src:
                return {"tool": tool, "arguments": {}}
            args: Dict[str, Any] = {}
            # Split by commas not inside quotes
            parts = re.split(r",\s*(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", args_src)
            for part in parts:
                kv = part.split("=", 1)
                if len(kv) != 2:
                    continue
                key = kv[0].strip()
                val_raw = kv[1].strip()
                # Strip quotes if present
                if (val_raw.startswith('"') and val_raw.endswith('"')) or (val_raw.startswith("'") and val_raw.endswith("'")):
                    val = val_raw[1:-1]
                else:
                    # Try to parse numbers/bools
                    if val_raw.lower() in ("true", "false"):
                        val = val_raw.lower() == "true"
                    else:
                        try:
                            if "." in val_raw:
                                val = float(val_raw)
                            else:
                                val = int(val_raw)
                        except Exception:
                            val = val_raw
                args[key] = val
            return {"tool": tool, "arguments": args}
        except Exception:
            return None

    @staticmethod
    def _extract_transcription_text(text: str) -> Optional[str]:
        r"""Extract transcription from patterns like: Транскрипция: "..." or Transcription: "...""" 
        try:
            import re
            m = re.search(r"Транскрипц[ияИи][^:]*:\s*\"([\s\S]*?)\"", text)
            if m:
                return m.group(1)
            m2 = re.search(r"Transcription[^:]*:\s*\"([\s\S]*?)\"", text, re.IGNORECASE)
            if m2:
                return m2.group(1)
        except Exception:
            pass
        return None

    @staticmethod
    def _extract_audio_path(text: str) -> Optional[str]:
        r"""Find local audio path in text like D:\TEMP\file.(ogg|mp3|wav|m4a)."""
        try:
            import re
            m = re.search(r"([A-Za-z]:\\\\[^\s\"]+\.(ogg|mp3|wav|m4a))", text, re.IGNORECASE)
            if m:
                return m.group(1)
        except Exception:
            pass
        return None

    def _transcribe_via_tools_or_local(self, audio_path: str) -> Optional[str]:
        """Try tools_system transcription first with common tool names, fallback to local whisper."""
        # Try tools
        try:
            if self.tools_system:
                candidate_tools = [
                    "transcribe_audio", "whisper_transcribe", "speech_to_text", "stt_whisper"
                ]
                for name in candidate_tools:
                    try:
                        res = self.tools_system.execute_tool(name, audio_path=audio_path)
                        data = getattr(res, 'data', res)
                        if isinstance(data, dict) and data.get('transcription'):
                            return str(data.get('transcription')).strip()
                        if isinstance(data, str) and data.strip():
                            return data.strip()
                    except Exception:
                        continue
        except Exception:
            pass
        # Local fallback: whisper
        try:
            import whisper, os
            if not os.path.exists(audio_path):
                return None
            model = whisper.load_model("base")
            result = model.transcribe(audio_path)
            return str(result.get("text", "")).strip()
        except Exception:
            return None

    def _try_vl_image_analysis(self, image_path: Optional[str]) -> Optional[str]:
        """Ask chief_engineer (VL) to analyze image via base64 data URI; return short text."""
        try:
            if not image_path:
                return None
            import os, base64
            if not os.path.exists(image_path):
                return None
            with open(image_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            data_uri = f"data:image/jpeg;base64,{b64}"
            messages = [
                {"role": "system", "content": "Ты — Главный инженер. Кратко опиши сцену, объекты, потенциальные нарушения и рекомендации."},
                {"role": "user", "content": f"Проанализируй изображение: {data_uri}"}
            ]
            resp = self.model_manager.query("chief_engineer", messages)
            return str(resp).strip() if resp else None
        except Exception:
            return None

"""Multi-agent coordinator using LangChain for SuperBuilder"""

import json
import os
import re  # For JSON extraction
import logging
import time
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field

# Dialog manager for pause/resume flow
try:
    from core.dialog_manager import dialog_manager
    from core.dialog_state import DialogStatus, DialogState
except Exception:
    dialog_manager = None  # type: ignore
    DialogStatus = None  # type: ignore
    DialogState = None  # type: ignore

# Import configuration and model manager
try:
    from core.config import MODELS_CONFIG, get_capabilities_prompt
    CONFIG_AVAILABLE = True
except ImportError:
    print("Configuration module not available")
    MODELS_CONFIG = {}
    get_capabilities_prompt = lambda x: ""
    CONFIG_AVAILABLE = False

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
        # Initialize meta-tools related attributes to avoid AttributeError before configuration
        self.meta_tools_system = None
        self.celery_integration = None
        self.enable_meta_tools = enable_meta_tools
        
        # Defensive defaults to avoid attribute errors before full setup
        self.tools: List[Any] = []  # type: ignore
        self.agent_executor = None
        self.request_context = None
        
        # Complete setup (defines tools, system prompt, agent executor)
        try:
            self.set_tools_system(tools_system)
        except Exception as e:
            logger.warning(f"CoordinatorAgent init: set_tools_system failed: {e}")
            # Ensure at least LLM and prompt are available
            try:
                self._init_llm_if_needed(lm_studio_url)
            except Exception:
                pass
            system_prompt = get_capabilities_prompt("coordinator") if CONFIG_AVAILABLE else None
            self.system_prompt = system_prompt if system_prompt else "You are the coordinator agent for Bldr Empire v2."
            # agent_executor remains None; will be lazily created when tools are available

    def set_tools_system(self, tools_system) -> None:
        """Set/replace the attached tools system at runtime."""
        self.tools_system = tools_system
        
        # Initialize Meta-Tools System if available and enabled
        self.meta_tools_system = None
        self.celery_integration = None
        if self.enable_meta_tools and META_TOOLS_AVAILABLE and tools_system:
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
        
        # Initialize LLM (base URL from config/env inside method)
        self._init_llm_if_needed()
        
        # Get capabilities prompt for coordinator from config
        system_prompt = get_capabilities_prompt("coordinator") if CONFIG_AVAILABLE else None
        self.system_prompt = system_prompt if system_prompt else "You are the coordinator agent for Bldr Empire v2."
        
        # Light, pragmatic guidance (no over-constraints)
        self.system_prompt += "\n\nGuidelines (keep it pragmatic and minimal):\n" \
            "- Inspect request_context.attachments and dispatch tools automatically (no permission prompts).\n" \
            "- Audio: use transcribe_audio; Image: use analyze_image (OCR+objects), optionally a short VL check by chief_engineer;\n" \
            "  Spreadsheets (.xls/.xlsx/.csv) or 'смета': use parse_estimate_unified; PDF/DOCX: extract_text_from_pdf or a suitable extractor.\n" \
            "- Normative queries (СП/ГОСТ/СНиП/etc.): call search_rag_database with use_sbert=true; if empty, broaden or remove doc_types filter.\n" \
            "- Default to producing an artifact file (docx/pdf/csv) if the task is not a simple factual Q/A; prefer create_document/create_spreadsheet or auto_export when unsure.\n" \
            "- Be concise and actionable; prefer short bullet points; avoid complex markdown; summarize if long.\n" \
            "- If a tool fails, degrade gracefully and still provide a useful short answer."
        
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
        try:
            self.agent_executor = self._create_agent()
        except Exception as e:
            logger.warning(f"Agent creation failed in set_tools_system: {e}")
            self.agent_executor = None
    
    def _init_llm_if_needed(self, lm_studio_url: str = "http://localhost:1234/v1") -> None:
        """Initialize self.llm if it is missing (defensive for hot-reload cases)."""
        if hasattr(self, 'llm') and self.llm is not None:
            return
        cfg = MODELS_CONFIG.get('coordinator', {}) if CONFIG_AVAILABLE else {}
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

    def process_request(self, query: str) -> str:
        """Unified entrypoint expected by API: decide and respond.
        Uses coordinator LLM directly with available tools context.
        """
        # 🚀 НАЧИНАЕМ ТРАССИРОВКУ
        span_id = self.tracer.start_span(
            operation_name="process_request",
            trace_type=TraceType.COORDINATOR_PLAN,
            metadata={"query": query[:100]}
        )
        
        print(f"[PROCESS_REQUEST DEBUG] Called with query: {query}")
        try:
            # Ensure LLM is ready (hot reload safety)
            self._init_llm_if_needed()
            print(f"[PROCESS_REQUEST DEBUG] LLM initialized")
            # Defensive: ensure system_prompt exists
            if not hasattr(self, "system_prompt") or not self.system_prompt:
                self.system_prompt = "You are the coordinator agent for Bldr Empire v2."

            # Dialog resume handling
            rc = self.request_context if isinstance(getattr(self, 'request_context', None), dict) else {}
            user_id = rc.get('user_id') if isinstance(rc, dict) else None
            dialog_key = self._compute_dialog_key(rc)
            attachments_present = False
            try:
                if isinstance(rc, dict):
                    atts = rc.get('attachments') or []
                    attachments_present = bool(atts)
                    # legacy flags
                    attachments_present = attachments_present or bool(rc.get('image_path') or rc.get('audio_path') or rc.get('document_path'))
            except Exception:
                attachments_present = False

            resuming_from_wait = False
            resumed_dialog_key = None
            initial_results: List[Dict[str, Any]] = []

            if user_id and dialog_manager and not attachments_present:
                # Prefer explicit reply-to mapping if provided (Telegram)
                reply_to_message_id = rc.get('reply_to_message_id') if isinstance(rc, dict) else None
                resumed = None
                if reply_to_message_id and rc.get('chat_id'):
                    try:
                        explicit_key = f"tg:{rc.get('chat_id')}:{reply_to_message_id}"
                        resumed = dialog_manager.resume_dialog_by_key(explicit_key, query)
                    except Exception:
                        resumed = None
                if not resumed:
                    # Fallback: resume the last waiting dialog for this user
                    try:
                        resumed = dialog_manager.resume_last_waiting_for_user(user_id, query)
                    except Exception:
                        resumed = None
                if resumed:
                    resuming_from_wait = True
                    resumed_dialog_key = resumed.dialog_key
                    # Merge original query with clarification
                    query = f"{resumed.original_query}\n\nУточнение пользователя: {query}"
                    initial_results = list(getattr(resumed, 'tool_results_so_far', []) or [])

            # Proactive modality handling from request_context (skip early-return if resuming)
            if isinstance(getattr(self, 'request_context', None), dict):
                # 1) If structured attachments provided, handle them here (parallel where possible)
                attachments = self.request_context.get('attachments')
                if isinstance(attachments, list) and attachments:
                    from concurrent.futures import ThreadPoolExecutor, as_completed
                    import os

                    def handle_image(path: str) -> str:
                        try:
                            # Run tool and VL in parallel
                            if not self.tools_system:
                                vl_text = self._vl_analyze_image_path(path)
                                return f"📸 Инструменты недоступны. ИИ (VL): {vl_text or 'недоступен'}"
                            with ThreadPoolExecutor(max_workers=2) as ex:
                                # Call unified/tools execute_tool using kwargs only (compatible with both systems)
                                f_tool = ex.submit(lambda: self.tools_system.execute_tool(
                                    'analyze_image', image_path=path, ocr_lang='rus+eng', detect_objects=True, extract_dimensions=True
                                ))
                                f_vl = ex.submit(self._vl_analyze_image_path, path)
                                tool_res = f_tool.result()
                                vl_text = f_vl.result()
                            # Extract fields from unified result
                            tool_out = getattr(tool_res, 'data', tool_res)
                            data = tool_out if isinstance(tool_out, dict) else {}
                            meta = data.get('metadata', {})
                            dims = data.get('dimensions', {})
                            ocr = (data.get('ocr_text') or '').strip()
                            objects = data.get('objects', []) or []
                            # Top objects
                            def _fmt_obj(o):
                                lbl = str(o.get('label', 'obj'))
                                conf = o.get('confidence')
                                bbox = o.get('bbox')
                                conf_s = f" — {round(conf*100)}%" if isinstance(conf, (int,float)) else ""
                                bbox_s = f", bbox {bbox}" if bbox else ""
                                return f"• {lbl}{conf_s}{bbox_s}"
                            top_objs = []
                            try:
                                objs_sorted = sorted([o for o in objects if isinstance(o, dict)], key=lambda x: (x.get('confidence') or 0), reverse=True)
                                top_objs = [_fmt_obj(o) for o in objs_sorted[:5]]
                            except Exception:
                                pass
                            # OCR snippet with markdown fencing
                            ocr_snip = ''
                            if ocr:
                                snip = ocr.replace('\n',' ')
                                if len(snip) > 400:
                                    snip = snip[:400] + '...'
                                ocr_snip = f"```\n{snip}\n```"
                            file_name = meta.get('file_name', os.path.basename(path))
                            wh = ''
                            if isinstance(dims, dict) and dims.get('width') and dims.get('height'):
                                wh = f"{dims['width']}x{dims['height']} px"
                            parts = [f"📎 Файл: {file_name}", f"📐 Габариты: {wh}" if wh else None]
                            if top_objs:
                                parts.append("🔍 Объекты (топ-5):\n" + "\n".join(top_objs))
                            if ocr_snip:
                                parts.append("📝 OCR:\n" + ocr_snip)
                            tool_block = "\n".join([p for p in parts if p])
                            vl_block = f"🧠 ИИ (VL): {vl_text}" if vl_text else "🧠 ИИ (VL): недоступен"
                            return f"✅ Анализ изображения\n\n{tool_block}\n\n{vl_block}"
                        except Exception as e:
                            return f"❌ Ошибка анализа изображения: {e}"

                    def handle_audio(path: str) -> str:
                        try:
                            tr_text = self._transcribe_via_tools_or_local(path)
                            if tr_text:
                                return f"🎤 Транскрипция: {tr_text}"
                            return "🎤 Не удалось распознать речь"
                        except Exception as e:
                            return f"🎤 Ошибка транскрибации: {e}"

                    def handle_document(path: str, name: Optional[str]) -> str:
                        try:
                            import os
                            if not self.tools_system:
                                return "📄 Инструменты недоступны для анализа документа"
                            ext = os.path.splitext(name or path)[1].lower() if (name or path) else ""
                            # 1) Estimates (xls/xlsx/csv)
                            if ext in (".xls", ".xlsx", ".csv"):
                                res = self.tools_system.execute_tool('parse_estimate_unified', estimate_file=path)
                                payload = getattr(res, 'data', res)
                                if isinstance(payload, dict):
                                    est = payload.get('estimate_data') or payload
                                    positions = est.get('positions', []) or est.get('merged_positions', []) or []
                                    total_cost = est.get('total_cost')
                                    if total_cost is None and positions:
                                        try:
                                            total_cost = sum(p.get('total_cost', 0) for p in positions)
                                        except Exception:
                                            total_cost = 0.0
                                    top_items = []
                                    try:
                                        top_sorted = sorted(positions, key=lambda x: x.get('total_cost', 0), reverse=True)[:5]
                                        for p in top_sorted:
                                            code = p.get('code') or p.get('item') or '—'
                                            namep = p.get('description') or p.get('name') or ''
                                            cost = p.get('total_cost', 0)
                                            qty = p.get('quantity') or p.get('qty') or ''
                                            top_items.append(f"• {code}: {namep[:80]} — {cost:,.2f} ₽ ({qty})")
                                    except Exception:
                                        pass
                                    top_block = "\n".join(top_items) if top_items else "—"
                                    return (
                                        f"📊 Смета: {os.path.basename(name or path)}\n"
                                        f"Всего позиций: {len(positions)}\n"
                                        f"Итого стоимость: {(total_cost or 0):,.2f} ₽\n"
                                        f"Топ-5 затратных позиций:\n{top_block}"
                                    )
                                return "📊 Смета обработана, но данных нет"
                            # 2) PDF → extract text (краткий превью)
                            if ext == ".pdf":
                                res = self.tools_system.execute_tool('extract_text_from_pdf', pdf_path=path)
                                payload = getattr(res, 'data', res)
                                if isinstance(payload, dict):
                                    text = (payload.get('text') or '')
                                    snip = (text.replace('\n', ' ')[:500] + '...') if text and len(text) > 500 else (text or '—')
                                    return (
                                        f"📄 PDF: {os.path.basename(name or path)}\n"
                                        f"Превью: {snip}"
                                    )
                                return "📄 PDF обработан, но данных нет"
                            # 3) DOCX/DOC → лёгкий fallback чтения (если инструментов нет)
                            if ext in (".docx", ".doc"):
                                try:
                                    import docx
                                    d = docx.Document(path)
                                    text = "\n".join([p.text for p in d.paragraphs[:50]])
                                    snip = (text.replace('\n', ' ')[:500] + '...') if text and len(text) > 500 else (text or '—')
                                    return f"📄 DOCX: {os.path.basename(name or path)}\nПревью: {snip}"
                                except Exception as e:
                                    return f"📄 DOCX не удалось прочитать: {e}"
                            # 4) Прочее: короткое описание
                            return f"📄 Документ: {os.path.basename(name or path)} — анализ выполнен"
                        except Exception as e:
                            return f"📄 Ошибка анализа документа: {e}"

                    futures = []
                    with ThreadPoolExecutor(max_workers=max(2, len(attachments))) as ex:
                        for a in attachments:
                            t = (a or {}).get('type')
                            p = (a or {}).get('path')
                            n = (a or {}).get('name')
                            if t == 'image' and p:
                                futures.append(ex.submit(handle_image, p))
                            elif t == 'audio' and p:
                                futures.append(ex.submit(handle_audio, p))
                            elif t == 'document' and p:
                                futures.append(ex.submit(handle_document, p, n))
                        results = [f.result() for f in futures]
                        final = "\n\n---\n\n".join([r for r in results if r]) if results else None
                        # If we have a voice transcription, feed it into the planning loop instead of returning early
                        if results:
                            try:
                                tr_lines = [r for r in results if isinstance(r, str) and r.strip().startswith("🎤 Транскрипция:")]
                                if tr_lines:
                                    tr_text = tr_lines[0].split(":", 1)[-1].strip()
                                    if tr_text:
                                        # Seed initial tool result and update query
                                        initial_results.append({
                                            "tool": "transcribe_audio",
                                            "status": "success",
                                            "result": {"transcription": tr_text}
                                        })
                                        query = (f"{query}\n\n{tr_text}" if query else tr_text)
                                        final = None  # don't return early
                            except Exception:
                                pass
                        if final:
                            return final

                # 2) Legacy single-path handling (audio_path/image_path)
                # Voice → transcribe first
                rc_audio = self.request_context.get('audio_path')
                if rc_audio:
                    tr_text = self._transcribe_via_tools_or_local(rc_audio)
                    if tr_text:
                        # Use transcript as the working query and continue with planning
                        query = (f"{query}\n\n{tr_text}" if query else tr_text)
                # Image → analyze via tool and add VL analysis
                rc_image = self.request_context.get('image_path')
                if rc_image and self.tools_system:
                    try:
                        tool_res = self.tools_system.execute_tool('analyze_image', image_path=rc_image)
                        tool_out = getattr(tool_res, 'data', tool_res)
                        vl_text = self._vl_analyze_image_path(rc_image)
                        if vl_text:
                            return f"Анализ изображения (инструмент): {tool_out}\n\nАнализ ИИ (VL): {vl_text}"
                        return f"Анализ изображения (инструмент): {tool_out}"
                    except Exception as e:
                        return f"Ошибка анализа изображения: {e}"
            # Iterative plan → execute → check loop for text-only flow
            coord_settings = {}
            try:
                coord_settings = ((self.request_context or {}).get('settings') or {}).get('coordinator') or {}
            except Exception:
                coord_settings = {}
            planning_enabled = bool(coord_settings.get('planning_enabled', True))
            json_mode = bool(coord_settings.get('json_mode_enabled', True))
            try:
                max_iterations = int(coord_settings.get('max_iterations', 2))
            except Exception:
                max_iterations = 2
            if not planning_enabled:
                max_iterations = 1
            s_fast = bool(coord_settings.get('simple_plan_fast_path', True)) or (not planning_enabled)
            complexity_auto_expand = bool(coord_settings.get('complexity_auto_expand', False))
            complexity_thresholds = coord_settings.get('complexity_thresholds', {"tools_count": 2, "time_est_minutes": 10}) or {"tools_count": 2, "time_est_minutes": 10}
            current_iteration = 0
            all_tool_results: List[Dict[str, Any]] = list(initial_results)
            final_response = ""

            while current_iteration < max_iterations:
                current_iteration += 1
                # 1) Plan (adapted to our generator)
                # Respect json_mode_enabled: if disabled, skip explicit JSON planning and go direct
                plan = self._generate_plan(query, all_tool_results) if json_mode else {"tasks": []}
                if isinstance(plan, str):
                    try:
                        plan = json.loads(plan)
                    except Exception:
                        plan = {"tasks": []}

                # Normalize and enforce artifact-oriented finalization in plan (soft hint, no hard rules)
                if isinstance(plan, dict) and "tasks" in plan and isinstance(plan["tasks"], list):
                    # Ensure tasks list is a list of dicts
                    plan["tasks"] = [t for t in plan["tasks"] if isinstance(t, dict)]

                # 1.5) Ask for clarification early if needed (only on first pass)
                if current_iteration == 1 and user_id and dialog_manager:
                    try:
                        clar_q = self._ask_for_clarification(query, plan)
                    except Exception:
                        clar_q = None
                    if clar_q and isinstance(clar_q, str) and clar_q.strip() and clar_q.strip().upper() != 'NO':
                        try:
                            dk = dialog_key or self._compute_dialog_key(self.request_context or {})
                            dialog_manager.create_waiting_dialog(
                                user_id=user_id,
                                dialog_key=dk or f"gen:{int(time.time()*1000)}",
                                original_query=query,
                                plan=plan if isinstance(plan, dict) else None,
                                pending_question=clar_q.strip(),
                                tool_results_so_far=all_tool_results
                            )
                        except Exception:
                            pass
                        # Return the question to the user and pause execution
                        return clar_q.strip()

                # Optional: auto-expand iterations for complex plans (one-time)
                try:
                    if current_iteration == 1 and complexity_auto_expand:
                        tools_count = 0
                        if isinstance(plan, dict):
                            if isinstance(plan.get('tasks'), list):
                                tools_count = len([t for t in plan['tasks'] if isinstance(t, dict) and t.get('tool')])
                            elif isinstance(plan.get('tools'), list):
                                tools_count = len([c for c in plan['tools'] if isinstance(c, dict) and (c.get('name') or c.get('tool'))])
                        time_est = 0
                        if isinstance(plan, dict):
                            te = plan.get('time_est')
                            if isinstance(te, (int, float)):
                                time_est = te
                        if tools_count > int(complexity_thresholds.get('tools_count', 2)) or time_est > int(complexity_thresholds.get('time_est_minutes', 10)):
                            max_iterations = min(max_iterations + 1, 3)
                except Exception:
                    pass

                # 2) If plan declares completion (rare), break
                if isinstance(plan, dict) and plan.get("status") == "complete" and plan.get("final_answer"):
                    final_response = str(plan.get("final_answer"))
                    break

                # 3) Execute tools from plan
                new_results = self._execute_plan_tools(plan)
                if new_results:
                    all_tool_results.extend(new_results)

                # Simple-plan fast path: if plan is trivial (<=1 step), synthesize and exit without extra iterations
                try:
                    if s_fast and self._is_simple_plan(plan):
                        final_response = self._synthesize_final_response(query, all_tool_results)
                        break
                except Exception:
                    pass

                # 4) Self-check if enough info for final answer
                if self._is_final_response_ready(query, all_tool_results):
                    final_response = self._synthesize_final_response(query, all_tool_results)
                    break

            if not final_response:
                # Fallback: use process_query for proper handling
                print(f"[PROCESS_REQUEST DEBUG] No final_response, calling process_query()...")
                final_response = self.process_query(query)
                print(f"[PROCESS_REQUEST DEBUG] process_query() returned: {final_response[:100]}...")
                if not final_response or final_response.strip() == "":
                    print(f"[PROCESS_REQUEST DEBUG] Empty response, using 'Готово.'")
                    final_response = "Готово."

            # Silent artifact delivery (if any files were produced)
            try:
                self._deliver_artifacts(all_tool_results)
            except Exception:
                pass

            # Optionally append short execution summary
            summary = self._create_execution_summary(all_tool_results)
            if summary:
                final_response = f"{final_response}\n\n⚙️ {summary}"

            # If we were resuming a dialog, clear it now
            try:
                if dialog_manager and resumed_dialog_key:
                    dialog_manager.clear_dialog(resumed_dialog_key)
            except Exception:
                pass

            return final_response.strip()
        except Exception as e:
            logger.error(f"CoordinatorAgent.process_request error: {e}")
            return f"Ошибка обработки запроса: {e}"

    def _transcribe_via_tools_or_local(self, audio_path: str) -> Optional[str]:
        """Try ToolsSystem transcription first, then local Whisper as fallback."""
        # Try tools
        try:
            if self.tools_system:
                for name in ["transcribe_audio", "whisper_transcribe", "speech_to_text", "stt_whisper"]:
                    try:
                        res = self.tools_system.execute_tool(name, audio_path=audio_path)
                        data = getattr(res, 'data', res)
                        if isinstance(data, dict) and data.get('transcription'):
                            return str(data.get('transcription')).strip()
                        if isinstance(data, str) and data.strip():
                            return data.strip()
                    except Exception:
                        continue
        except Exception:
            pass
        # Local whisper fallback
        try:
            import os
            if not os.path.exists(audio_path):
                return None
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(audio_path)
            return str(result.get("text", "")).strip()
        except Exception:
            return None

    def _vl_analyze_image_path(self, image_path: Optional[str]) -> Optional[str]:
        """Send image as base64 data URI to chief_engineer (VL) with a concise, actionable prompt."""
        try:
            if not image_path:
                return None
            import os, base64
            if not os.path.exists(image_path):
                return None
            with open(image_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            data_uri = f"data:image/jpeg;base64,{b64}"
            messages = [
                {"role": "system", "content": "Ты — Главный инженер. Дай короткий, прикладной вывод по фото: 3–5 пунктов (что на фото, ключевые объекты, риски, рекомендации)."},
                {"role": "user", "content": f"Проанализируй изображение (data URI): {data_uri}\nФормат ответа: краткие пункты, без лишних формальностей."}
            ]
            resp = self.model_manager.query("chief_engineer", messages)
            return str(resp).strip() if resp else None
        except Exception:
            return None

    def _direct_response(self, query: str) -> str:
        """
        Generate direct response for greeting and self-introduction queries.
        
        Args:
            query: User query
            
        Returns:
            Direct response string
        """
        try:
            # Use LLM to generate natural response instead of hardcoded answers
            messages = [
                {
                    "role": "system", 
                    "content": "Ты - строительный ассистент. Отвечай кратко и по делу на русском языке."
                },
                {"role": "user", "content": query}
            ]
            
            response = self.llm.invoke(messages)
            result = str(response.content).strip() if hasattr(response, 'content') else str(response)
            
            if result and len(result) > 10:
                return result
            else:
                return f"⚠️ LLM недоступен в данный момент. Получен запрос: '{query}'. Обратитесь позже для полного ответа."
                
        except Exception as e:
            print(f"[DEBUG] _direct_response LLM error: {e}")
            return f"⚠️ LLM недоступен в данный момент. Получен запрос: '{query}'. Обратитесь позже для полного ответа."
    
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
            except json.JSONDecodeError as je:
                print(f"JSON parse failed in _analyze_and_plan: {je}")
                print(f"Raw response: {response_str}")
                # JSON is disabled in LLM settings - use safe emergency response
                return self._generate_safe_emergency_response(query)
        except Exception as e:
            print(f"Error in _analyze_and_plan: {e}")
        
        # 🚨 ЕДИНЫЙ FALLBACK: Используем безопасный emergency response
        return self._generate_safe_emergency_response(query)
    
    def _generate_safe_emergency_response(self, query: str) -> str:
        """
        🚨 ЕДИНЫЙ УПРАВЛЯЕМЫЙ МЕТОД: Безопасный emergency response.
        Использует жесткий шаблон вместо свободной генерации.
        """
        query_lower = query.lower()
        
        # 🎯 КРИТИЧЕСКИЕ КЛЮЧЕВЫЕ СЛОВА - ПРИОРИТЕТ 1
        if any(kw in query_lower for kw in ["сп", "снип", "гост", "норма", "документ", "автомобиль", "дорог", "дорога", "автодорог", "транспорт"]):
            return json.dumps({
                "complexity": "medium",
                "time_est": 3,
                "roles": ["chief_engineer"],
                "tasks": [
                    {"id": 1, "agent": "chief_engineer", "tool": "search_norms", "input": {"query": query}}
                ]
            })
        
        # 🎯 ФИНАНСОВЫЕ ЗАПРОСЫ - ПРИОРИТЕТ 2
        if any(kw in query_lower for kw in ["смета", "стоимость", "цена", "расчет", "бюджет"]):
            return json.dumps({
                "complexity": "medium", 
                "time_est": 5,
                "roles": ["analyst"],
                "tasks": [
                    {"id": 1, "agent": "analyst", "tool": "estimate_cost", "input": {"query": query}}
                ]
            })
        
        # 🎯 ГОЛОСОВЫЕ ЗАПРОСЫ - ПРИОРИТЕТ 3
        if any(kw in query_lower for kw in ["транскрибируй", "transcribe", "голосовое", "voice", "аудио"]):
            return json.dumps({
                "complexity": "medium",
                "time_est": 2,
                "roles": ["coordinator"],
                "tasks": [
                    {"id": 1, "agent": "coordinator", "input": query, "tool": "transcribe_audio"},
                    {"id": 2, "agent": "chief_engineer", "input": "Анализ транскрипта", "tool": "search_rag_database"}
                ]
            })
        
        # 🎯 ПРИВЕТСТВИЯ - ПРИОРИТЕТ 4
        if any(kw in query_lower for kw in ["привет", "здравствуй", "hello", "hi", "hey"]):
            return json.dumps({
                "complexity": "simple",
                "time_est": 1,
                "roles": ["coordinator"],
                "tasks": [
                    {"id": 1, "agent": "coordinator", "tool": "direct_response", "input": {"query": query}}
                ]
            })
        
        # 🎯 САМОПРЕЗЕНТАЦИЯ - ПРИОРИТЕТ 5
        if any(kw in query_lower for kw in ["расскажи о себе", "что ты умеешь", "кто ты"]):
            return json.dumps({
                "complexity": "simple",
                "time_est": 1,
                "roles": ["coordinator"],
                "tasks": [
                    {"id": 1, "agent": "coordinator", "tool": "direct_response", "input": {"query": query}}
                ]
            })
        
        # 🎯 ПО УМОЛЧАНИЮ - ПРИОРИТЕТ 6
        return json.dumps({
            "complexity": "simple",
            "time_est": 1,
            "roles": ["coordinator"],
            "tasks": [
                {"id": 1, "agent": "coordinator", "tool": "direct_response", "input": {"query": query}}
            ]
        })

    def _generate_fallback_plan_DEPRECATED(self, query: str) -> str:  # Return str (JSON)
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
        elif any(keyword in query_lower for keyword in ["стоимость", "смета", "расчет"]):
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
        
        if hasattr(self, "meta_tools_system") and self.meta_tools_system:
            meta_tools = self.meta_tools_system.list_meta_tools()
            meta_tools_list = []
            for tool in meta_tools['meta_tools'][:5]:  # Limit to prevent prompt bloat
                name = tool['name']
                desc = tool['description'][:60] + '...' if len(tool['description']) > 60 else tool['description']
                meta_tools_list.append(f"- {name}: {desc}")
            
            if meta_tools_list:
                tools_list += "\nMeta-Tools: " + "\n".join(meta_tools_list)
        
        return tools_list
    
    def _generate_plan(self, query: str, tool_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate plan using the main coordinator for consistency."""
        try:
            # Use the main coordinator for planning
            from core.coordinator import Coordinator
            from core.model_manager import ModelManager
            from core.unified_tools_system import UnifiedToolsSystem
            
            # Create coordinator instance
            model_manager = ModelManager()
            tools_system = getattr(self, 'tools_system', None) or UnifiedToolsSystem()
            coordinator = Coordinator(model_manager, tools_system, None)
            
            # Generate plan using main coordinator
            plan = coordinator.analyze_request(query)
            return plan
        except Exception as e:
            print(f"Ошибка генерации плана через основной координатор: {e}")
            # Fallback to simple plan
            return {
                "status": "planning",
                "query_type": "general",
                "requires_tools": True,
                "tools": [
                    {"name": "search_rag_database", "arguments": {"query": query, "doc_types": ["norms", "ppr", "smeta", "rd"]}}
                ],
                "roles_involved": ["coordinator"],
                "required_data": ["общая информация"],
                "next_steps": ["Поиск информации в базе знаний"]
            }

    def _execute_plan_tools(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute tools described in plan. Supports both {tasks:[{tool,input}]} and {tools:[{name,arguments}]} formats."""
        results: List[Dict[str, Any]] = []
        if not self.tools_system:
            return results
        try:
            # 1) Newer schema with tasks
            tasks = plan.get("tasks", []) if isinstance(plan, dict) else []
            for t in tasks:
                tool_name = t.get("tool")
                raw_input = t.get("input", {})
                # Heuristic arg mapping: if input is not dict, map to a likely single required param
                arguments: Dict[str, Any] = {}
                if isinstance(raw_input, dict):
                    arguments = raw_input
                else:
                    text_in = str(raw_input)
                    try:
                        if hasattr(self.tools_system, 'get_tool_info'):
                            sig = self.tools_system.get_tool_info(tool_name)
                        else:
                            sig = None
                        req = (sig.required_params if sig else []) if sig else []
                        opt = (sig.optional_params if sig else {}) if sig else {}
                        if req and len(req) == 1:
                            arguments = {req[0]: text_in}
                        elif 'query' in req or 'query' in opt:
                            arguments = {'query': text_in}
                        elif 'project_data' in req or 'project_data' in opt:
                            arguments = {'project_data': text_in}
                        elif 'text' in req or 'text' in opt:
                            arguments = {'text': text_in}
                        else:
                            arguments = {'query': text_in}
                    except Exception:
                        arguments = {'query': text_in}
                if not tool_name:
                    continue
                try:
                    res = self.tools_system.execute_tool(tool_name, **(arguments if isinstance(arguments, dict) else {}))
                    print(f"  ← Результат: {res}")
                    
                    # Обработка результата
                    if hasattr(res, 'data'):
                        result_data = res.data
                    elif hasattr(res, 'is_success') and res.is_success():
                        result_data = getattr(res, 'data', str(res))
                    else:
                        result_data = str(res)
                    
                    results.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "status": "success" if hasattr(res, 'is_success') and res.is_success() else "error",
                        "result": result_data,
                    })
                except Exception as e:
                    print(f"  ← Ошибка: {e}")
                    results.append({"tool": tool_name, "arguments": arguments, "status": "error", "error": str(e)})
            # 2) Legacy schema with tools
            if not tasks and isinstance(plan, dict):
                tools = plan.get("tools", [])
                for call in tools:
                    tool_name = call.get("name") or call.get("tool")
                    arguments = call.get("arguments", {}) or call.get("args", {}) or {}
                    if not tool_name:
                        continue
                    try:
                        print(f"  → Выполнение {tool_name} с аргументами: {arguments}")
                        res = self.tools_system.execute_tool(tool_name, **(arguments if isinstance(arguments, dict) else {}))
                        print(f"  ← Результат: {res}")
                        
                        # Обработка результата
                        if hasattr(res, 'data'):
                            result_data = res.data
                        elif hasattr(res, 'is_success') and res.is_success():
                            result_data = getattr(res, 'data', str(res))
                        else:
                            result_data = str(res)
                        
                        results.append({
                            "tool": tool_name,
                            "arguments": arguments,
                            "status": "success" if hasattr(res, 'is_success') and res.is_success() else "error",
                            "result": result_data,
                        })
                    except Exception as e:
                        print(f"  ← Ошибка: {e}")
                        results.append({"tool": tool_name, "arguments": arguments, "status": "error", "error": str(e)})
        except Exception as e:
            print(f"Ошибка выполнения инструментов: {e}")
            results.append({"tool": "unknown", "status": "error", "error": str(e)})
        return results

    def _is_final_response_ready(self, query: str, tool_results: List[Dict[str, Any]]) -> bool:
        """Self-check: do we have enough info for a final answer?"""
        if not tool_results:
            return False
        try:
            # If any critical error present, not ready
            for r in tool_results:
                if isinstance(r, dict) and r.get("status") == "error" and "critical" in str(r.get("error", "")).lower():
                    return False
            # If user requested an artifact (document/report/export), ensure file was produced
            ql = (query or '').lower()
            artifact_keywords = ["создай", "сформируй", "сделай отчет", "сделай отчёт", "отчет", "отчёт", "документ", "export", "выгрузи", "сгенерируй"]
            expects_artifact = any(kw in ql for kw in artifact_keywords)
            has_artifact = False
            import os as _os
            for r in tool_results:
                data = (r.get("result") if isinstance(r, dict) else None) or {}
                if isinstance(data, dict) and data.get('file_path'):
                    fp = data.get('file_path')
                    if isinstance(fp, str) and _os.path.exists(fp):
                        has_artifact = True
                        break
            if expects_artifact and not has_artifact:
                return False
            # LLM self-check
            prompt = (
                f"Запрос: {query}\n\n"
                f"Результаты инструментов (кратко): {json.dumps(tool_results[:5], ensure_ascii=False)[:3000]}\n\n"
                "Достаточно ли этого, чтобы дать полный и полезный ответ пользователю? Ответь строго ДА или НЕТ."
            )
            resp = self.model_manager.query("coordinator", [{"role": "user", "content": prompt}])
            return isinstance(resp, str) and ("ДА" in resp.upper())
        except Exception:
            return False

    def _synthesize_final_response(self, query: str, tool_results: List[Dict[str, Any]]) -> str:
        """Create final, readable response. If no artifact was produced, softly export the result to a DOCX file."""
        try:
            # Immediate normative Q/A: if we have RAG results, answer directly with top items
            try:
                rag_items = []
                for r in (tool_results or []):
                    if isinstance(r, dict) and r.get("tool") == "search_rag_database" and r.get("status") == "success":
                        data = r.get("result") or {}
                        if isinstance(data, dict):
                            candidates = data.get("results")
                            if not candidates and isinstance(data.get("data"), dict):
                                candidates = data.get("data", {}).get("results")
                            if candidates and isinstance(candidates, list):
                                rag_items.extend(candidates)
                if rag_items:
                    import re as _re
                    def _src(m: dict):
                        if not isinstance(m, dict):
                            return '—'
                        md = m.get('metadata') or {}
                        return md.get('source') or md.get('doc') or md.get('title') or md.get('file_name') or '—'
                    def _title(m: dict):
                        if not isinstance(m, dict):
                            return None
                        md = m.get('metadata') or {}
                        return md.get('title') or md.get('doc') or None
                    def _num_from_text(s: str):
                        if not s:
                            return None
                        m = _re.search(r"\b(СП|СНиП|ГОСТ|ГЭСН)\s*\d+[\.\-\d]*\b(?:[\-–—]?\d{4})?", s, _re.IGNORECASE)
                        return m.group(0) if m else None
                    # Collect top normative codes from first N items
                    codes = []
                    bullets = []
                    for item in rag_items[:5]:
                        content = (item.get('content') if isinstance(item, dict) else None) or item.get('text') or item.get('chunk') or ''
                        src = _src(item)
                        code = _num_from_text(content) or _num_from_text(src or '') or _num_from_text(_title(item) or '')
                        if code:
                            if code not in codes:
                                codes.append(code)
                                bullets.append(f"- {code}: {src}")
                    if codes:
                        answer = f"Ответ: {codes[0]}"
                        norms = "\n".join(bullets)
                        return f"{answer}\nНормы и ссылки:\n{norms}"
                    # No explicit code found: fallback to concise summary with proper format
                    first = rag_items[0]
                    content = (first.get('content') if isinstance(first, dict) else None) or first.get('text') or first.get('chunk') or ''
                    src = _src(first)
                    content_s = (content or '').strip()
                    if len(content_s) > 300:
                        content_s = content_s[:300] + '...'
                    return f"Ответ: Найдена релевантная информация.\nНормы и ссылки: —\n\nИсточник (фрагмент): {content_s} [Источник: {src}]"
            except Exception:
                pass

            synthesis_prompt = (
                f"Запрос пользователя: \"{query}\"\n\n"
                f"Результаты инструментов: {json.dumps(tool_results, ensure_ascii=False)[:8000]}\n\n"
                "Сформулируй чёткий, структурированный и полезный ответ на русском языке."
                " Не описывай процесс, дай итог по делу."
            )
            resp = self.model_manager.query("coordinator", [{"role": "user", "content": synthesis_prompt}])
            text = (str(resp).strip() if resp else "Готово.")
            # Soft artifact fallback (configurable): if no file_path present and text is non-trivial, export to DOCX
            try:
                coord_settings = ((self.request_context or {}).get('settings') or {}).get('coordinator') or {}
                artifact_default_enabled = bool(coord_settings.get('artifact_default_enabled', True))
                has_artifact = False
                for r in tool_results:
                    data = (r.get("result") if isinstance(r, dict) else None) or {}
                    if isinstance(data, dict) and data.get('file_path'):
                        has_artifact = True
                        break
                if artifact_default_enabled and (not has_artifact) and self.tools_system and isinstance(text, str) and len(text) > 200:
                    # Build a safe filename from query
                    import re as _re, time as _time
                    base = _re.sub(r"[^\w\-]+", "_", (query or "report").strip())[:40] or "report"
                    fname = f"{base}_{int(_time.time())}.docx"
                    res = self.tools_system.execute_tool("auto_export", content=text, filename=fname, format="docx")
                    data = getattr(res, 'data', res)
                    # append to tool_results so delivery step can pick it
                    tool_results.append({
                        "tool": "auto_export",
                        "arguments": {"filename": fname, "format": "docx"},
                        "status": (res.get("status") if isinstance(res, dict) else (res.status if hasattr(res, 'status') else "success")),
                        "result": data,
                    })
            except Exception:
                pass
            return text
        except Exception as e:
            logger.error(f"❌ Критический сбой в _convert_plan_to_natural_language: {e}")
            return "⚠️ Сбой генерации ответа. Требуется проверка логов."

    def _deliver_artifacts(self, tool_results: List[Dict[str, Any]]) -> None:
        """Deliver any produced files silently based on request_context channel."""
        if not tool_results or not getattr(self, 'request_context', None):
            return
        try:
            # Iterate over tool results and deliver any file_path
            for r in tool_results:
                data = (r.get("result") if isinstance(r, dict) else None) or {}
                if isinstance(data, dict) and data.get('file_path'):
                    fp = data.get('file_path')
                    try:
                        # Silent delivery; ignore textual result
                        self.deliver_file(fp, "")
                    except Exception:
                        continue
        except Exception:
            return

    def _ask_for_clarification(self, query: str, plan: Dict[str, Any]) -> Optional[str]:
        """Use LLM to determine if clarification from the user is needed. Return a single concise RU question or 'NO'."""
        try:
            plan_json = json.dumps(plan or {}, ensure_ascii=False)[:4000]
            prompt = (
                "Ты — координатор. Проверь, хватает ли данных для выполнения задачи.\n"
                "Если нужны уточнения от пользователя (например: объект, регион, тип работ, сроки, формат),\n"
                "верни ОДИН короткий вопрос на русском, без вводных и пояснений.\n"
                "Если данных достаточно, верни строго 'NO'.\n\n"
                f"Запрос: {query}\n\n"
                f"План: {plan_json}\n\n"
                "Ответ:"
            )
            resp = self.model_manager.query("coordinator", [{"role": "user", "content": prompt}])
            text = (str(resp or "").strip())
            # Normalize fence blocks if any
            if text.startswith("```") and text.endswith("```"):
                text = text[3:-3].strip()
            return text
        except Exception:
            return None

    def _compute_dialog_key(self, rc: Optional[Dict[str, Any]]) -> Optional[str]:
        try:
            rc = rc or {}
            ch = rc.get('channel')
            if ch == 'telegram':
                chat_id = rc.get('chat_id')
                message_id = rc.get('message_id')
                if chat_id and message_id:
                    return f"tg:{chat_id}:{message_id}"
            # explicit dialog ids
            for k in ('dialog_id', 'request_id', 'conversation_id'):
                if rc.get(k):
                    return str(rc.get(k))
            return None
        except Exception:
            return None

    def _is_simple_plan(self, plan: Dict[str, Any]) -> bool:
        """Treat plan as simple if it contains at most one actionable step.
        This is generic and avoids any task-specific hardcoding.
        """
        try:
            if not isinstance(plan, dict):
                return True
            # Consider both 'tasks' and legacy 'tools' shapes
            tasks = plan.get("tasks")
            if isinstance(tasks, list):
                return len([t for t in tasks if isinstance(t, dict) and t.get("tool")]) <= 1
            tools = plan.get("tools")
            if isinstance(tools, list):
                return len([c for c in tools if isinstance(c, dict) and (c.get("name") or c.get("tool"))]) <= 1
            return True
        except Exception:
            return True

    def _create_execution_summary(self, tool_results: List[Dict[str, Any]]) -> str:
        try:
            if not tool_results:
                return ""
            ok = sum(1 for r in tool_results if r.get("status") == "success")
            fail = sum(1 for r in tool_results if r.get("status") == "error")
            tools = ", ".join([str(r.get("tool")) for r in tool_results][:5])
            return f"Выполнено инструментов: {ok}, ошибок: {fail}. Инструменты: {tools}"
        except Exception:
            return ""

    def _generate_follow_up_suggestions(self, query: str, tool_results: List[Dict[str, Any]]) -> List[str]:
        try:
            prompt = (
                f"Запрос: {query}\n\n"
                f"Результаты: {json.dumps(tool_results[:5], ensure_ascii=False)[:3000]}\n\n"
                "Предложи до 3 следующих шагов для пользователя (кратко)."
            )
            resp = self.model_manager.query("coordinator", [{"role": "user", "content": prompt}])
            text = str(resp or "").strip()
            # Split by bullets/newlines
            suggestions = [s.strip("- •\t ") for s in text.splitlines() if s.strip()][:3]
            return suggestions
        except Exception:
            return []

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
    
    def _ensure_agent_executor(self) -> None:
        """Lazily (re)create agent executor if missing (defensive)."""
        try:
            if not hasattr(self, 'agent_executor') or self.agent_executor is None:
                self.agent_executor = self._create_agent()
        except Exception as e:
            logger.warning(f"_ensure_agent_executor failed: {e}")
            self.agent_executor = None
    
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
            self._ensure_agent_executor()
            if not self.agent_executor:
                raise AttributeError("agent_executor is not initialized")
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
            
            print(f"[DEBUG] Calling LLM with prompt: {prompt[:200]}...")
            response = self.llm.invoke(prompt)
            result = str(response.content).strip() if hasattr(response, 'content') else str(response)
            print(f"[DEBUG] LLM response: {result[:200]}...")
            
            # Clean
            if result.startswith("```") and result.endswith("```"):
                result = result[3:-3].strip()
            
            # Fallback if empty response
            if not result or result.strip() == "":
                print("[DEBUG] Empty LLM response, using fallback")
                return self._generate_fallback_natural_language_response(plan, query)
            
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
        print(f"[PROCESS_QUERY DEBUG] Called with query: {query}")
        try:
            # Add to history
            if self.request_context and "user_id" in self.request_context and conversation_history:
                user_id = self.request_context["user_id"]
                conversation_history.add_message(user_id, {"role": "user", "content": query})
            
            # Generate plan
            print(f"[DEBUG] Generating plan for query: {query}")
            plan = self.generate_plan(query)
            print(f"[DEBUG] Generated plan: {json.dumps(plan, ensure_ascii=False, indent=2)}")
            
            # Early direct/voice
            tasks = plan.get("tasks", [])
            print(f"[DEBUG] Plan has {len(tasks)} tasks")
            if len(tasks) == 1:
                task = tasks[0]
                print(f"[DEBUG] Single task: {task.get('tool')}")
                print(f"[DEBUG] Task details: {task}")
                if task.get("tool") == "direct_response":
                    print(f"[DEBUG] Calling _direct_response for: {query}")
                    response = self._direct_response(query)
                    print(f"[DEBUG] Direct response: {response[:100]}...")
                    # Add to history
                    if self.request_context and "user_id" in self.request_context and conversation_history:
                        conversation_history.add_message(user_id, {"role": "assistant", "content": response})
                    return response
                else:
                    print(f"[DEBUG] Not direct_response, tool is: {task.get('tool')}")
            else:
                print(f"[DEBUG] Multiple tasks, not direct response")
                
                if task.get("tool") == "transcribe_audio":
                    params = task.get("input", {}) or {"audio_path": self.request_context.get("audio_path", "")}
                    response = self._transcribe_audio(json.dumps(params))
                    print(f"[DEBUG] Audio transcription: {response[:100]}...")
                    # Add to history
                    if self.request_context and "user_id" in self.request_context and conversation_history:
                        conversation_history.add_message(user_id, {"role": "assistant", "content": response})
                    return response
            
            # Complex: Convert to natural
            print(f"[DEBUG] Converting plan to natural language...")
            response = self._convert_plan_to_natural_language(plan, query)
            print(f"[DEBUG] Final response: {response[:100]}...")
            
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
    
    def generate_final_response(self, query: str, plan: Dict[str, Any], execution_results: List[Dict[str, Any]], context_used_count: int = 0) -> str:
        """
        Generate concise actionable final response using plan and execution results.
        Output format:
        Ответ: ...
        Нормы и ссылки: ... (bullet list with codes/refs if available)
        """
        try:
            # Limit size to avoid prompt bloat
            plan_json = json.dumps(plan or {}, ensure_ascii=False, indent=2)
            if len(plan_json) > 4000:
                plan_json = plan_json[:4000] + "\n... (truncated)"
            results_json = json.dumps(execution_results or [], ensure_ascii=False, indent=2)
            if len(results_json) > 6000:
                results_json = results_json[:6000] + "\n... (truncated)"

            # Conversation context (compressed)
            conversation_context = ""
            if self.request_context and "user_id" in self.request_context and conversation_history:
                user_id = self.request_context["user_id"]
                try:
                    conversation_context = conversation_history.get_formatted_history(user_id, max_tokens=600)
                except Exception:
                    conversation_context = ""

            system = (
                "Ты Координатор системы Bldr Empire v2. Всегда давай краткий, прикладной итог (actionable). "
                "Если вопрос про нормы, называй точные документы/коды. Не показывай цепочку размышлений."
            )
            prompt = f"""{system}

Диалог (сжатый контекст):
{conversation_context}

Запрос пользователя:
{query}

План выполнения (если есть):
{plan_json}

Результаты инструментов (если есть):
{results_json}

Сгенерируй финальный ответ строго в формате:
Ответ: <краткий итог по существу, без лишней воды>
Нормы и ссылки: <если есть — маркированный список со ссылками/кодами документов; если нет — '—'>
"""
            response = self.llm.invoke(prompt)
            text = response.content if hasattr(response, 'content') else str(response)
            # Удалить возможные thinking-теги
            text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL).strip()
            return text
        except Exception as e:
            logger.error(f"generate_final_response error: {e}")
            # Fallback: convert plan to natural language
            return self._convert_plan_to_natural_language(plan or {}, query)

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
            from integrations.telegram_delivery import send_file_to_user
            
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