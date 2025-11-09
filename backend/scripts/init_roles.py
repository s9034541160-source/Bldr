"""
Скрипт для создания начальных ролей и разрешений
"""

import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import SessionLocal, get_db
from backend.models.auth import Role, Permission
from sqlalchemy.orm import Session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_roles_and_permissions(db: Session):
    """Создание начальных ролей и разрешений"""
    
    # Определение разрешений
    permissions_data = [
        # Проекты
        {"name": "project:read", "description": "Чтение проектов", "resource": "project", "action": "read"},
        {"name": "project:write", "description": "Создание и редактирование проектов", "resource": "project", "action": "write"},
        {"name": "project:delete", "description": "Удаление проектов", "resource": "project", "action": "delete"},
        
        # Документы
        {"name": "document:read", "description": "Чтение документов", "resource": "document", "action": "read"},
        {"name": "document:write", "description": "Создание и редактирование документов", "resource": "document", "action": "write"},
        {"name": "document:delete", "description": "Удаление документов", "resource": "document", "action": "delete"},
        {"name": "document:approve", "description": "Согласование документов", "resource": "document", "action": "approve"},
        
        # Процессы
        {"name": "process:read", "description": "Чтение процессов", "resource": "process", "action": "read"},
        {"name": "process:execute", "description": "Выполнение процессов", "resource": "process", "action": "execute"},
        {"name": "process:manage", "description": "Управление процессами", "resource": "process", "action": "manage"},
        
        # Пользователи
        {"name": "user:read", "description": "Чтение пользователей", "resource": "user", "action": "read"},
        {"name": "user:write", "description": "Создание и редактирование пользователей", "resource": "user", "action": "write"},
        {"name": "user:delete", "description": "Удаление пользователей", "resource": "user", "action": "delete"},
        
        # Администрирование
        {"name": "admin:all", "description": "Полный доступ", "resource": "admin", "action": "all"},
    ]
    
    # Создание разрешений
    permissions = {}
    for perm_data in permissions_data:
        existing = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
        if not existing:
            permission = Permission(**perm_data)
            db.add(permission)
            db.flush()
            permissions[perm_data["name"]] = permission
            logger.info(f"Created permission: {perm_data['name']}")
        else:
            permissions[perm_data["name"]] = existing
    
    db.commit()
    
    # Определение ролей
    roles_data = [
        {
            "name": "admin",
            "description": "Администратор системы",
            "permissions": ["admin:all"]
        },
        {
            "name": "manager",
            "description": "Менеджер проектов",
            "permissions": [
                "project:read", "project:write",
                "document:read", "document:write", "document:approve",
                "process:read", "process:execute", "process:manage",
                "user:read"
            ]
        },
        {
            "name": "user",
            "description": "Обычный пользователь",
            "permissions": [
                "project:read",
                "document:read", "document:write",
                "process:read", "process:execute"
            ]
        },
        {
            "name": "guest",
            "description": "Гостевой доступ",
            "permissions": [
                "project:read",
                "document:read"
            ]
        }
    ]
    
    # Создание ролей
    for role_data in roles_data:
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing:
            role = Role(
                name=role_data["name"],
                description=role_data["description"]
            )
            db.add(role)
            db.flush()
            
            # Привязка разрешений
            for perm_name in role_data["permissions"]:
                if perm_name in permissions:
                    role.permissions.append(permissions[perm_name])
            
            db.commit()
            logger.info(f"Created role: {role_data['name']} with {len(role_data['permissions'])} permissions")
        else:
            logger.info(f"Role {role_data['name']} already exists")


def main():
    """Главная функция"""
    db = SessionLocal()
    try:
        create_roles_and_permissions(db)
        logger.info("Roles and permissions initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize roles and permissions: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

