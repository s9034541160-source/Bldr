#!/usr/bin/env python3
"""
Скрипт для запуска RAG-обучения на базе НТД с предобработкой Stage 0
"""

import os
import sys
import time
import glob
from pathlib import Path
from typing import List

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from scripts.bldr_rag_trainer import BldrRAGTrainer
from core.ntd_preprocessor import NormativeDatabase, NormativeChecker
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ntd_rag_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def find_documents(base_path: str, extensions: List[str] = None) -> List[str]:
    """Find all documents in base path"""
    if extensions is None:
        extensions = ['.pdf', '.docx', '.doc', '.txt']
    
    documents = []
    for ext in extensions:
        pattern = os.path.join(base_path, "**", f"*{ext}")
        files = glob.glob(pattern, recursive=True)
        documents.extend(files)
    
    logger.info(f"Found {len(documents)} documents in {base_path}")
    return documents

def main():
    """Main function for NTD RAG training"""
    
    # Configuration
    BASE_DIR = os.getenv("BASE_DIR", "I:/docs")
    NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "neopassword")
    
    # Paths
    ntd_base_path = os.path.join(BASE_DIR, "БАЗА")  # Основная база НТД
    projects_path = os.path.join(BASE_DIR, "ПРОЕКТЫ")  # Проекты
    clean_base_path = os.path.join(BASE_DIR, "clean_base")  # Очищенная база
    qdrant_path = os.path.join(BASE_DIR, "qdrant_db")
    reports_path = os.path.join(BASE_DIR, "reports")
    
    logger.info("🚀 Starting NTD RAG Training with Stage 0 preprocessing")
    logger.info(f"Base directory: {BASE_DIR}")
    logger.info(f"NTD base path: {ntd_base_path}")
    logger.info(f"Projects path: {projects_path}")
    
    try:
        # Initialize BldrRAGTrainer with NTD preprocessing enabled
        trainer = BldrRAGTrainer(
            base_dir=clean_base_path,
            neo4j_uri=NEO4J_URI,
            neo4j_user=NEO4J_USER,
            neo4j_pass=NEO4J_PASS,
            qdrant_path=qdrant_path,
            norms_db=clean_base_path,
            reports_dir=reports_path,
            use_advanced_embeddings=True  # Use advanced Russian model
        )
        
        # Find all documents
        logger.info("📁 Searching for documents...")
        all_documents = []
        
        if os.path.exists(ntd_base_path):
            ntd_docs = find_documents(ntd_base_path)
            all_documents.extend(ntd_docs)
            logger.info(f"Found {len(ntd_docs)} NTD documents")
        
        if os.path.exists(projects_path):
            project_docs = find_documents(projects_path)
            all_documents.extend(project_docs)
            logger.info(f"Found {len(project_docs)} project documents")
        
        if not all_documents:
            logger.error("No documents found! Please check paths:")
            logger.error(f"  - NTD path: {ntd_base_path} (exists: {os.path.exists(ntd_base_path)})")
            logger.error(f"  - Projects path: {projects_path} (exists: {os.path.exists(projects_path)})")
            return
        
        logger.info(f"📊 Total documents to process: {len(all_documents)}")
        
        # Process documents with progress tracking
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for i, doc_path in enumerate(all_documents, 1):
            try:
                logger.info(f"🔄 Processing {i}/{len(all_documents)}: {os.path.basename(doc_path)}")
                
                # Process document through 14-stage pipeline including Stage 0 NTD preprocessing
                result = trainer.process_document(doc_path)
                
                if result:
                    success_count += 1
                    logger.info(f"✅ Successfully processed: {os.path.basename(doc_path)}")
                else:
                    skipped_count += 1
                    logger.warning(f"⏭️ Skipped (duplicate/too short): {os.path.basename(doc_path)}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error processing {doc_path}: {e}")
                
            # Progress update every 10 documents
            if i % 10 == 0:
                logger.info(f"📈 Progress: {i}/{len(all_documents)} ({i/len(all_documents)*100:.1f}%) - Success: {success_count}, Errors: {error_count}, Skipped: {skipped_count}")
        
        # Final statistics
        logger.info("🎉 NTD RAG Training completed!")
        logger.info(f"📊 Final Statistics:")
        logger.info(f"  - Total documents: {len(all_documents)}")
        logger.info(f"  - Successfully processed: {success_count}")
        logger.info(f"  - Errors: {error_count}")
        logger.info(f"  - Skipped (duplicates/too short): {skipped_count}")
        
        # Test the trained system
        if success_count > 0:
            logger.info("🧪 Testing the trained system...")
            try:
                # Test query
                test_query = "СП 45.13330"
                results = trainer.query(test_query, k=3)
                logger.info(f"✅ Test query '{test_query}' returned {len(results)} results")
                
                if results:
                    for i, result in enumerate(results[:2], 1):
                        logger.info(f"  Result {i}: {result.get('chunk', '')[:100]}... (score: {result.get('score', 0):.3f})")
                        
            except Exception as e:
                logger.error(f"❌ Error testing system: {e}")
        
        logger.info(f"📝 Training log saved to: ntd_rag_training.log")
        logger.info(f"📊 Reports saved to: {reports_path}")
        
    except Exception as e:
        logger.error(f"❌ Fatal error during training: {e}")
        raise

if __name__ == "__main__":
    main()