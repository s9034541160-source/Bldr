from neo4j import GraphDatabase
import sys

# Common Neo4j credentials to test
credentials_to_test = [
    ("neo4j", "neopassword"),
    ("neo4j", "neo4j"),
    ("neo4j", "password"),
    ("neo4j", "admin"),
    ("admin", "admin"),
]

uri = "neo4j://localhost:7687"

for user, password in credentials_to_test:
    try:
        print(f"Testing {user}/{password}...")
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            result = session.run("RETURN 1")
            print(f"✅ SUCCESS: {user}/{password}")
            driver.close()
            sys.exit(0)
    except Exception as e:
        print(f"❌ FAILED: {user}/{password} - {str(e)}")
        continue

print("All credential combinations failed.")