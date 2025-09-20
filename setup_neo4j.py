#!/usr/bin/env python3
"""
Script to set up Neo4j database for Bldr Empire v2
This script will:
1. Check if Neo4j is running
2. Update the .env file with the correct credentials
"""

import os
import sys
import time
from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

def check_neo4j_connection():
    """Check Neo4j connection with default credentials"""
    uri = "neo4j://localhost:7687"
    user = "neo4j"
    password = "neopassword"
    
    print("[INFO] Checking Neo4j connection...")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
        print("[INFO] Neo4j is accessible with default credentials")
        return True
    except AuthError:
        print("[ERROR] Authentication failed with default credentials")
        return False
    except ServiceUnavailable as e:
        print(f"[ERROR] Neo4j service unavailable: {e}")
        print("[INFO] Please make sure Neo4j is running before running this script")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to connect to Neo4j: {e}")
        return False

def update_env_file():
    """Update .env file with correct Neo4j credentials"""
    env_content = """NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neopassword
REDIS_URL=redis://localhost:6379
"""
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("[INFO] .env file updated with default credentials")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update .env file: {e}")
        return False

def main():
    """Main function to set up Neo4j"""
    print("==========================================")
    print("   Bldr Empire v2 - Neo4j Setup Script")
    print("==========================================")
    
    # Check Neo4j connection
    if check_neo4j_connection():
        # Update .env file
        if update_env_file():
            print("[SUCCESS] Neo4j setup completed successfully!")
            print("[INFO] Using default credentials (neo4j/neo4j)")
            return 0
        else:
            print("[ERROR] Failed to update .env file")
            return 1
    else:
        print("[ERROR] Failed to connect to Neo4j")
        print("[INFO] Please make sure Neo4j is running and accessible on neo4j://localhost:7687")
        return 1

if __name__ == "__main__":
    sys.exit(main())