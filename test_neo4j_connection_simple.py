#!/usr/bin/env python3
"""
Simple Neo4j connection test using the credentials from .env
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

# Get configuration from environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neopassword")

print(f"Testing Neo4j connection with:")
print(f"  URI: {NEO4J_URI}")
print(f"  User: {NEO4J_USER}")
print(f"  Password: {NEO4J_PASSWORD}")
print()

try:
    # Attempt to connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    # Test the connection
    with driver.session() as session:
        result = session.run("RETURN 1 AS result")
        record = result.single()
        if record and record["result"] == 1:
            print("✅ Successfully connected to Neo4j!")
        else:
            print("❌ Unexpected result from Neo4j")
    
    driver.close()
    
except Exception as e:
    print(f"❌ Failed to connect to Neo4j: {e}")
    print()
    print("Common issues and solutions:")
    print("1. Make sure Neo4j Desktop is running")
    print("2. Make sure your database instance is started")
    print("3. Verify your credentials are correct")
    print("4. Check if the database is using the correct port (7687)")
    print("5. If you've changed the password, update your .env file")