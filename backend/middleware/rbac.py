"""
RBAC middleware для проверки прав доступа
"""

from functools import wraps
from typing import Callable, List
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.models import get_db
from backend.models.auth import User
from backend.services.auth_service import (
    verify_token,
    get_user_by_username,
    check_permission
)
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Получение текущего пользователя из токена"""
    token_data = verify_token(token)
    if token_data is None or token_data.username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_username(db, username=token_data.username)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    return user


def require_permission(resource: str, action: str):
    """
    Декоратор для проверки прав доступа
    
    Использование:
    @router.get("/projects")
    @require_permission("project", "read")
    async def get_projects(current_user: User = Depends(get_current_user)):
        ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Извлекаем current_user из kwargs
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not db:
                # Если db не передан, получаем его через dependency
                db = next(get_db())
            
            if not check_permission(db, current_user, resource, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {resource}:{action}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role_names: List[str]):
    """
    Декоратор для проверки ролей
    
    Использование:
    @router.get("/admin")
    @require_role(["admin", "manager"])
    async def admin_endpoint(current_user: User = Depends(get_current_user)):
        ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_roles = [role.name for role in current_user.roles]
            if not any(role in user_roles for role in role_names):
                if not current_user.is_superuser:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Required roles: {', '.join(role_names)}"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

