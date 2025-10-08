#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SECURITY API FOR Bldr Empire
============================

API endpoints для управления безопасностью инструментов
на основе паттернов из agents-towards-production.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from core.security.tool_auth import get_auth_manager, ToolPermission, AuthType, UserContext
from core.memory.dual_memory import get_memory_system
from core.structured_logging import get_logger

router = APIRouter(prefix="/security", tags=["security"])
logger = get_logger("security_api")

# Pydantic модели для API
class UserAuthRequest(BaseModel):
    user_id: str
    username: str
    roles: List[str]
    permissions: List[str]
    session_token: Optional[str] = None
    oauth_token: Optional[str] = None
    api_key: Optional[str] = None

class ToolPermissionRequest(BaseModel):
    tool_name: str
    auth_type: str
    required_scopes: List[str] = []
    rate_limit: int = 100
    user_whitelist: List[str] = []
    admin_only: bool = False

class MemoryStoreRequest(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}
    tags: List[str] = []
    importance_score: float = 0.5

class MemorySearchRequest(BaseModel):
    query: str
    limit: int = 10
    include_long_term: bool = True

@router.post("/auth/user")
async def authenticate_user(request: UserAuthRequest):
    """
    🚀 АУТЕНТИФИКАЦИЯ ПОЛЬЗОВАТЕЛЯ
    
    Аутентифицирует пользователя и создает контекст сессии
    """
    try:
        auth_manager = get_auth_manager()
        
        user_context = auth_manager.authenticate_user(
            user_id=request.user_id,
            username=request.username,
            roles=request.roles,
            permissions=request.permissions,
            session_token=request.session_token,
            oauth_token=request.oauth_token,
            api_key=request.api_key
        )
        
        logger.log_agent_activity(
            agent_name="security_api",
            action="user_authenticated",
            query=request.username,
            result_status="success",
            context={"user_id": request.user_id, "roles": request.roles}
        )
        
        return {
            "status": "success",
            "message": "User authenticated successfully",
            "user_id": user_context.user_id,
            "username": user_context.username,
            "roles": user_context.roles
        }
        
    except Exception as e:
        logger.log_error(e, {"user_id": request.user_id})
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@router.post("/auth/check-access")
async def check_tool_access(user_id: str, tool_name: str):
    """
    🚀 ПРОВЕРКА ДОСТУПА К ИНСТРУМЕНТУ
    
    Проверяет, имеет ли пользователь доступ к указанному инструменту
    """
    try:
        auth_manager = get_auth_manager()
        
        has_access = auth_manager.check_tool_access(user_id, tool_name)
        
        logger.log_agent_activity(
            agent_name="security_api",
            action="access_checked",
            query=tool_name,
            result_status="success" if has_access else "denied",
            context={"user_id": user_id, "tool_name": tool_name}
        )
        
        return {
            "status": "success",
            "has_access": has_access,
            "user_id": user_id,
            "tool_name": tool_name
        }
        
    except Exception as e:
        logger.log_error(e, {"user_id": user_id, "tool_name": tool_name})
        return {
            "status": "error",
            "has_access": False,
            "error": str(e),
            "user_id": user_id,
            "tool_name": tool_name
        }

@router.post("/permissions/register")
async def register_tool_permission(request: ToolPermissionRequest):
    """
    🚀 РЕГИСТРАЦИЯ РАЗРЕШЕНИЯ ДЛЯ ИНСТРУМЕНТА
    
    Регистрирует разрешение для инструмента
    """
    try:
        auth_manager = get_auth_manager()
        
        # Конвертируем строку в enum
        auth_type = AuthType(request.auth_type)
        
        permission = ToolPermission(
            tool_name=request.tool_name,
            auth_type=auth_type,
            required_scopes=request.required_scopes,
            rate_limit=request.rate_limit,
            user_whitelist=request.user_whitelist,
            admin_only=request.admin_only
        )
        
        auth_manager.register_tool_permission(permission)
        
        logger.log_agent_activity(
            agent_name="security_api",
            action="permission_registered",
            query=request.tool_name,
            result_status="success",
            context={
                "tool_name": request.tool_name,
                "auth_type": request.auth_type,
                "rate_limit": request.rate_limit
            }
        )
        
        return {
            "status": "success",
            "message": f"Permission registered for tool {request.tool_name}",
            "permission": {
                "tool_name": permission.tool_name,
                "auth_type": permission.auth_type.value,
                "rate_limit": permission.rate_limit,
                "admin_only": permission.admin_only
            }
        }
        
    except Exception as e:
        logger.log_error(e, {"tool_name": request.tool_name})
        raise HTTPException(status_code=400, detail=f"Failed to register permission: {str(e)}")

