import json
from typing import Dict, Any, List
from config.models_config import MODELS_CONFIG
from core.model_manager import ModelManager

class Trainer:
    def __init__(self):
        """
        Trainer - основной класс для обучения и управления моделями в SuperBuilder.
        """
        # Инициализация менеджера моделей
        self.model_manager = ModelManager()
        
    def train_model(self, role: str, training_data: List[Dict[str, Any]]) -> bool:
        """
        Обучение модели для указанной роли.
        
        Args:
            role: Роль для которой нужно обучить модель
            training_data: Данные для обучения
            
        Returns:
            Успешность обучения
        """
        print(f"Обучение модели для роли: {role}")
        
        # Получить клиент модели
        client = self.model_manager.get_model_client(role)
        if client is None:
            print(f"Не удалось получить клиент модели для роли {role}")
            return False
            
        # В реальной реализации здесь будет код обучения модели
        # Для демонстрации просто возвращаем True
        print(f"Модель для роли {role} успешно обучена")
        return True
        
    def query_model(self, role: str, messages: List[Dict[str, str]]) -> str:
        """
        Запрос к модели для указанной роли через менеджер моделей.
        
        Args:
            role: Роль для которой нужно выполнить запрос
            messages: Список сообщений для модели
            
        Returns:
            Ответ модели
        """
        # Используем метод query из ModelManager
        response = self.model_manager.query(role, messages)
        return response
        
    def get_model_stats(self) -> Dict[str, Any]:
        """
        Получить статистику использования моделей.
        
        Returns:
            Статистика моделей
        """
        return self.model_manager.get_model_stats()
        
    def preload_models(self, roles: List[str]) -> None:
        """
        Предзагрузка указанных моделей.
        
        Args:
            roles: Список ролей для предзагрузки
        """
        print(f"Предзагрузка моделей для ролей: {roles}")
        for role in roles:
            client = self.model_manager.get_model_client(role)
            if client:
                print(f"✓ Предзагружена модель для роли {role}")
            else:
                print(f"✗ Не удалось предзагрузить модель для роли {role}")

# Пример использования
if __name__ == "__main__":
    # Создание тренера
    trainer = Trainer()
    
    # Предзагрузка моделей
    trainer.preload_models(["coordinator", "chief_engineer"])
    
    # Получение статистики
    stats = trainer.get_model_stats()
    print(f"Статистика моделей: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    # Запрос к модели координатора
    messages = [{"role": "user", "content": "Проанализируйте проект строительства жилого комплекса"}]
    response = trainer.query_model("coordinator", messages)
    print(f"Ответ координатора: {response}")