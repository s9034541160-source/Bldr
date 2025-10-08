#!/usr/bin/env python3
"""
Quick reset of RAG data (non-interactive)

Actions:
- Drop and recreate Qdrant collection `enterprise_docs`
- Wipe Neo4j graph (DETACH DELETE all)
- Remove local caches and trainer artifacts (JSON, PKL, reports)
- Remove processed_files.json and file_moves.json

Safe to run multiple times. Requires Qdrant (HTTP) and Neo4j accessible.
"""

import os
import shutil
from pathlib import Path

BASE_DIR = Path(os.getenv("BASE_DIR", "I:/docs"))

def reset_qdrant():
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import Distance, VectorParams
        client = QdrantClient(host="localhost", port=6333)
        cols = [c.name for c in client.get_collections().collections]
        if "enterprise_docs" in cols:
            client.delete_collection(collection_name="enterprise_docs")
        client.create_collection(
            collection_name="enterprise_docs",
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        )
        print("✅ Qdrant: enterprise_docs reset")
    except Exception as e:
        print(f"⚠️ Qdrant reset error: {e}")

def reset_qdrant_docker():
    """Reset Qdrant via Docker (stops, removes, recreates)"""
    import subprocess
    import time
    
    try:
        # Stop and remove Qdrant container
        subprocess.run(["docker", "compose", "stop", "qdrant"], 
                      capture_output=True, text=True, timeout=30)
        subprocess.run(["docker", "compose", "rm", "-f", "qdrant"], 
                      capture_output=True, text=True, timeout=30)
        
        # Remove Qdrant volumes
        result = subprocess.run(["docker", "volume", "ls", "--format", "{{.Name}}"], 
                               capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            volumes = result.stdout.strip().split('\n')
            for vol in volumes:
                if 'qdrant' in vol.lower():
                    subprocess.run(["docker", "volume", "rm", "-f", vol], 
                                  capture_output=True, text=True, timeout=30)
        
        # Start Qdrant again
        subprocess.run(["docker", "compose", "up", "-d", "qdrant"], 
                      capture_output=True, text=True, timeout=30)
        
        # Wait for Qdrant to be ready
        time.sleep(8)
        
        # Verify it's working
        result = subprocess.run(["curl", "http://localhost:6333/collections"], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and '"collections":[]' in result.stdout:
            print("✅ Qdrant: Docker reset complete")
        else:
            print("⚠️ Qdrant: Docker reset may have issues")
            
    except Exception as e:
        print(f"⚠️ Qdrant Docker reset error: {e}")

def reset_neo4j():
    try:
        from neo4j import GraphDatabase
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "neopassword")
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        driver.close()
        print("✅ Neo4j: graph cleared")
    except Exception as e:
        print(f"⚠️ Neo4j reset error: {e}")

def reset_neo4j_docker():
    """Reset Neo4j via Docker (stops, removes volumes, recreates)"""
    import subprocess
    import time
    
    try:
        # Stop and remove Neo4j container
        subprocess.run(["docker", "compose", "stop", "neo4j"], 
                      capture_output=True, text=True, timeout=30)
        subprocess.run(["docker", "compose", "rm", "-f", "neo4j"], 
                      capture_output=True, text=True, timeout=30)
        
        # Remove Neo4j volumes
        result = subprocess.run(["docker", "volume", "ls", "--format", "{{.Name}}"], 
                               capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            volumes = result.stdout.strip().split('\n')
            for vol in volumes:
                if 'neo4j' in vol.lower():
                    subprocess.run(["docker", "volume", "rm", "-f", vol], 
                                  capture_output=True, text=True, timeout=30)
        
        # Start Neo4j again
        subprocess.run(["docker", "compose", "up", "-d", "neo4j"], 
                      capture_output=True, text=True, timeout=30)
        
        # Wait for Neo4j to be ready
        time.sleep(15)
        
        # Verify it's working
        result = subprocess.run(["docker", "exec", "bldr_neo4j", "cypher-shell", "-u", "neo4j", "-p", "neopassword", "RETURN 1"], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Neo4j: Docker reset complete")
        else:
            print("⚠️ Neo4j: Docker reset may have issues")
            
    except Exception as e:
        print(f"⚠️ Neo4j Docker reset error: {e}")

def remove_path(p: Path):
    if not p.exists():
        return 0
    try:
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return 1
    except Exception:
        return 0

def reset_local_artifacts():
    removed = 0
    # Trainer artifacts
    for rel in [
        "cache",
        "embedding_cache",
        "reports",
        "qdrant_db",  # local fallback storage if used
    ]:
        removed += remove_path(BASE_DIR / rel)

    # Top-level known artifacts
    for rel in [
        "cache",
        "training_logs",
        "rag_logs",
        "faiss_index.index",
        "processed_files.json",
        "file_moves.json",
    ]:
        removed += remove_path(Path.cwd() / rel)

    # Purge JSON/PKL cache files inside BASE_DIR recursively
    purged = 0
    for pattern in ["*.json", "*.pkl", "*.cache", "*.tmp"]:
        for f in BASE_DIR.rglob(pattern):
            # keep settings.json
            if f.name == "settings.json":
                continue
            try:
                f.unlink()
                purged += 1
            except Exception:
                pass
    print(f"✅ Local artifacts removed: dirs/files removed={removed}, files purged={purged}")

def main():
    print("💥 QUICK RESET RAG DATA")
    # Try Docker reset first (more thorough), fallback to API reset
    reset_qdrant_docker()
    reset_neo4j_docker()
    reset_local_artifacts()
    print("🎉 Done. You have a clean slate.")

if __name__ == "__main__":
    main()


