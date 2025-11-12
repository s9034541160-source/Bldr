"""
Сервис для работы с Qdrant
"""

import logging
import time
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    ScalarQuantization,
    ScalarQuantizationConfig,
    ScalarType,
)

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class QdrantService:
    """Сервис для работы с Qdrant"""
    
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
            prefer_grpc=False,
            trust_env=False,
        )
        self.collection_name = settings.RAG_COLLECTION_NAME
    
    def init_collection(self, vector_size: int = 384):
        """Инициализация коллекции с повторными попытками при недоступности Qdrant."""
        max_attempts = 5
        backoff_seconds = 3

        for attempt in range(1, max_attempts + 1):
            try:
                collections = self.client.get_collections()
                collection_names = [col.name for col in collections.collections]

                quantization_config = None
                if settings.RAG_ENABLE_QUANTIZATION:
                    quantization_config = ScalarQuantization(
                        scalar=ScalarQuantizationConfig(
                            type=ScalarType.INT8,
                            quantile=settings.RAG_QUANTIZATION_QUANTILE,
                            always_ram=True,
                        )
                    )

                if self.collection_name not in collection_names:
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=vector_size,
                            distance=Distance.COSINE,
                        ),
                        quantization_config=quantization_config,
                    )
                    logger.info("Created collection: %s", self.collection_name)
                else:
                    if quantization_config:
                        try:
                            self.client.update_collection(
                                collection_name=self.collection_name,
                                quantization_config=quantization_config,
                            )
                            logger.info(
                                "Updated quantization config for collection %s",
                                self.collection_name,
                            )
                        except Exception as update_exc:  # noqa: BLE001
                            logger.warning(
                                "Failed to update quantization config: %s",
                                update_exc,
                            )
                    logger.info("Collection %s already exists", self.collection_name)
                return
            except UnexpectedResponse as exc:
                if exc.status_code == 503 and attempt < max_attempts:
                    logger.warning(
                        "Qdrant unavailable (503). Retry %s/%s after %ss",
                        attempt,
                        max_attempts,
                        backoff_seconds,
                    )
                    time.sleep(backoff_seconds)
                    backoff_seconds *= 2
                    continue
                logger.error("Error initializing collection: %s", exc)
                raise
            except Exception as exc:  # noqa: BLE001
                logger.error("Error initializing collection: %s", exc)
                raise
    
    def add_document(self, document_id: str, vector: list, payload: dict):
        """Добавление документа в коллекцию"""
        point = PointStruct(
            id=document_id,
            vector=vector,
            payload=payload
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

    def add_documents_batch(self, points: List[PointStruct]):
        """Добавление документов батчом"""
        if not points:
            return
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
    
    def search(self, query_vector: list, limit: int = 10, filter_dict: dict = None):
        """Поиск похожих документов"""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        search_filter = None
        if filter_dict:
            conditions = []
            for key, value in filter_dict.items():
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            search_filter = Filter(must=conditions)
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=search_filter
        )
        
        return results
    
    def delete_document(self, document_id: str):
        """Удаление документа"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[document_id]
        )


# Глобальный экземпляр сервиса
qdrant_service = QdrantService()