@router.get("/permissions/summary")
async def get_permissions_summary():
    """
    🚀 ПОЛУЧЕНИЕ СВОДКИ ПО РАЗРЕШЕНИЯМ
    
    Возвращает сводку по всем зарегистрированным разрешениям
    """
    try:
        auth_manager = get_auth_manager()
        summary = auth_manager.get_tool_permissions_summary()
        
        return {
            "status": "success",
            "permissions": summary,
            "total_tools": len(summary)
        }
        
    except Exception as e:
        logger.log_error(e, {})
        raise HTTPException(status_code=500, detail=f"Failed to get permissions summary: {str(e)}")

@router.delete("/auth/session/{user_id}")
async def revoke_user_session(user_id: str):
    """
    🚀 ОТЗЫВ ПОЛЬЗОВАТЕЛЬСКОЙ СЕССИИ
    
    Отзывает сессию пользователя
    """
    try:
        auth_manager = get_auth_manager()
        auth_manager.revoke_user_session(user_id)
        
        logger.log_agent_activity(
            agent_name="security_api",
            action="session_revoked",
            query="",
            result_status="success",
            context={"user_id": user_id}
        )
        
        return {
            "status": "success",
            "message": f"Session revoked for user {user_id}"
        }
        
    except Exception as e:
        logger.log_error(e, {"user_id": user_id})
        raise HTTPException(status_code=400, detail=f"Failed to revoke session: {str(e)}")

@router.post("/memory/store")
async def store_memory(request: MemoryStoreRequest):
    """
    🚀 СОХРАНЕНИЕ В ПАМЯТЬ
    
    Сохраняет информацию в систему памяти
    """
    try:
        memory_system = get_memory_system()
        
        entry_id = await memory_system.store_memory(
            content=request.content,
            metadata=request.metadata,
            tags=request.tags,
            importance_score=request.importance_score
        )
        
        logger.log_agent_activity(
            agent_name="security_api",
            action="memory_stored",
            query=request.content[:100],
            result_status="success",
            context={"entry_id": entry_id, "importance": request.importance_score}
        )
        
        return {
            "status": "success",
            "message": "Memory stored successfully",
            "entry_id": entry_id
        }
        
    except Exception as e:
        logger.log_error(e, {"content": request.content[:100]})
        raise HTTPException(status_code=400, detail=f"Failed to store memory: {str(e)}")

@router.post("/memory/search")
async def search_memory(request: MemorySearchRequest):
    """
    🚀 ПОИСК В ПАМЯТИ
    
    Выполняет поиск в системе памяти
    """
    try:
        memory_system = get_memory_system()
        
        results = await memory_system.retrieve_memory(
            query=request.query,
            limit=request.limit,
            include_long_term=request.include_long_term
        )
        
        # Конвертируем результаты в словари
        results_data = [entry.to_dict() for entry in results]
        
        logger.log_agent_activity(
            agent_name="security_api",
            action="memory_searched",
            query=request.query,
            result_status="success",
            context={"results_count": len(results_data)}
        )
        
        return {
            "status": "success",
            "results": results_data,
            "count": len(results_data)
        }
        
    except Exception as e:
        logger.log_error(e, {"query": request.query})
        raise HTTPException(status_code=400, detail=f"Failed to search memory: {str(e)}")

@router.get("/memory/stats")
async def get_memory_stats():
    """
    🚀 СТАТИСТИКА ПАМЯТИ
    
    Возвращает статистику системы памяти
    """
    try:
        memory_system = get_memory_system()
        stats = await memory_system.get_memory_stats()
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        logger.log_error(e, {})
        raise HTTPException(status_code=500, detail=f"Failed to get memory stats: {str(e)}")

@router.get("/health")
async def security_health_check():
    """
    🚀 ПРОВЕРКА ЗДОРОВЬЯ СИСТЕМЫ БЕЗОПАСНОСТИ
    
    Проверяет состояние системы безопасности и памяти
    """
    try:
        auth_manager = get_auth_manager()
        memory_system = get_memory_system()
        
        # Проверяем доступность компонентов
        auth_healthy = auth_manager is not None
        memory_healthy = memory_system is not None
        
        return {
            "status": "healthy" if auth_healthy and memory_healthy else "degraded",
            "components": {
                "auth_manager": "healthy" if auth_healthy else "unavailable",
                "memory_system": "healthy" if memory_healthy else "unavailable"
            },
            "timestamp": "2025-09-28T16:00:00Z"
        }
        
    except Exception as e:
        logger.log_error(e, {})
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-09-28T16:00:00Z"
        }
