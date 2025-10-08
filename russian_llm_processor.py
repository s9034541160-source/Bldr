"""
🇷🇺 Российский LLM процессор для RAG пайплайна
Интеграция YaLM/GigaChat для глубокого анализа русских документов
"""

import logging
import requests
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RussianLLMConfig:
    """Конфигурация российского LLM"""
    provider: str = "yalm"  # yalm, gigachat, rut5
    api_key: str = ""
    base_url: str = ""
    model_name: str = ""
    max_tokens: int = 2048
    temperature: float = 0.1
    timeout: int = 30

class RussianLLMProcessor:
    """
    Российский LLM процессор для глубокого анализа документов
    Поддерживает YaLM, GigaChat, RuT5
    """
    
    def __init__(self, config: RussianLLMConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._validate_config()
    
    def _validate_config(self):
        """Валидация конфигурации"""
        if not self.config.api_key:
            raise ValueError("API ключ не указан")
        
        if self.config.provider not in ["yalm", "gigachat", "rut5"]:
            raise ValueError(f"Неподдерживаемый провайдер: {self.config.provider}")
    
    def analyze_document_structure(self, content: str, vlm_metadata: Dict) -> Dict:
        """
        Глубокий анализ структуры документа с помощью российского LLM
        
        Args:
            content: Текст документа
            vlm_metadata: Метаданные от VLM анализа
            
        Returns:
            Dict с результатами анализа
        """
        try:
            # Подготавливаем промпт для российского LLM
            prompt = self._prepare_analysis_prompt(content, vlm_metadata)
            
            # Отправляем запрос к LLM
            response = self._send_llm_request(prompt)
            
            # Парсим ответ
            analysis_result = self._parse_llm_response(response)
            
            return {
                'russian_llm_available': True,
                'analysis': analysis_result,
                'provider': self.config.provider,
                'model': self.config.model_name,
                'tokens_used': response.get('usage', {}).get('total_tokens', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Russian LLM analysis failed: {e}")
            return {
                'russian_llm_available': False,
                'error': str(e),
                'fallback_to_vlm': True
            }
    
    def _prepare_analysis_prompt(self, content: str, vlm_metadata: Dict) -> str:
        """Подготовка промпта для российского LLM"""
        
        # Извлекаем информацию от VLM
        vlm_tables = vlm_metadata.get('tables', [])
        vlm_sections = vlm_metadata.get('sections', [])
        
        prompt = f"""
Ты - эксперт по анализу строительной документации. Проанализируй следующий документ и извлеки структурированную информацию.

ДОКУМЕНТ:
{content[:3000]}...

VLM АНАЛИЗ (предварительный):
- Таблицы: {len(vlm_tables)}
- Секции: {len(vlm_sections)}

ЗАДАЧИ:
1. Определи тип документа (СНиП, ГОСТ, ППР, смета, проект)
2. Извлеки основные разделы и подразделы
3. Найди таблицы и их содержимое
4. Выдели ключевые требования и нормы
5. Определи применимость и область действия

ФОРМАТ ОТВЕТА (JSON):
{{
    "document_type": "тип документа",
    "sections": [
        {{
            "title": "название раздела",
            "content": "содержимое",
            "level": 1
        }}
    ],
    "tables": [
        {{
            "title": "название таблицы",
            "data": "данные таблицы"
        }}
    ],
    "requirements": [
        "ключевое требование 1",
        "ключевое требование 2"
    ],
    "scope": "область применения"
}}

Отвечай только JSON, без дополнительного текста.
"""
        return prompt
    
    def _send_llm_request(self, prompt: str) -> Dict:
        """Отправка запроса к российскому LLM"""
        
        if self.config.provider == "yalm":
            return self._send_yalm_request(prompt)
        elif self.config.provider == "gigachat":
            return self._send_gigachat_request(prompt)
        elif self.config.provider == "rut5":
            return self._send_rut5_request(prompt)
        else:
            raise ValueError(f"Неподдерживаемый провайдер: {self.config.provider}")
    
    def _send_yalm_request(self, prompt: str) -> Dict:
        """Запрос к YaLM API"""
        url = f"{self.config.base_url}/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.config.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        
        response = requests.post(
            url, 
            headers=headers, 
            json=data, 
            timeout=self.config.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"YaLM API error: {response.status_code} - {response.text}")
        
        return response.json()
    
    def _send_gigachat_request(self, prompt: str) -> Dict:
        """Запрос к GigaChat API"""
        # Реализация для GigaChat API
        # (требует специфичную настройку для Сбера)
        pass
    
    def _send_rut5_request(self, prompt: str) -> Dict:
        """Запрос к RuT5 (локальная модель)"""
        # Реализация для локальной RuT5 модели
        # (требует установки transformers)
        pass
    
    def _parse_llm_response(self, response: Dict) -> Dict:
        """Парсинг ответа от LLM"""
        try:
            # Извлекаем текст ответа
            if 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0]['message']['content']
            else:
                raise ValueError("Некорректный формат ответа от LLM")
            
            # Парсим JSON
            analysis = json.loads(content)
            return analysis
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {e}")
            return {"error": "Failed to parse LLM response"}
        except Exception as e:
            self.logger.error(f"Failed to parse LLM response: {e}")
            return {"error": str(e)}

# Пример использования
if __name__ == "__main__":
    # Конфигурация для YaLM
    config = RussianLLMConfig(
        provider="yalm",
        api_key="your-yalm-api-key",
        base_url="https://api.yalm.ru",
        model_name="yalm-30b",
        max_tokens=2048
    )
    
    # Создание процессора
    processor = RussianLLMProcessor(config)
    
    # Тестовый анализ
    test_content = "Это тестовый документ для анализа структуры."
    vlm_metadata = {"tables": [], "sections": []}
    
    result = processor.analyze_document_structure(test_content, vlm_metadata)
    print(f"Результат анализа: {result}")
