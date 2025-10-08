import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.projects_api import ProjectManager

# Test the ProjectManager directly
neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "neopassword")

print(f"Creating ProjectManager with URI: {neo4j_uri}")

try:
    project_manager = ProjectManager(neo4j_uri, neo4j_user, neo4j_password)
    print("ProjectManager created successfully")
    
    # Test get_projects
    print("Testing get_projects...")
    projects = project_manager.get_projects()
    print(f"Found {len(projects)} projects")
    
    # Test create_project
    print("Testing create_project...")
    from core.projects_api import ProjectCreate
    project_data = ProjectCreate(name="Test Project Direct", code="TPD001", status="testing")
    created_project = project_manager.create_project(project_data)
    print(f"Created project: {created_project['name']} with ID {created_project['id']}")
    
    print("All tests passed!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()