#!/usr/bin/env python3
"""
Comprehensive Neo4j connection test with multiple credential combinations
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

# Get configuration from environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")

# Common password combinations to test
password_combinations = [
    os.getenv("NEO4J_PASSWORD", "neopassword"),  # From .env
    "neopassword",  # What you specified
    "neo4j",  # Default Neo4j password
    "password",  # Common default
    "admin",  # Common default
    "bldr",  # Possible custom password
]

print(f"Testing Neo4j connection with URI: {NEO4J_URI} and user: {NEO4J_USER}")
print("=" * 60)
print()

# Test each password combination
for i, password in enumerate(password_combinations, 1):
    print(f"Test {i}: Trying password '{password}'")
    try:
        # Attempt to connect to Neo4j
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, password), connection_timeout=10)
        
        # Test the connection
        with driver.session() as session:
            result = session.run("RETURN 1 AS result")
            record = result.single()
            if record and record["result"] == 1:
                print(f"✅ SUCCESS! Connected with password: '{password}'")
                print(f"   This should be your correct password!")
                print()
                driver.close()
                break
            else:
                print(f"❌ Unexpected result with password: '{password}'")
        
        driver.close()
        
    except Exception as e:
        if "Unauthorized" in str(e) or "unauthorized" in str(e).lower():
            print(f"❌ Authentication failed with password: '{password}'")
        else:
            print(f"❌ Connection failed with password: '{password}' - {e}")
    print()

print("=" * 60)
print("If none of the above worked, please check:")
print("1. Is Neo4j Desktop running?")
print("2. Is your database instance started?")
print("3. Is the database using the correct port (7687)?")
print("4. Have you set the correct password in Neo4j Desktop?")
print("5. Is there a firewall blocking the connection?")