import os
from neo4j import GraphDatabase

# Use default values from the project
neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "neopassword")

print(f"Connecting to Neo4j at {neo4j_uri} with user {neo4j_user}")

try:
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    print("Driver created successfully")
    
    # Test connection
    with driver.session() as session:
        result = session.run("RETURN 1 as test")
        record = result.single()
        if record:
            print(f"Connection test result: {record['test']}")
        else:
            print("Connection test returned no results")
        
        # Test project query
        try:
            result = session.run("MATCH (p:Project) RETURN count(p) as count")
            record = result.single()
            if record:
                print(f"Project count: {record['count']}")
            else:
                print("Project query returned no results")
        except Exception as e:
            print(f"Error querying projects: {e}")
            
    print("All tests passed!")
    driver.close()
    
except Exception as e:
    print(f"Error connecting to Neo4j: {e}")