"""
Контроллер достоверности для двухуровневой валидации ИИ
"""

# ... existing imports ...
from typing import Dict, Any, Optional, List
from backend.services.rag_service import rag_service
from backend.core.model_manager import model_manager
from backend.services.redis_service import redis_service
import logging
import hashlib
import json

logger = logging.getLogger(__name__)

METRIC_TOTAL_KEY = "validation:metrics:total"
METRIC_VALIDATED_KEY = "validation:metrics:validated"
METRIC_REQUIRES_KEY = "validation:metrics:requires_verification"
METRIC_SUM_DISCREPANCY_KEY = "validation:metrics:sum_discrepancy"
METRIC_SUM_CONFIDENCE_KEY = "validation:metrics:sum_confidence"


class ValidationController:
    """Контроллер для проверки достоверности ответов LLM через RAG"""
    
    def __init__(self, threshold: float = 0.10):
        """
        Args:
            threshold: Порог расхождения между LLM и RAG (10% по умолчанию)
        """
        self.threshold = threshold
    
    def validate_response(
        self,
        query: str,
        llm_response: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Валидация ответа LLM через RAG
        
        Args:
            query: Исходный запрос
            llm_response: Ответ от LLM
            use_cache: Использовать кэш для RAG поиска
            
        Returns:
            Результат валидации с метриками
        """
        # Поиск релевантных документов через RAG
        if use_cache:
            rag_results = self._get_cached_rag_results(query)
            if not rag_results:
                rag_results = rag_service.search(query, limit=5, score_threshold=0.7)
                self._cache_rag_results(query, rag_results)
        else:
            rag_results = rag_service.search(query, limit=5, score_threshold=0.7)
        
        # Если RAG не нашел документов, пометка "требует проверки"
        if not rag_results:
            return {
                "validated": False,
                "requires_verification": True,
                "reason": "no_rag_results",
                "llm_response": llm_response,
                "rag_results": [],
                "discrepancy": None,
                "confidence": 0.0
            }
        
        # Расчет расхождения между ответом LLM и результатами RAG
        discrepancy = self._calculate_discrepancy(llm_response, rag_results)
        
        # Определение требует ли ответ верификации
        requires_verification = discrepancy > self.threshold
        
        # Расчет confidence score
        confidence = self._calculate_confidence(discrepancy, rag_results)
        
        result = {
            "validated": not requires_verification,
            "requires_verification": requires_verification,
            "reason": "high_discrepancy" if requires_verification else "validated",
            "llm_response": llm_response,
            "rag_results": [
                {
                    "text": r.get("text", "")[:200],  # Первые 200 символов
                    "score": r.get("score", 0),
                    "document_id": r.get("document_id")
                }
                for r in rag_results
            ],
            "discrepancy": discrepancy,
            "confidence": confidence,
            "threshold": self.threshold
        }
        
        # Логирование случаев расхождений
        if requires_verification:
            self._log_discrepancy(query, llm_response, discrepancy, rag_results)
        
        self._update_metrics(result)
        return result
    
    def _calculate_discrepancy(
        self,
        llm_response: str,
        rag_results: List[Dict[str, Any]]
    ) -> float:
        """
        Расчет расхождения между ответом LLM и результатами RAG
        
        Используется семантическое сравнение через эмбеддинги
        """
        try:
            # Создание эмбеддинга для ответа LLM
            llm_embedding = rag_service.create_embedding(llm_response)
            
            # Создание эмбеддинга для лучшего результата RAG
            if not rag_results:
                return 1.0  # Максимальное расхождение если нет результатов
            
            best_rag_text = rag_results[0].get("text", "")
            rag_embedding = rag_service.create_embedding(best_rag_text)
            
            # Расчет косинусного расстояния
            import numpy as np
            
            llm_array = np.array(llm_embedding)
            rag_array = np.array(rag_embedding)
            
            cosine_similarity = np.dot(llm_array, rag_array) / (
                np.linalg.norm(llm_array) * np.linalg.norm(rag_array)
            )
            
            # Преобразование в расхождение (1 - similarity)
            discrepancy = 1.0 - cosine_similarity
            
            return float(discrepancy)
            
        except Exception as e:
            logger.error(f"Error calculating discrepancy: {e}")
            return 0.5  # Среднее расхождение при ошибке
    
    def _calculate_confidence(
        self,
        discrepancy: float,
        rag_results: List[Dict[str, Any]]
    ) -> float:
        """
        Расчет confidence score (0-1)
        
        Args:
            discrepancy: Расхождение между LLM и RAG
            rag_results: Результаты RAG поиска
            
        Returns:
            Confidence score от 0 до 1
        """
        # Базовый confidence на основе расхождения
        base_confidence = 1.0 - discrepancy
        
        # Учет качества RAG результатов
        if rag_results:
            avg_score = sum(r.get("score", 0) for r in rag_results) / len(rag_results)
            # Увеличиваем confidence если RAG результаты релевантны
            base_confidence = (base_confidence + avg_score) / 2
        
        # Ограничение в диапазоне [0, 1]
        confidence = max(0.0, min(1.0, base_confidence))
        
        return confidence
    
    def _get_cached_rag_results(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Получение закэшированных результатов RAG"""
        try:
            cache_key = f"rag_search:{hashlib.md5(query.encode()).hexdigest()}"
            cached = redis_service.get(cache_key)
            if cached:
                return cached
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        return None
    
    def _cache_rag_results(self, query: str, results: List[Dict[str, Any]]):
        """Кэширование результатов RAG"""
        try:
            cache_key = f"rag_search:{hashlib.md5(query.encode()).hexdigest()}"
            redis_service.set(cache_key, results, ex=3600)  # TTL 1 час
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def _log_discrepancy(
        self,
        query: str,
        llm_response: str,
        discrepancy: float,
        rag_results: List[Dict[str, Any]]
    ):
        """Логирование случаев расхождений для анализа"""
        log_entry = {
            "query": query,
            "llm_response": llm_response[:500],  # Первые 500 символов
            "discrepancy": discrepancy,
            "rag_results_count": len(rag_results),
            "timestamp": str(logging.Formatter().formatTime(logging.LogRecord(
                name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
            )))
        }
        
        logger.warning(
            f"High discrepancy detected: {discrepancy:.2%} "
            f"for query: {query[:100]}"
        )
        
        # Сохранение в Redis для последующего анализа
        try:
            discrepancy_key = f"discrepancy_log:{hashlib.md5(query.encode()).hexdigest()}"
            redis_service.set(discrepancy_key, log_entry, ex=86400 * 7)  # 7 дней
        except Exception as e:
            logger.warning(f"Failed to log discrepancy: {e}")

    def _update_metrics(self, result: Dict[str, Any]) -> None:
        try:
            redis_service.incr(METRIC_TOTAL_KEY)
            if result.get("requires_verification"):
                redis_service.incr(METRIC_REQUIRES_KEY)
            else:
                redis_service.incr(METRIC_VALIDATED_KEY)
            discrepancy = float(result.get("discrepancy") or 0.0)
            confidence = float(result.get("confidence") or 0.0)
            redis_service.incrbyfloat(METRIC_SUM_DISCREPANCY_KEY, discrepancy)
            redis_service.incrbyfloat(METRIC_SUM_CONFIDENCE_KEY, confidence)
        except Exception as exc:
            logger.warning("Failed to update validation metrics: %s", exc)

    def get_metrics(self) -> Dict[str, float]:
        def _get_int(key: str) -> int:
            value = redis_service.get(key)
            return int(value) if value is not None else 0

        def _get_float(key: str) -> float:
            value = redis_service.get(key)
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        total = _get_int(METRIC_TOTAL_KEY)
        validated = _get_int(METRIC_VALIDATED_KEY)
        requires = _get_int(METRIC_REQUIRES_KEY)
        sum_discrepancy = _get_float(METRIC_SUM_DISCREPANCY_KEY)
        sum_confidence = _get_float(METRIC_SUM_CONFIDENCE_KEY)

        average_discrepancy = sum_discrepancy / total if total else 0.0
        average_confidence = sum_confidence / total if total else 0.0
        hallucination_rate = requires / total if total else 0.0

        return {
            "total_validations": float(total),
            "validated_count": float(validated),
            "requires_verification_count": float(requires),
            "average_discrepancy": average_discrepancy,
            "average_confidence": average_confidence,
            "hallucination_rate": hallucination_rate,
        }


# Глобальный экземпляр контроллера валидации
validation_controller = ValidationController(threshold=0.10)

