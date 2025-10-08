"""
Менеджер состояний пользователей для Telegram бота
"""
import json
import redis
from typing import Dict, Any, Optional
import os

class StateManager:
    """Менеджер состояний пользователей"""
    
    def __init__(self):
        """Инициализация менеджера состояний"""
        # Подключение к Redis (если доступен)
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()  # Проверяем подключение
            self.use_redis = True
        except Exception:
            # Если Redis недоступен, используем in-memory хранилище
            self.redis_client = None
            self.use_redis = False
            self.memory_storage = {}
    
    async def get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение состояния пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict: Состояние пользователя или None
        """
        try:
            if self.use_redis:
                state_data = self.redis_client.get(f"user_state:{user_id}")
                if state_data:
                    return json.loads(state_data)
                return None
            else:
                return self.memory_storage.get(user_id)
        except Exception as e:
            print(f"❌ Ошибка получения состояния пользователя {user_id}: {e}")
            return None
    
    async def set_user_state(self, user_id: int, state: Dict[str, Any]) -> bool:
        """
        Установка состояния пользователя
        
        Args:
            user_id: ID пользователя
            state: Состояние пользователя
            
        Returns:
            bool: True если успешно
        """
        try:
            if self.use_redis:
                # Устанавливаем TTL для автоматической очистки (24 часа)
                self.redis_client.setex(
                    f"user_state:{user_id}",
                    86400,  # 24 часа
                    json.dumps(state, ensure_ascii=False)
                )
            else:
                self.memory_storage[user_id] = state
            
            return True
        except Exception as e:
            print(f"❌ Ошибка установки состояния пользователя {user_id}: {e}")
            return False
    
    async def update_user_state(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """
        Обновление состояния пользователя
        
        Args:
            user_id: ID пользователя
            updates: Обновления состояния
            
        Returns:
            bool: True если успешно
        """
        try:
            current_state = await self.get_user_state(user_id)
            if current_state:
                current_state.update(updates)
                return await self.set_user_state(user_id, current_state)
            else:
                return await self.set_user_state(user_id, updates)
        except Exception as e:
            print(f"❌ Ошибка обновления состояния пользователя {user_id}: {e}")
            return False
    
    async def clear_user_state(self, user_id: int) -> bool:
        """
        Очистка состояния пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если успешно
        """
        try:
            if self.use_redis:
                self.redis_client.delete(f"user_state:{user_id}")
            else:
                if user_id in self.memory_storage:
                    del self.memory_storage[user_id]
            
            return True
        except Exception as e:
            print(f"❌ Ошибка очистки состояния пользователя {user_id}: {e}")
            return False
    
    async def get_user_data(self, user_id: int, key: str = None) -> Any:
        """
        Получение данных пользователя
        
        Args:
            user_id: ID пользователя
            key: Ключ данных (если None, возвращает все данные)
            
        Returns:
            Any: Данные пользователя
        """
        try:
            state = await self.get_user_state(user_id)
            if state and "data" in state:
                if key:
                    return state["data"].get(key)
                else:
                    return state["data"]
            return None
        except Exception as e:
            print(f"❌ Ошибка получения данных пользователя {user_id}: {e}")
            return None
    
    async def set_user_data(self, user_id: int, key: str, value: Any) -> bool:
        """
        Установка данных пользователя
        
        Args:
            user_id: ID пользователя
            key: Ключ данных
            value: Значение данных
            
        Returns:
            bool: True если успешно
        """
        try:
            current_state = await self.get_user_state(user_id)
            if current_state:
                if "data" not in current_state:
                    current_state["data"] = {}
                current_state["data"][key] = value
                return await self.set_user_state(user_id, current_state)
            else:
                return await self.set_user_state(user_id, {"data": {key: value}})
        except Exception as e:
            print(f"❌ Ошибка установки данных пользователя {user_id}: {e}")
            return False
    
    async def get_active_users(self) -> list:
        """
        Получение списка активных пользователей
        
        Returns:
            list: Список ID активных пользователей
        """
        try:
            if self.use_redis:
                keys = self.redis_client.keys("user_state:*")
                return [int(key.split(":")[1]) for key in keys]
            else:
                return list(self.memory_storage.keys())
        except Exception as e:
            print(f"❌ Ошибка получения активных пользователей: {e}")
            return []
    
    async def cleanup_expired_states(self) -> int:
        """
        Очистка истекших состояний
        
        Returns:
            int: Количество очищенных состояний
        """
        try:
            if self.use_redis:
                # Redis автоматически удаляет истекшие ключи
                return 0
            else:
                # Для in-memory хранилища очищаем старые состояния
                # (здесь можно добавить логику очистки по времени)
                return 0
        except Exception as e:
            print(f"❌ Ошибка очистки истекших состояний: {e}")
            return 0
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Получение информации о хранилище
        
        Returns:
            Dict: Информация о хранилище
        """
        try:
            if self.use_redis:
                info = self.redis_client.info()
                return {
                    "type": "redis",
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "keyspace": info.get("db0", {}).get("keys", 0)
                }
            else:
                return {
                    "type": "memory",
                    "users_count": len(self.memory_storage),
                    "users": list(self.memory_storage.keys())
                }
        except Exception as e:
            return {
                "type": "error",
                "error": str(e)
            }
