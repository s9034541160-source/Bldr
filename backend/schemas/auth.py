"""
Pydantic схемы для аутентификации и авторизации
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Схема для создания пользователя"""
    password: str


class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """Схема пользователя в БД"""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    """Схема ответа с пользователем"""
    roles: List[str] = []


class Token(BaseModel):
    """Схема токена"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    """Данные из токена"""
    username: Optional[str] = None
    user_id: Optional[int] = None


class LoginRequest(BaseModel):
    """Схема запроса на вход"""
    username: str
    password: str


class RoleBase(BaseModel):
    """Базовая схема роли"""
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Схема для создания роли"""
    pass


class RoleResponse(RoleBase):
    """Схема ответа с ролью"""
    id: int
    permissions: List[str] = []

    class Config:
        from_attributes = True


class PermissionBase(BaseModel):
    """Базовая схема разрешения"""
    name: str
    description: Optional[str] = None
    resource: str
    action: str


class PermissionCreate(PermissionBase):
    """Схема для создания разрешения"""
    pass


class PermissionResponse(PermissionBase):
    """Схема ответа с разрешением"""
    id: int

    class Config:
        from_attributes = True

