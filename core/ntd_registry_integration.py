#!/usr/bin/env python3
"""
Интеграция извлечения НТД в RAG-Тренер (Stage 12)
"""
import json
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
import logging

from core.ntd_reference_extractor import NTDReferenceExtractor, NTDReference

logger = logging.getLogger(__name__)

class NTDRegistryIntegration:
    """Интеграция реестра НТД с RAG-Тренером"""
    
    def __init__(self, neo4j_uri: str = "neo4j://localhost:7687", 
                 neo4j_user: str = "neo4j", neo4j_password: str = "neopassword"):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver = None
        self.extractor = NTDReferenceExtractor()
        
        # Инициализируем подключение к Neo4j
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, self.neo4j_password)
            )
            logger.info("Neo4j connection established for NTD Registry")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None
    
    def process_document_ntd_references(self, document_text: str, document_id: str, 
                                      document_metadata: Dict[str, Any]) -> List[NTDReference]:
        """
        Обрабатывает документ и извлекает ссылки на НТД
        
        Args:
            document_text: Текст документа
            document_id: ID документа
            document_metadata: Метаданные документа
            
        Returns:
            Список найденных ссылок на НТД
        """
        try:
            # Извлекаем ссылки на НТД
            references = self.extractor.extract_ntd_references(document_text, document_id)
            
            # Сохраняем в Neo4j
            if self.driver:
                self._save_ntd_references_to_neo4j(document_id, references, document_metadata)
            
            logger.info(f"Processed {len(references)} NTD references for document {document_id}")
            return references
            
        except Exception as e:
            logger.error(f"Error processing NTD references for {document_id}: {e}")
            return []
    
    def _save_ntd_references_to_neo4j(self, document_id: str, references: List[NTDReference], 
                                     document_metadata: Dict[str, Any]):
        """Сохраняет ссылки на НТД в Neo4j"""
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                # Создаем узел документа если его нет
                session.run("""
                    MERGE (doc:Document {id: $doc_id})
                    SET doc.title = $title,
                        doc.type = $type,
                        doc.processed_at = datetime()
                """, 
                doc_id=document_id,
                title=document_metadata.get('title', ''),
                type=document_metadata.get('type', 'document')
                )
                
                # Создаем узлы НТД и связи
                for ref in references:
                    # Создаем узел НТД
                    session.run("""
                        MERGE (ntd:NTD {canonical_id: $canonical_id})
                        SET ntd.document_type = $doc_type,
                            ntd.full_text = $full_text,
                            ntd.context = $context,
                            ntd.confidence = $confidence,
                            ntd.updated_at = datetime()
                    """, 
                    canonical_id=ref.canonical_id,
                    doc_type=ref.document_type,
                    full_text=ref.full_text,
                    context=ref.context,
                    confidence=ref.confidence
                    )
                    
                    # Создаем связь между документом и НТД
                    session.run("""
                        MATCH (doc:Document {id: $doc_id})
                        MATCH (ntd:NTD {canonical_id: $canonical_id})
                        MERGE (doc)-[r:REFERENCES_NTD]->(ntd)
                        SET r.confidence = $confidence,
                            r.context = $context,
                            r.position = $position,
                            r.created_at = datetime()
                    """, 
                    doc_id=document_id,
                    canonical_id=ref.canonical_id,
                    confidence=ref.confidence,
                    context=ref.context,
                    position=ref.position
                    )
                
                logger.info(f"Saved {len(references)} NTD references to Neo4j for document {document_id}")
                
        except Exception as e:
            logger.error(f"Error saving NTD references to Neo4j: {e}")
    
    def get_ntd_network_for_document(self, document_id: str) -> Dict[str, Any]:
        """Получает сеть НТД для конкретного документа"""
        if not self.driver:
            return {"error": "Neo4j not available"}
        
        try:
            with self.driver.session() as session:
                # Получаем все НТД, на которые ссылается документ
                result = session.run("""
                    MATCH (doc:Document {id: $doc_id})-[r:REFERENCES_NTD]->(ntd:NTD)
                    RETURN ntd.canonical_id as canonical_id,
                           ntd.document_type as doc_type,
                           ntd.confidence as confidence,
                           r.context as context
                    ORDER BY ntd.confidence DESC
                """, doc_id=document_id)
                
                references = []
                for record in result:
                    references.append({
                        'canonical_id': record['canonical_id'],
                        'document_type': record['doc_type'],
                        'confidence': record['confidence'],
                        'context': record['context']
                    })
                
                return {
                    'document_id': document_id,
                    'references': references,
                    'total_references': len(references)
                }
                
        except Exception as e:
            logger.error(f"Error getting NTD network for document {document_id}: {e}")
            return {"error": str(e)}
    
    def get_ntd_statistics(self) -> Dict[str, Any]:
        """Получает статистику по НТД"""
        if not self.driver:
            return {"error": "Neo4j not available"}
        
        try:
            with self.driver.session() as session:
                # Общая статистика
                total_ntd = session.run("MATCH (n:NTD) RETURN count(n) as count").single()['count']
                total_docs = session.run("MATCH (d:Document) RETURN count(d) as count").single()['count']
                total_relations = session.run("MATCH ()-[r:REFERENCES_NTD]->() RETURN count(r) as count").single()['count']
                
                # Статистика по типам НТД
                type_stats = session.run("""
                    MATCH (n:NTD)
                    RETURN n.document_type as doc_type, count(n) as count
                    ORDER BY count DESC
                """).data()
                
                # Топ НТД по количеству ссылок
                top_ntd = session.run("""
                    MATCH (d:Document)-[r:REFERENCES_NTD]->(n:NTD)
                    RETURN n.canonical_id as canonical_id, 
                           n.document_type as doc_type,
                           count(r) as reference_count
                    ORDER BY reference_count DESC
                    LIMIT 10
                """).data()
                
                return {
                    'total_ntd': total_ntd,
                    'total_documents': total_docs,
                    'total_relations': total_relations,
                    'by_type': type_stats,
                    'top_ntd': top_ntd
                }
                
        except Exception as e:
            logger.error(f"Error getting NTD statistics: {e}")
            return {"error": str(e)}
    
    def find_related_documents(self, ntd_canonical_id: str) -> List[Dict[str, Any]]:
        """Находит документы, которые ссылаются на конкретный НТД"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (d:Document)-[r:REFERENCES_NTD]->(n:NTD {canonical_id: $ntd_id})
                    RETURN d.id as doc_id,
                           d.title as title,
                           d.type as type,
                           r.confidence as confidence,
                           r.context as context
                    ORDER BY r.confidence DESC
                """, ntd_id=ntd_canonical_id)
                
                documents = []
                for record in result:
                    documents.append({
                        'doc_id': record['doc_id'],
                        'title': record['title'],
                        'type': record['type'],
                        'confidence': record['confidence'],
                        'context': record['context']
                    })
                
                return documents
                
        except Exception as e:
            logger.error(f"Error finding related documents for NTD {ntd_canonical_id}: {e}")
            return []
    
    def close(self):
        """Закрывает подключение к Neo4j"""
        if self.driver:
            self.driver.close()

# Example usage
if __name__ == "__main__":
    integration = NTDRegistryIntegration()
    
    # Тестовые данные
    test_text = """
    В соответствии с СП 43.13330.2012 и СНиП 2.09.03-85, 
    а также ГОСТ 12345-67, при проектировании следует учитывать
    требования СП 31-110-2003.
    """
    
    test_metadata = {
        'title': 'Тестовый документ',
        'type': 'construction'
    }
    
    # Обрабатываем документ
    references = integration.process_document_ntd_references(
        test_text, "test_doc_001", test_metadata
    )
    
    print(f"Found {len(references)} NTD references")
    
    # Получаем статистику
    stats = integration.get_ntd_statistics()
    print(f"NTD Statistics: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    
    integration.close()
