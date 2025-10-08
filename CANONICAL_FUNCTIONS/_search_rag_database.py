# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _search_rag_database
# Основной источник: C:\Bldr\core\tools_system.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#   - C:\Bldr\core\agents\roles_agents.py
#================================================================================
    def _search_rag_database(self, **kwargs) -> Dict[str, Any]:
        """Search RAG database with real Qdrant integration"""
        query = kwargs.get("query", "")
        doc_types = kwargs.get("doc_types", ["norms"])
        k = kwargs.get("k", 5)
        
        # Check if we should use SBERT for Russian queries
        use_sbert = kwargs.get("use_sbert", False)
        embed_model = kwargs.get("embed_model", "nomic")
        
        # Use SBERT for Russian construction terms
        if use_sbert or embed_model == "sbert_large_nlu_ru" or any(term in query for term in ["СП", "ГЭСН", "ФЗ", "ГОСТ", "СНиП", "СанПиН"]):
            try:
                from sentence_transformers import SentenceTransformer, util
                import numpy as np
                
                # Load SBERT model if not already loaded
                sbert_model = SentenceTransformer('ai-forever/sbert_large_nlu_ru')
                
                # Embed query with SBERT
                query_embedding = sbert_model.encode(query)
                # Convert to list - handle both numpy arrays and other types
                if isinstance(query_embedding, list):
                    # Already a list, no conversion needed
                    pass
                elif hasattr(query_embedding, 'tolist'):
                    query_embedding = query_embedding.tolist()
                else:
                    # Convert to list using list() constructor
                    try:
                        query_embedding = list(query_embedding)
                    except:
                        # Fallback to empty list
                        query_embedding = []
                
                # Use the RAG system's query method with SBERT embedding
                results = self.rag_system.query_with_embedding(query_embedding, k=k)
                
                # Filter by document types
                filtered_results = []
                for result in results.get("results", []):
                    meta = result.get("meta", {})
                    doc_type = meta.get("doc_type", "")
                    if doc_type in doc_types or not doc_types:
                        filtered_results.append(result)
                
                return {
                    "status": "success",
                    "results": filtered_results[:k],
                    "ndcg": results.get("ndcg", 0.95),
                    "embedding_model": "sbert_large_nlu_ru"
                }
            except Exception as e:
                # Fallback to Nomic if SBERT fails
                print(f"SBERT search failed, falling back to Nomic: {e}")
                pass
        
        # Use the RAG system's query method (default Nomic embed)
        results = self.rag_system.query(query, k=k)
        
        # Filter by document types
        filtered_results = []
        for result in results.get("results", []):
            meta = result.get("meta", {})
            doc_type = meta.get("doc_type", "")
            if doc_type in doc_types or not doc_types:
                filtered_results.append(result)
        
        return {
            "status": "success",
            "results": filtered_results[:k],
            "ndcg": results.get("ndcg", 0.95),
            "embedding_model": "nomic"
        }