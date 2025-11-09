"""
Сервис для гибридного подхода к знаниям (LLM + RAG)
"""

from typing import Dict, Any, Optional
from backend.core.model_manager import model_manager
from backend.services.rag_service import rag_service
from backend.services.validation_controller import validation_controller
import logging

logger = logging.getLogger(__name__)


class HybridKnowledgeService:
    """Сервис для гибридного подхода: LLM как основной путь, RAG как контроль"""
    
    def __init__(self, confidence_threshold: float = 0.90):
        """
        Args:
            confidence_threshold: Порог уверенности для автоматического ответа (90%)
        """
        self.confidence_threshold = confidence_threshold
    
    def answer_query(
        self,
        query: str,
        use_llm: bool = True,
        use_rag_fallback: bool = True,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Ответ на запрос с использованием гибридного подхода
        
        Args:
            query: Вопрос пользователя
            use_llm: Использовать LLM для генерации ответа
            use_rag_fallback: Использовать RAG как fallback
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации
            
        Returns:
            Ответ с метаданными о методе генерации
        """
        # Основной путь: дообученная GGUF-модель
        if use_llm:
            llm_response = model_manager.generate(
                prompt=query,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if llm_response:
                # Валидация ответа через RAG
                validation_result = validation_controller.validate_response(
                    query=query,
                    llm_response=llm_response
                )
                
                confidence = validation_result.get("confidence", 0.0)
                
                # Если confidence достаточно высокий, возвращаем ответ LLM
                if confidence >= self.confidence_threshold:
                    return {
                        "answer": llm_response,
                        "method": "llm_validated",
                        "confidence": confidence,
                        "requires_verification": False,
                        "validation": validation_result
                    }
                
                # Если confidence низкий, но есть RAG результаты
                if use_rag_fallback and validation_result.get("rag_results"):
                    # Используем RAG для генерации ответа
                    rag_answer = rag_service.generate_answer(
                        query=query,
                        context_documents=validation_result["rag_results"],
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    
                    return {
                        "answer": rag_answer.get("answer", ""),
                        "method": "rag_fallback",
                        "confidence": confidence,
                        "requires_verification": True,
                        "reason": "low_llm_confidence",
                        "llm_response": llm_response,
                        "rag_sources": rag_answer.get("sources", []),
                        "validation": validation_result
                    }
                
                # Если confidence низкий и нет RAG результатов
                return {
                    "answer": llm_response,
                    "method": "llm_with_warning",
                    "confidence": confidence,
                    "requires_verification": True,
                    "reason": "low_confidence_no_rag",
                    "validation": validation_result
                }
        
        # Fallback: только RAG
        if use_rag_fallback:
            rag_answer = rag_service.rag_query(
                query=query,
                limit=5,
                score_threshold=0.7,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if rag_answer.get("answer"):
                return {
                    "answer": rag_answer["answer"],
                    "method": "rag_only",
                    "confidence": 0.7,  # Средний confidence для RAG
                    "requires_verification": True,
                    "reason": "llm_unavailable_or_failed",
                    "rag_sources": rag_answer.get("sources", [])
                }
        
        # Если ничего не сработало
        return {
            "answer": "Извините, не удалось найти информацию для ответа на ваш вопрос.",
            "method": "none",
            "confidence": 0.0,
            "requires_verification": True,
            "reason": "no_data_available"
        }


# Глобальный экземпляр сервиса
hybrid_knowledge_service = HybridKnowledgeService(confidence_threshold=0.90)

