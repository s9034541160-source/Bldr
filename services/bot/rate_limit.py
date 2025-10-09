"""
Rate limiting для Telegram бота с Redis
"""
import os
import time
from typing import Tuple, Optional
import redis
from datetime import datetime, timedelta

class RateLimiter:
    """Rate limiter для защиты от спама"""
    
    def __init__(self):
        """Инициализация rate limiter"""
        # Подключение к Redis
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
    
    async def check_rate_limit(self, user_id: int, max_messages: int = 20, window_seconds: int = 60) -> Tuple[bool, int]:
        """
        Проверка rate limit для пользователя
        
        Args:
            user_id: ID пользователя
            max_messages: Максимальное количество сообщений
            window_seconds: Окно времени в секундах
            
        Returns:
            Tuple[bool, int]: (разрешено, оставшихся сообщений)
        """
        try:
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            if self.use_redis:
                # Используем Redis для подсчета
                pipe = self.redis_client.pipeline()
                
                # Ключ для подсчета сообщений
                count_key = f"user:{user_id}:count"
                
                # Увеличиваем счетчик
                pipe.incr(count_key)
                pipe.expire(count_key, window_seconds)
                
                # Получаем текущий счет
                results = pipe.execute()
                current_count = results[0]
                
                # Проверяем лимит
                if current_count > max_messages:
                    # Пользователь превысил лимит - баним на 5 минут
                    ban_key = f"user:{user_id}:banned"
                    ban_until = current_time + 300  # 5 минут
                    self.redis_client.setex(ban_key, 300, ban_until)
                    
                    return False, 0
                
                remaining = max(0, max_messages - current_count)
                return True, remaining
                
            else:
                # Используем in-memory хранилище
                if user_id not in self.memory_storage:
                    self.memory_storage[user_id] = []
                
                # Очищаем старые записи
                user_messages = self.memory_storage[user_id]
                user_messages[:] = [msg_time for msg_time in user_messages if msg_time > window_start]
                
                # Добавляем текущее сообщение
                user_messages.append(current_time)
                
                # Проверяем лимит
                if len(user_messages) > max_messages:
                    # Баним пользователя
                    self.memory_storage[f"{user_id}_banned"] = current_time + 300
                    return False, 0
                
                remaining = max(0, max_messages - len(user_messages))
                return True, remaining
                
        except Exception as e:
            print(f"❌ Ошибка rate limit для пользователя {user_id}: {e}")
            # В случае ошибки разрешаем сообщение
            return True, max_messages
    
    async def is_user_banned(self, user_id: int) -> Tuple[bool, Optional[int]]:
        """
        Проверка забанен ли пользователь
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Tuple[bool, Optional[int]]: (забанен, время разбана)
        """
        try:
            current_time = int(time.time())
            
            if self.use_redis:
                ban_key = f"user:{user_id}:banned"
                ban_until = self.redis_client.get(ban_key)
                
                if ban_until:
                    ban_until = int(ban_until)
                    if current_time < ban_until:
                        return True, ban_until
                    else:
                        # Время бана истекло
                        self.redis_client.delete(ban_key)
                        return False, None
                else:
                    return False, None
                    
            else:
                # In-memory проверка
                ban_key = f"{user_id}_banned"
                if ban_key in self.memory_storage:
                    ban_until = self.memory_storage[ban_key]
                    if current_time < ban_until:
                        return True, ban_until
                    else:
                        # Время бана истекло
                        del self.memory_storage[ban_key]
                        return False, None
                else:
                    return False, None
                    
        except Exception as e:
            print(f"❌ Ошибка проверки бана для пользователя {user_id}: {e}")
            return False, None
    
    async def unban_user(self, user_id: int) -> bool:
        """
        Разбан пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если разбан прошел успешно
        """
        try:
            if self.use_redis:
                ban_key = f"user:{user_id}:banned"
                self.redis_client.delete(ban_key)
            else:
                ban_key = f"{user_id}_banned"
                if ban_key in self.memory_storage:
                    del self.memory_storage[ban_key]
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка разбана пользователя {user_id}: {e}")
            return False
    
    async def get_user_stats(self, user_id: int) -> dict:
        """
        Получение статистики пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            dict: Статистика пользователя
        """
        try:
            current_time = int(time.time())
            
            if self.use_redis:
                count_key = f"user:{user_id}:count"
                ban_key = f"user:{user_id}:banned"
                
                # Получаем количество сообщений
                message_count = self.redis_client.get(count_key) or 0
                message_count = int(message_count)
                
                # Проверяем бан
                ban_until = self.redis_client.get(ban_key)
                is_banned = ban_until is not None and current_time < int(ban_until)
                
                return {
                    "user_id": user_id,
                    "message_count": message_count,
                    "is_banned": is_banned,
                    "ban_until": int(ban_until) if ban_until else None,
                    "storage_type": "redis"
                }
            else:
                # In-memory статистика
                user_messages = self.memory_storage.get(user_id, [])
                ban_key = f"{user_id}_banned"
                ban_until = self.memory_storage.get(ban_key)
                
                is_banned = ban_until is not None and current_time < ban_until
                
                return {
                    "user_id": user_id,
                    "message_count": len(user_messages),
                    "is_banned": is_banned,
                    "ban_until": ban_until,
                    "storage_type": "memory"
                }
                
        except Exception as e:
            print(f"❌ Ошибка получения статистики пользователя {user_id}: {e}")
            return {
                "user_id": user_id,
                "message_count": 0,
                "is_banned": False,
                "ban_until": None,
                "storage_type": "error"
            }
    
    async def cleanup_expired_data(self) -> int:
        """
        Очистка истекших данных
        
        Returns:
            int: Количество очищенных записей
        """
        try:
            cleaned = 0
            current_time = int(time.time())
            
            if self.use_redis:
                # Redis автоматически удаляет истекшие ключи
                return 0
            else:
                # Очищаем in-memory хранилище
                for key in list(self.memory_storage.keys()):
                    if key.endswith("_banned"):
                        ban_until = self.memory_storage[key]
                        if current_time >= ban_until:
                            del self.memory_storage[key]
                            cleaned += 1
                
                return cleaned
                
        except Exception as e:
            print(f"❌ Ошибка очистки данных: {e}")
            return 0
    
    def get_storage_info(self) -> dict:
        """
        Получение информации о хранилище
        
        Returns:
            dict: Информация о хранилище
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
                    "users_count": len([k for k in self.memory_storage.keys() if not k.endswith("_banned")]),
                    "banned_count": len([k for k in self.memory_storage.keys() if k.endswith("_banned")])
                }
        except Exception as e:
            return {
                "type": "error",
                "error": str(e)
            }
