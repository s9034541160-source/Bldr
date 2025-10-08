#!/usr/bin/env python3
"""
NTD API - API для доступа к реестру НТД
Предоставляет endpoints для работы с графом связей НТД
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Импортируем Neo4j
try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    logger.warning("Neo4j not available")
    HAS_NEO4J = False

def get_neo4j_db():
    """Получение подключения к Neo4j"""
    if not HAS_NEO4J:
        raise HTTPException(status_code=503, detail="Neo4j not available")
    
    import os
    neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "neopassword")
    
    try:
        if neo4j_user and neo4j_password:
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        else:
            driver = GraphDatabase.driver(neo4j_uri)
        return driver
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        raise HTTPException(status_code=503, detail=f"Neo4j connection failed: {str(e)}")

# Pydantic модели для API
class NTDNode(BaseModel):
    canonical_id: str
    document_type: str
    full_text: str
    context: str
    confidence: float
    reference_count: Optional[int] = 0

class NTDReference(BaseModel):
    canonical_id: str
    document_type: str
    confidence: float
    context: str
    position: int

class NTDRelationship(BaseModel):
    source: str
    target: str
    relationship_type: str
    created_at: str

class NTDStatistics(BaseModel):
    total_ntd_nodes: int
    total_documents: int
    total_relationships: int
    by_type: Dict[str, int]
    high_confidence_count: int
    average_confidence: float

class NTDNetwork(BaseModel):
    nodes: List[NTDNode]
    relationships: List[NTDRelationship]

# Создаем роутер
ntd_router = APIRouter(prefix="/api/ntd", tags=["NTD Registry"])

@ntd_router.get("/statistics", response_model=NTDStatistics)
async def get_ntd_statistics(neo4j_driver = Depends(get_neo4j_db)):
    """Получает общую статистику по реестру НТД"""
    try:
        with neo4j_driver.session() as session:
            # Общее количество узлов НТД
            ntd_count_result = session.run("MATCH (n:NTD) RETURN count(n) as count")
            ntd_record = ntd_count_result.single()
            ntd_count = ntd_record["count"] if ntd_record else 0
            
            # Общее количество документов
            doc_count_result = session.run("MATCH (d:Document) RETURN count(d) as count")
            doc_record = doc_count_result.single()
            doc_count = doc_record["count"] if doc_record else 0
            
            # Общее количество связей
            rel_count_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_record = rel_count_result.single()
            rel_count = rel_record["count"] if rel_record else 0
            
            # Статистика по типам
            type_stats_result = session.run("""
                MATCH (n:NTD) 
                RETURN n.document_type as type, count(n) as count
                ORDER BY count DESC
            """)
            by_type = {record["type"]: record["count"] for record in type_stats_result}
            
            # Статистика по уверенности
            confidence_result = session.run("""
                MATCH (n:NTD) 
                WHERE n.confidence IS NOT NULL
                RETURN 
                    count(n) as total,
                    sum(CASE WHEN n.confidence >= 0.7 THEN 1 ELSE 0 END) as high_confidence,
                    avg(n.confidence) as avg_confidence
            """)
            conf_record = confidence_result.single()
            high_confidence_count = conf_record["high_confidence"] if conf_record else 0
            average_confidence = conf_record["avg_confidence"] if conf_record else 0.0
            
            return NTDStatistics(
                total_ntd_nodes=ntd_count,
                total_documents=doc_count,
                total_relationships=rel_count,
                by_type=by_type,
                high_confidence_count=high_confidence_count,
                average_confidence=float(average_confidence) if average_confidence else 0.0
            )
            
    except Exception as e:
        logger.error(f"Error getting NTD statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting NTD statistics: {str(e)}")

@ntd_router.get("/search", response_model=List[NTDNode])
async def search_ntd(
    query: str = Query(..., description="Search query for NTD"),
    doc_type: Optional[str] = Query(None, description="Filter by document type"),
    min_confidence: float = Query(0.0, description="Minimum confidence threshold"),
    limit: int = Query(50, description="Maximum number of results"),
    neo4j_driver = Depends(get_neo4j_db)
):
    """Поиск НТД по запросу"""
    try:
        with neo4j_driver.session() as session:
            # Базовый запрос
            cypher_query = """
                MATCH (n:NTD)
                WHERE n.canonical_id CONTAINS $query 
                   OR n.full_text CONTAINS $query
                   OR n.context CONTAINS $query
            """
            params = {"query": query}
            
            # Добавляем фильтры
            if doc_type:
                cypher_query += " AND n.document_type = $doc_type"
                params["doc_type"] = doc_type
            
            cypher_query += " AND n.confidence >= $min_confidence"
            params["min_confidence"] = min_confidence
            
            cypher_query += """
                RETURN n.canonical_id as canonical_id,
                       n.document_type as document_type,
                       n.full_text as full_text,
                       n.context as context,
                       n.confidence as confidence,
                       n.reference_count as reference_count
                ORDER BY n.confidence DESC
                LIMIT $limit
            """
            params["limit"] = limit
            
            result = session.run(cypher_query, params)
            ntd_nodes = []
            
            for record in result:
                ntd_nodes.append(NTDNode(
                    canonical_id=record["canonical_id"],
                    document_type=record["document_type"],
                    full_text=record["full_text"],
                    context=record["context"],
                    confidence=record["confidence"],
                    reference_count=record["reference_count"] or 0
                ))
            
            return ntd_nodes
            
    except Exception as e:
        logger.error(f"Error searching NTD: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching NTD: {str(e)}")

@ntd_router.get("/network", response_model=NTDNetwork)
async def get_ntd_network(
    canonical_id: Optional[str] = Query(None, description="Center the network around this NTD"),
    depth: int = Query(2, description="Network depth"),
    limit: int = Query(100, description="Maximum number of nodes"),
    neo4j_driver = Depends(get_neo4j_db)
):
    """Получает сеть связей НТД"""
    try:
        with neo4j_driver.session() as session:
            if canonical_id:
                # Сеть вокруг конкретного НТД
                cypher_query = """
                    MATCH (center:NTD {canonical_id: $canonical_id})
                    MATCH path = (center)-[*1..$depth]-(connected:NTD)
                    RETURN DISTINCT connected, path
                    LIMIT $limit
                """
                params = {"canonical_id": canonical_id, "depth": depth, "limit": limit}
            else:
                # Общая сеть
                cypher_query = """
                    MATCH (n:NTD)-[r]-(connected:NTD)
                    RETURN DISTINCT n, connected, r
                    LIMIT $limit
                """
                params = {"limit": limit}
            
            result = session.run(cypher_query, params)
            
            nodes = []
            relationships = []
            seen_nodes = set()
            seen_relationships = set()
            
            for record in result:
                # Обрабатываем узлы
                if "n" in record:
                    node = record["n"]
                    node_id = node["canonical_id"]
                    if node_id not in seen_nodes:
                        nodes.append(NTDNode(
                            canonical_id=node_id,
                            document_type=node.get("document_type", ""),
                            full_text=node.get("full_text", ""),
                            context=node.get("context", ""),
                            confidence=node.get("confidence", 0.0),
                            reference_count=node.get("reference_count", 0)
                        ))
                        seen_nodes.add(node_id)
                
                if "connected" in record:
                    connected = record["connected"]
                    connected_id = connected["canonical_id"]
                    if connected_id not in seen_nodes:
                        nodes.append(NTDNode(
                            canonical_id=connected_id,
                            document_type=connected.get("document_type", ""),
                            full_text=connected.get("full_text", ""),
                            context=connected.get("context", ""),
                            confidence=connected.get("confidence", 0.0),
                            reference_count=connected.get("reference_count", 0)
                        ))
                        seen_nodes.add(connected_id)
                
                # Обрабатываем связи
                if "r" in record:
                    rel = record["r"]
                    rel_key = f"{rel.start_node['canonical_id']}-{rel.end_node['canonical_id']}"
                    if rel_key not in seen_relationships:
                        relationships.append(NTDRelationship(
                            source=rel.start_node["canonical_id"],
                            target=rel.end_node["canonical_id"],
                            relationship_type=rel.type,
                            created_at=str(rel.get("created_at", ""))
                        ))
                        seen_relationships.add(rel_key)
            
            return NTDNetwork(nodes=nodes, relationships=relationships)
            
    except Exception as e:
        logger.error(f"Error getting NTD network: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting NTD network: {str(e)}")

@ntd_router.get("/document/{doc_id}/references", response_model=List[NTDReference])
async def get_document_ntd_references(
    doc_id: str,
    neo4j_driver = Depends(get_neo4j_db)
):
    """Получает НТД ссылки для конкретного документа"""
    try:
        with neo4j_driver.session() as session:
            cypher_query = """
                MATCH (doc:Document {id: $doc_id})-[r:REFERENCES_NTD]->(ntd:NTD)
                RETURN ntd.canonical_id as canonical_id,
                       ntd.document_type as document_type,
                       r.confidence as confidence,
                       r.context as context,
                       r.position as position
                ORDER BY r.confidence DESC
            """
            
            result = session.run(cypher_query, {"doc_id": doc_id})
            references = []
            
            for record in result:
                references.append(NTDReference(
                    canonical_id=record["canonical_id"],
                    document_type=record["document_type"],
                    confidence=record["confidence"],
                    context=record["context"],
                    position=record["position"]
                ))
            
            return references
            
    except Exception as e:
        logger.error(f"Error getting document NTD references: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting document NTD references: {str(e)}")

@ntd_router.get("/ntd/{canonical_id}/documents", response_model=List[Dict[str, Any]])
async def get_ntd_referencing_documents(
    canonical_id: str,
    neo4j_driver = Depends(get_neo4j_db)
):
    """Получает документы, которые ссылаются на конкретный НТД"""
    try:
        with neo4j_driver.session() as session:
            cypher_query = """
                MATCH (doc:Document)-[r:REFERENCES_NTD]->(ntd:NTD {canonical_id: $canonical_id})
                RETURN doc.id as doc_id,
                       doc.title as title,
                       doc.canonical_id as doc_canonical_id,
                       r.confidence as confidence,
                       r.context as context
                ORDER BY r.confidence DESC
            """
            
            result = session.run(cypher_query, {"canonical_id": canonical_id})
            documents = []
            
            for record in result:
                documents.append({
                    "doc_id": record["doc_id"],
                    "title": record["title"],
                    "doc_canonical_id": record["doc_canonical_id"],
                    "confidence": record["confidence"],
                    "context": record["context"]
                })
            
            return documents
            
    except Exception as e:
        logger.error(f"Error getting NTD referencing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting NTD referencing documents: {str(e)}")

@ntd_router.get("/types", response_model=List[Dict[str, Any]])
async def get_ntd_types(neo4j_driver = Depends(get_neo4j_db)):
    """Получает список всех типов НТД"""
    try:
        with neo4j_driver.session() as session:
            cypher_query = """
                MATCH (n:NTD)
                RETURN n.document_type as type, count(n) as count
                ORDER BY count DESC
            """
            
            result = session.run(cypher_query)
            types = []
            
            for record in result:
                types.append({
                    "type": record["type"],
                    "count": record["count"]
                })
            
            return types
            
    except Exception as e:
        logger.error(f"Error getting NTD types: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting NTD types: {str(e)}")

@ntd_router.get("/registry/view", response_model=Dict[str, Any])
async def get_registry_view(
    limit: int = Query(1000, description="Maximum number of nodes to return"),
    neo4j_driver = Depends(get_neo4j_db)
):
    """Получает полный вид реестра НТД для просмотра и визуализации"""
    try:
        # Импортируем EnterpriseRAGTrainer для использования новых методов
        from enterprise_rag_trainer_full import EnterpriseRAGTrainer
        
        # Создаем экземпляр тренера (только для доступа к методам)
        trainer = EnterpriseRAGTrainer()
        trainer.neo4j = neo4j
        
        # Получаем данные реестра
        registry_data = trainer.get_ntd_registry_view(limit=limit)
        
        return registry_data
        
    except Exception as e:
        logger.error(f"Error getting NTD registry view: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting NTD registry view: {str(e)}")

@ntd_router.post("/registry/export")
async def export_registry(
    format: str = Query("json", description="Export format: json or csv"),
    output_file: str = Query("ntd_registry_export", description="Output file name (without extension)"),
    neo4j_driver = Depends(get_neo4j_db)
):
    """Экспортирует реестр НТД в JSON или CSV формат"""
    try:
        # Импортируем EnterpriseRAGTrainer для использования новых методов
        from enterprise_rag_trainer_full import EnterpriseRAGTrainer
        
        # Создаем экземпляр тренера (только для доступа к методам)
        trainer = EnterpriseRAGTrainer()
        trainer.neo4j = neo4j
        
        # Экспортируем реестр
        export_result = trainer.export_ntd_registry(format=format, output_file=output_file)
        
        return export_result
        
    except Exception as e:
        logger.error(f"Error exporting NTD registry: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting NTD registry: {str(e)}")

@ntd_router.get("/registry/statistics", response_model=Dict[str, Any])
async def get_registry_statistics(neo4j_driver = Depends(get_neo4j_db)):
    """Получает детальную статистику по реестру НТД"""
    try:
        # Импортируем EnterpriseRAGTrainer для использования новых методов
        from enterprise_rag_trainer_full import EnterpriseRAGTrainer
        
        # Создаем экземпляр тренера (только для доступа к методам)
        trainer = EnterpriseRAGTrainer()
        trainer.neo4j = neo4j
        
        # Получаем статистику
        statistics = trainer.get_ntd_statistics()
        
        return statistics
        
    except Exception as e:
        logger.error(f"Error getting NTD registry statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting NTD registry statistics: {str(e)}")

# Health check endpoint
@ntd_router.get("/health")
async def health_check():
    """Проверка состояния API НТД"""
    return {"status": "healthy", "service": "NTD Registry API"}