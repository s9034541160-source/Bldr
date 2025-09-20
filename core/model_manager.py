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
    # This import might not be available, so we'll handle it gracefully
    pass
except ImportError as e:
    logging.warning(f"docx2pdf not available: {e}")

# Import configuration
from core.config import MODELS_CONFIG, get_capabilities_prompt

class ModelManager:
    """Enhanced ModelManager with role-based configuration and self-aware agents"""
    
    def __init__(self, cache_size: int = 12, ttl_minutes: int = 30):
        """
        Initialize ModelManager with LRU cache and TTL.
        
        Args:
            cache_size: Maximum number of models to cache (default: 12)
            ttl_minutes: Time-to-live for cached models in minutes (default: 30)
        """
        self.cache_size = cache_size
        self.ttl_minutes = ttl_minutes
        self.model_cache: Dict[str, Dict[str, Any]] = {}
        self.last_access: Dict[str, datetime] = {}
        
        # Preload priority models
        self._preload_priority_models()
    
    def _preload_priority_models(self):
        """Preload priority models to ensure fast response times."""
        priority_roles = ["coordinator", "chief_engineer", "analyst"]
        print("Предзагрузка приоритетных моделей...")
        
        for role in priority_roles:
            if role in MODELS_CONFIG:
                config = MODELS_CONFIG[role]
                try:
                    print(f"Загрузка модели {config['model']} для роли {role} с base_url {config['base_url']}")
                    client = self.get_model_client(role)
                    if client:
                        print(f"✓ Предзагружена модель для роли {role}")
                    else:
                        print(f"✗ Не удалось загрузить модель для роли {role}")
                except Exception as e:
                    print(f"✗ Ошибка при загрузке модели для роли {role}: {e}")
        
        print("Предзагрузка завершена")
    
    @lru_cache(maxsize=12)
    def get_model_client(self, role: str) -> Optional[Any]:
        """
        Get model client for specific role with caching.
        
        Args:
            role: Role name (e.g., 'coordinator', 'chief_engineer')
            
        Returns:
            Model client or None if not available
        """
        # Check if role exists in configuration
        if role not in MODELS_CONFIG:
            logging.warning(f"Role {role} not found in MODELS_CONFIG")
            return None
            
        config = MODELS_CONFIG[role]
        
        # Check cache first
        cache_key = f"{role}_{config['base_url']}_{config['model']}"
        if cache_key in self.model_cache:
            cached_entry = self.model_cache[cache_key]
            if datetime.now() - self.last_access[cache_key] < timedelta(minutes=self.ttl_minutes):
                self.last_access[cache_key] = datetime.now()
                return cached_entry['client']
            else:
                # Remove expired entry
                del self.model_cache[cache_key]
                del self.last_access[cache_key]
        
        try:
            # Import LangChain components
            from langchain_openai import ChatOpenAI
            
            # Create model client with role-specific parameters
            # For local models via LM Studio, we don't need an API key
            # Set environment variable instead
            os.environ["OPENAI_API_KEY"] = "not-needed"
            
            # Create client with all parameters
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
        
        Args:
            role: Role name
            
        Returns:
            Capabilities prompt string or None
        """
        return get_capabilities_prompt(role)
    
    def get_role_responsibilities(self, role: str) -> List[str]:
        """
        Get responsibilities for specific role.
        
        Args:
            role: Role name
            
        Returns:
            List of responsibilities
        """
        if role in MODELS_CONFIG:
            return MODELS_CONFIG[role].get('responsibilities', [])
        return []
    
    def get_role_exclusions(self, role: str) -> List[str]:
        """
        Get exclusions for specific role.
        
        Args:
            role: Role name
            
        Returns:
            List of exclusions
        """
        if role in MODELS_CONFIG:
            return MODELS_CONFIG[role].get('exclusions', [])
        return []
    
    def get_role_tools(self, role: str) -> List[str]:
        """
        Get available tools for specific role.
        
        Args:
            role: Role name
            
        Returns:
            List of tool names
        """
        # This would be expanded based on the actual tools available for each role
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
    
    # Additional methods for testing and statistics
    def get_model_stats(self) -> Dict[str, Any]:
        """
        Get statistics about loaded models and cache.
        
        Returns:
            Dictionary with model statistics
        """
        return {
            "loaded_models": len(self.model_cache),
            "max_cache_size": self.cache_size,
            "ttl_minutes": self.ttl_minutes,
            "model_details": {
                role: {
                    "usage_stats": {
                        "call_count": self._get_model_call_count(role),  # Track actual model usage
                        "last_access": str(self.last_access.get(f"{role}_{MODELS_CONFIG[role]['base_url']}_{MODELS_CONFIG[role]['model']}", "Never"))
                    }
                } for role in MODELS_CONFIG.keys()
            }
        }
    
    def get_all_roles(self) -> List[str]:
        """
        Get all available roles.
        
        Returns:
            List of role names
        """
        return list(MODELS_CONFIG.keys())
    
    def _get_model_call_count(self, role: str) -> int:
        """
        Get the number of calls made to a specific model.
        
        Args:
            role: Role name
            
        Returns:
            Number of calls made to the model
        """
        # Track actual model usage by counting accesses to this role's cache key
        cache_key = f"{role}_{MODELS_CONFIG[role]['base_url']}_{MODELS_CONFIG[role]['model']}"
        # Count how many times this model has been accessed
        return len([key for key in self.last_access.keys() if key.startswith(role)])

# Global instance
model_manager = ModelManager()