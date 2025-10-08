"""Model management system for Bldr Empire v2 with role-based agents"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, List
from functools import lru_cache
import hashlib
from datetime import datetime, timedelta

# Try to import optional dependencies with proper error handling
OLLAMA_AVAILABLE = False
try:
    import ollama
    OLLAMA_AVAILABLE = True
    logging.info("Ollama client successfully imported")
except ImportError as e:
    logging.warning(f"Ollama not available: {e}")

EZDXF_AVAILABLE = False
try:
    import ezdxf
    EZDXF_AVAILABLE = True
    logging.info("ezdxf successfully imported")
except ImportError as e:
    logging.warning(f"ezdxf not available: {e}")

IFCOPENSHELL_AVAILABLE = False
try:
    import ifcopenshell
    IFCOPENSHELL_AVAILABLE = True
    logging.info("ifcopenshell successfully imported")
except ImportError as e:
    logging.warning(f"ifcopenshell not available: {e}")

TORCH_AVAILABLE = False
try:
    import torch
    TORCH_AVAILABLE = True
    logging.info("torch successfully imported")
except ImportError as e:
    logging.warning(f"torch not available: {e}")

SCIPY_AVAILABLE = False
try:
    import scipy
    SCIPY_AVAILABLE = True
    logging.info("scipy successfully imported")
except ImportError as e:
    logging.warning(f"scipy not available: {e}")

DOCX2PDF_AVAILABLE = False
try:
    pass
except ImportError as e:
    logging.warning(f"docx2pdf not available: {e}")

# Import configuration
from core.config import MODELS_CONFIG, get_capabilities_prompt

# Path to shared runtime settings (same as main.py settings.json)
import os as _os
_SETTINGS_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), 'settings.json')

def _load_settings_json() -> Dict[str, Any]:
    try:
        if _os.path.exists(_SETTINGS_PATH):
            import json as _json
            with open(_SETTINGS_PATH, 'r', encoding='utf-8') as f:
                return _json.load(f) or {}
    except Exception:
        return {}
    return {}

def _get_role_override(role: str) -> Dict[str, Any]:
    try:
        data = _load_settings_json()
        overrides = data.get('models_overrides') or {}
        ov = overrides.get(role) or {}
        if isinstance(ov, dict):
            return ov
        return {}
    except Exception:
        return {}

def _merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(base, dict):
        base = {}
    if not isinstance(override, dict):
        override = {}
    merged = dict(base)
    for k, v in override.items():
        # Allow only known fields to avoid accidental pollution
        if k in ('model', 'base_url', 'temperature', 'max_tokens', 'timeout') and v not in (None, ''):
            merged[k] = v
    return merged

class ModelManager:
    """Enhanced ModelManager with role-based configuration and self-aware agents"""
    
    def __init__(self, cache_size: int = 3, ttl_minutes: int = 5):
        """
        Initialize ModelManager with strict memory management.
        
        Args:
            cache_size: Maximum number of models to cache (default: 3 - только координатор + 2 других)
            ttl_minutes: Time-to-live for cached models in minutes (default: 5 - быстро выгружаем)
        """
        self.cache_size = cache_size
        self.ttl_minutes = ttl_minutes
        self.model_cache: Dict[str, Dict[str, Any]] = {}
        self.last_access: Dict[str, datetime] = {}
        self.active_models: List[str] = []  # Порядок использования моделей
        
        # Preload only coordinator
        self._preload_priority_models()
    
    def _preload_priority_models(self):
        """Preload only coordinator to save memory."""
        print("Предзагрузка приоритетных моделей...")
        
        # Загружаем только координатора для экономии памяти
        if "coordinator" in MODELS_CONFIG:
            config = MODELS_CONFIG["coordinator"]
            try:
                print(f"Загрузка модели {config['model']} для роли coordinator с base_url {config['base_url']}")
                client = self.get_model_client("coordinator")
                if client:
                    print(f"OK: Предзагружена модель для роли coordinator")
                else:
                    print(f"FAIL: Не удалось загрузить модель для роли coordinator")
            except Exception as e:
                print(f"FAIL: Ошибка при загрузке модели для роли coordinator: {e}")
        
        print("Предзагрузка завершена")
    
    def get_model_client(self, role: str) -> Optional[Any]:
        """
        Get model client for specific role with strict memory management.
        
        Args:
            role: Role name (e.g., 'coordinator', 'chief_engineer')
            
        Returns:
            Model client or None if not available
        """
        # Check if role exists in configuration
        if role not in MODELS_CONFIG:
            logging.warning(f"Role {role} not found in MODELS_CONFIG")
            return None
            
        # Merge config with runtime override (from settings.json)
        base_cfg = MODELS_CONFIG[role]
        override = _get_role_override(role)
        config = _merge_config(base_cfg, override)
        cache_key = f"{role}_{config.get('base_url')}_{config.get('model')}"
        
        # Check cache first
        if cache_key in self.model_cache:
            cached_entry = self.model_cache[cache_key]
            if datetime.now() - self.last_access[cache_key] < timedelta(minutes=self.ttl_minutes):
                # Обновляем порядок использования
                if cache_key in self.active_models:
                    self.active_models.remove(cache_key)
                self.active_models.append(cache_key)
                self.last_access[cache_key] = datetime.now()
                return cached_entry['client']
            else:
                # Remove expired entry
                self._unload_model(cache_key)
        
        # Проверяем лимит памяти - выгружаем старые модели
        self._enforce_memory_limit()
        
        # Если это не координатор, выгружаем все остальные модели
        if role != "coordinator":
            self._unload_non_coordinator_models()
        
        try:
            # Import LangChain components
            from langchain_openai import ChatOpenAI
            
            # For local models via LM Studio, we don't need an API key
            os.environ["OPENAI_API_KEY"] = "not-needed"
            
            client = ChatOpenAI(
                model=config['model'],
                temperature=config['temperature'],
                max_tokens=config['max_tokens'],
                base_url=config['base_url'],
                timeout=config.get('timeout', 30.0)
            )
            
            # Cache the client
            self.model_cache[cache_key] = {
                'client': client,
                'config': config,
                'created_at': datetime.now()
            }
            self.last_access[cache_key] = datetime.now()
            
            return client
            
        except Exception as e:
            logging.error(f"Failed to create model client for role {role}: {e}")
            return None
    
    def query(self, role: str, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Query model with role-specific configuration.
        
        Args:
            role: Role name
            messages: List of message dictionaries
            **kwargs: Additional arguments for the model
            
        Returns:
            Model response as string
        """
        client = self.get_model_client(role)
        if not client:
            return f"Error: Model client for role {role} not available"
        
        try:
            # Add system prompt with capabilities
            system_prompt = get_capabilities_prompt(role)
            if system_prompt:
                messages = [{"role": "system", "content": system_prompt}] + messages
            
            response = client.invoke(messages, **kwargs)
            if hasattr(response, 'content'):
                return str(response.content)
            else:
                return str(response)
        except Exception as e:
            logging.error(f"Error querying model for role {role}: {e}")
            return f"Error querying model: {str(e)}"
    
    def get_capabilities_prompt(self, role: str) -> Optional[str]:
        """
        Get capabilities prompt for specific role.
        """
        return get_capabilities_prompt(role)
    
    def get_role_responsibilities(self, role: str) -> List[str]:
        if role in MODELS_CONFIG:
            return MODELS_CONFIG[role].get('responsibilities', [])
        return []
    
    def get_role_exclusions(self, role: str) -> List[str]:
        if role in MODELS_CONFIG:
            return MODELS_CONFIG[role].get('exclusions', [])
        return []
    
    def get_role_tools(self, role: str) -> List[str]:
        role_tool_mapping = {
            "coordinator": ["search_rag_database", "gen_docx"],
            "chief_engineer": ["search_rag_database", "vl_analyze_photo", "gen_diagram"],
            "structural_geotech_engineer": ["search_rag_database", "calc_estimate", "gen_excel"],
            "project_manager": ["search_rag_database", "gen_gantt", "gen_project_plan"],
            "construction_safety": ["search_rag_database", "vl_analyze_photo", "gen_safety_report"],
            "qc_compliance": ["search_rag_database", "gen_qc_report", "gen_checklist"],
            "analyst": ["search_rag_database", "calc_estimate", "gen_excel"],
            "tech_coder": ["search_rag_database", "bim_code_gen", "gen_script"]
        }
        return role_tool_mapping.get(role, [])
    
    def get_model_stats(self) -> Dict[str, Any]:
        return {
            "loaded_models": len(self.model_cache),
            "max_cache_size": self.cache_size,
            "ttl_minutes": self.ttl_minutes,
            "model_details": {
                role: {
                    "usage_stats": {
                        "call_count": self._get_model_call_count(role),
                        "last_access": str(self.last_access.get(f"{role}_{MODELS_CONFIG[role]['base_url']}_{MODELS_CONFIG[role]['model']}", "Never"))
                    }
                } for role in MODELS_CONFIG.keys()
            }
        }
    
    def get_all_roles(self) -> List[str]:
        return list(MODELS_CONFIG.keys())
    
    def _get_model_call_count(self, role: str) -> int:
        base_cfg = MODELS_CONFIG.get(role, {})
        ov = _get_role_override(role)
        cfg = _merge_config(base_cfg, ov)
        cache_key = f"{role}_{cfg.get('base_url')}_{cfg.get('model')}"
        return len([key for key in self.last_access.keys() if key.startswith(role)])
    
    def _enforce_memory_limit(self):
        """Строгое соблюдение лимита памяти - выгружаем старые модели."""
        while len(self.model_cache) >= self.cache_size:
            if not self.active_models:
                break
            # Выгружаем самую старую модель
            oldest_model = self.active_models.pop(0)
            self._unload_model(oldest_model)
    
    def _unload_non_coordinator_models(self):
        """Выгружаем все модели кроме координатора для экономии памяти."""
        coordinator_keys = [key for key in self.model_cache.keys() if key.startswith("coordinator_")]
        other_keys = [key for key in self.model_cache.keys() if not key.startswith("coordinator_")]
        
        for key in other_keys:
            self._unload_model(key)
    
    def _unload_model(self, cache_key: str):
        """Выгружаем конкретную модель из памяти."""
        if cache_key in self.model_cache:
            print(f"🗑️ Выгружаем модель из памяти: {cache_key}")
            del self.model_cache[cache_key]
            if cache_key in self.last_access:
                del self.last_access[cache_key]
            if cache_key in self.active_models:
                self.active_models.remove(cache_key)
    
    def force_cleanup(self):
        """Принудительная очистка всех моделей кроме координатора."""
        print("🧹 Принудительная очистка памяти (кроме координатора)...")
        coordinator_keys = [key for key in self.model_cache.keys() if key.startswith("coordinator_")]
        
        # Сохраняем только координатора
        new_cache = {}
        new_access = {}
        new_active = []
        
        for key in coordinator_keys:
            if key in self.model_cache:
                new_cache[key] = self.model_cache[key]
            if key in self.last_access:
                new_access[key] = self.last_access[key]
            if key in self.active_models:
                new_active.append(key)
        
        self.model_cache = new_cache
        self.last_access = new_access
        self.active_models = new_active
        
        print(f"✅ Очистка завершена. Осталось моделей: {len(self.model_cache)}")

    def clear_all_models(self):
        """Полная очистка кеша моделей (включая координатора)."""
        print("🧹 Полная очистка кеша моделей...")
        self.model_cache.clear()
        self.last_access.clear()
        self.active_models.clear()
        print("✅ Полная очистка завершена. Кеш пуст.")

# Global instance
model_manager = ModelManager()
