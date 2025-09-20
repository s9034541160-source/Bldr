#!/usr/bin/env python3
"""
Test script to verify Neo4j connection with default credentials
"""

import os
import sys
from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

def test_neo4j_connection():
    """Test Neo4j connection with default credentials"""
    uri = "neo4j://localhost:7687"
    user = "neo4j"
    password = "neopassword"
    
    print(f"[INFO] Testing Neo4j connection to {uri}")
    print(f"[INFO] Using credentials: {user}/{password}")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            result = session.run("RETURN 1 AS result")
            record = result.single()
            if record is not None:
                value = record["result"]
                if value == 1:
                    print("[SUCCESS] Connected to Neo4j successfully!")
                    print("[INFO] Default credentials are working")
                    driver.close()
                    return True
        driver.close()
    except AuthError as e:
        print(f"[ERROR] Authentication failed: {e}")
        return False
    except ServiceUnavailable as e:
        print(f"[ERROR] Neo4j service unavailable: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to connect to Neo4j: {e}")
        return False

if __name__ == "__main__":
    print("==========================================")
    print("   Neo4j Connection Test")
    print("==========================================")
    print()
    
    if test_neo4j_connection():
        print()
        print("[INFO] Neo4j is accessible with default credentials")
        sys.exit(0)
    else:
        print()
        print("[ERROR] Failed to connect to Neo4j")
        sys.exit(1)