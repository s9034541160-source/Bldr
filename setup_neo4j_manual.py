#!/usr/bin/env python3
"""
Script to help set up Neo4j database for Bldr Empire v2 manually
This script provides guidance for setting up Neo4j when auto-start is disabled.
"""

import os
import sys
import time
import subprocess
from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

def check_neo4j_running():
    """Check if Neo4j is running on the default port"""
    uri = "neo4j://localhost:7687"
    user = "neo4j"
    password = "neopassword"  # Default password
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
        return True
    except ServiceUnavailable:
        return False
    except Exception:
        # Might be running but with different credentials
        return True

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
    """Main function to guide Neo4j setup"""
    print("==========================================")
    print("   Bldr Empire v2 - Neo4j Manual Setup")
    print("==========================================")
    print()
    
    print("This script will help you set up Neo4j for Bldr Empire v2.")
    print("Since auto-start is disabled, you need to start Neo4j manually.")
    print()
    
    # Check if Neo4j is already running
    print("[INFO] Checking if Neo4j is running...")
    if check_neo4j_running():
        print("[INFO] Neo4j appears to be running.")
    else:
        print("[WARN] Neo4j does not appear to be running.")
        print()
        print("Please follow these steps to start Neo4j:")
        print("1. Open Neo4j Desktop")
        print("2. Create a new database instance or start an existing one")
        print("3. Make sure the database is configured to use:")
        print("   - Bolt port: 7687")
        print("   - HTTP port: 7474")
        print("4. Start the database instance")
        print("5. Use default credentials (neo4j/neo4j)")
        print()
        input("Press Enter after you have started Neo4j...")
    
    # Wait a bit for Neo4j to fully start
    print("[INFO] Waiting for Neo4j to fully start...")
    time.sleep(10)
    
    # Try to connect with default credentials
    uri = "neo4j://localhost:7687"
    user = "neo4j"
    password = "neopassword"  # Default password
    
    print("[INFO] Attempting to connect to Neo4j...")
    
    try:
        # Try with default password
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            print("[INFO] Connected with default credentials.")
        driver.close()
        print("[INFO] Neo4j connection verified successfully")
    except AuthError:
        print("[ERROR] Authentication failed with default credentials")
        print("[INFO] Please check your Neo4j credentials")
        return 1
    except ServiceUnavailable as e:
        print(f"[ERROR] Neo4j service unavailable: {e}")
        print("[INFO] Please make sure Neo4j is running and accessible on neo4j://localhost:7687")
        return 1
    except Exception as e:
        print(f"[ERROR] Failed to connect to Neo4j: {e}")
        return 1
    
    # Update .env file
    print("[INFO] Updating .env file...")
    if update_env_file():
        print("[SUCCESS] Neo4j setup completed successfully!")
        print("[INFO] Using default credentials (neo4j/neopassword)")
        print()
        print("You can now restart the Bldr Empire system.")
        print("The system will connect to Neo4j with the default credentials.")
        return 0
    else:
        print("[ERROR] Failed to update .env file")
        return 1

if __name__ == "__main__":
    sys.exit(main())