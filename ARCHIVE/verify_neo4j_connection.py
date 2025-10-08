#!/usr/bin/env python3
"""
Simple script to verify Neo4j connection with current credentials
"""

import os
from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

def verify_neo4j_connection():
    """Verify Neo4j connection with current credentials"""
    # Load environment variables
    neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "neopassword")
    
    print(f"Testing Neo4j connection...")
    print(f"URI: {neo4j_uri}")
    print(f"User: {neo4j_user}")
    print(f"Password: {'*' * len(neo4j_password)}")
    print()
    
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful' as message")
            record = result.single()
            if record:
                print("✅ SUCCESS: Connected to Neo4j successfully!")
                print(f"Message: {record['message']}")
                driver.close()
                return True
    except AuthError as e:
        print("❌ AUTHENTICATION FAILED:")
        print(f"Error: {e}")
        print()
        print("Possible causes:")
        print("1. Incorrect username or password")
        print("2. Neo4j authentication rate limit (wait a few minutes and try again)")
        print("3. Neo4j service not running")
        print()
        print("To fix:")
        print("1. Verify your Neo4j credentials in the .env file")
        print("2. Restart Neo4j Desktop and your database instance")
        print("3. Wait a few minutes if you've had many failed attempts")
        return False
    except ServiceUnavailable as e:
        print("❌ SERVICE UNAVAILABLE:")
        print(f"Error: {e}")
        print()
        print("Possible causes:")
        print("1. Neo4j service not running")
        print("2. Incorrect URI or port")
        print("3. Network connectivity issues")
        print()
        print("To fix:")
        print("1. Make sure Neo4j Desktop is running")
        print("2. Make sure your database instance is started")
        print("3. Check that the URI and port are correct")
        return False
    except Exception as e:
        print("❌ CONNECTION FAILED:")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    verify_neo4j_connection()