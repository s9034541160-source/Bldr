#!/usr/bin/env python3
"""
Script to run the full 14-stage RAG training pipeline on the updated NTD database
"""

import os
import sys
from pathlib import Path
import tempfile

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from scripts.bldr_rag_trainer import BldrRAGTrainer

def main():
    """Main function to run the RAG training pipeline"""
    print("🚀 Starting full 14-stage RAG training pipeline...")
    
    # Create a temporary directory for Qdrant to avoid conflicts
    with tempfile.TemporaryDirectory() as temp_qdrant_path:
        # Initialize the RAG trainer
        # Use the directory where our downloaded documents are stored
        base_dir_env = os.getenv("BASE_DIR", "I:/docs")
        trainer = BldrRAGTrainer(
            base_dir=os.path.join(base_dir_env, "ntd", "construction"),
            neo4j_uri='neo4j://localhost:7687',
            neo4j_user='neo4j',
            neo4j_pass='neopassword',
            qdrant_path=temp_qdrant_path,
            reports_dir=os.path.join(base_dir_env, "reports")
        )
        
        # Run the full training pipeline
        print("📚 Starting training process...")
        trainer.train()
        
        # Test the trained model with a sample query
        print("\n🔍 Testing trained model with sample query...")
        test_query = "Какие нормы СП 31.13330.2012 применяются для проектирования водопровода?"
        results = trainer.query(test_query, k=3)
        
        print(f"\n📝 Query: {test_query}")
        print(f"📊 Results ({len(results.get('results', []))} found):")
        
        for i, result in enumerate(results.get('results', [])):
            print(f"\n--- Result {i+1} ---")
            print(f"Score: {result.get('score', 0)}")
            print(f"Chunk: {result.get('chunk', '')[:200]}...")
            print(f"Tezis: {result.get('tezis', '')}")
            print(f"Violations: {result.get('viol', 0)}")
        
        print("\n🎉 RAG training pipeline completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())