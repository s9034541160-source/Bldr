from neo4j import GraphDatabase
import sys

# Connect to Neo4j system database with default credentials
uri = "bolt://localhost:7687"
user = "neo4j"
password = "neopassword"
new_password = "neopassword"

try:
    # Connect to system database with default credentials
    driver = GraphDatabase.driver(uri, auth=(user, password), database="system")
    with driver.session() as session:
        # Change password
        session.run("ALTER CURRENT USER SET PASSWORD FROM $old_password TO $new_password", 
                   old_password=password, new_password=new_password)
        print("Password changed successfully")
    driver.close()
except Exception as e:
    print(f"Error changing password: {e}")
    sys.exit(1)