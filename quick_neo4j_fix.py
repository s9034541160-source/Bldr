#!/usr/bin/env python3
"""
Quick Neo4j connection fix and verification script.
"""

import os
from neo4j import GraphDatabase

def check_neo4j_connection():
    """Check if Neo4j is accessible with the updated URI."""
    # Load environment variables
    neo4j_uri = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', 'neopassword')
    
    print(f"Checking Neo4j connection...")
    print(f"URI: {neo4j_uri}")
    print(f"User: {neo4j_user}")
    
    try:
        # Attempt to connect
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful' as message")
            record = result.single()
            if record:
                message = record["message"]
                print(f"✅ {message}")
            else:
                print("✅ Connection successful (no record returned)")
            driver.close()
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = check_neo4j_connection()
    if success:
        print("\n🎉 Neo4j connection is properly configured!")
        print("You can now run start_bldr.ps1 to start all services.")
    else:
        print("\n⚠️  Please check your Neo4j configuration and ensure the database is running.")