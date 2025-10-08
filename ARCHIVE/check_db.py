from neo4j import GraphDatabase
import os

# Connect to Neo4j
driver = GraphDatabase.driver('neo4j://localhost:7687', auth=('neo4j', 'neopassword'))

try:
    with driver.session() as session:
        # Count total nodes
        result = session.run('MATCH (n) RETURN count(n) as count')
        record = result.single()
        total_nodes = record["count"] if record else 0
        print(f"Total nodes in database: {total_nodes}")
        
        # Count NormDoc nodes
        result = session.run('MATCH (n:NormDoc) RETURN count(n) as count')
        record = result.single()
        normdoc_nodes = record["count"] if record else 0
        print(f"NormDoc nodes: {normdoc_nodes}")
        
        # Show some NormDoc nodes
        if normdoc_nodes > 0:
            result = session.run('MATCH (n:NormDoc) RETURN n LIMIT 5')
            print("\nSample NormDoc nodes:")
            for record in result:
                node = record["n"]
                print(f"  ID: {node.get('id', 'N/A')}")
                print(f"  Name: {node.get('name', 'N/A')}")
                print(f"  Category: {node.get('category', 'N/A')}")
                print(f"  Path: {node.get('path', 'N/A')}")
                print()
        
finally:
    driver.close()