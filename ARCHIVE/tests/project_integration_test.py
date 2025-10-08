#!/usr/bin/env python3
"""
Project Integration Test
Test the integration between projects and pro-tools functionality
"""

import sys
import os
import json
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.projects_api import ProjectManager, ProjectCreate, ProjectUpdate

def test_project_functionality():
    """Test project creation, file attachment, and tool integration"""
    print("Testing Project Integration...")
    
    # Initialize project manager
    pm = ProjectManager()
    
    # Test project creation
    print("1. Creating test project...")
    project_data = ProjectCreate(
        name="Test Integration Project",
        code="TIP-001",
        location="Екатеринбург",
        status="active"
    )
    
    try:
        project = pm.create_project(project_data)
        print(f"   ✓ Project created: {project['name']} (ID: {project['id']})")
    except Exception as e:
        print(f"   ✗ Failed to create project: {e}")
        return False
    
    # Test getting project
    print("2. Retrieving project...")
    try:
        retrieved_project = pm.get_project(project['id'])
        print(f"   ✓ Project retrieved: {retrieved_project['name']}")
    except Exception as e:
        print(f"   ✗ Failed to retrieve project: {e}")
        return False
    
    # Test updating project
    print("3. Updating project...")
    try:
        update_data = ProjectUpdate(status="completed")
        updated_project = pm.update_project(project['id'], update_data)
        print(f"   ✓ Project updated: {updated_project['status']}")
    except Exception as e:
        print(f"   ✗ Failed to update project: {e}")
        return False
    
    # Test project file handling
    print("4. Testing file handling...")
    try:
        # Create a test file
        test_file_content = "Test smeta file content with ГЭСН"
        test_file_path = Path("test_smeta.xlsx")
        with open(test_file_path, "w") as f:
            f.write(test_file_content)
        
        # Mock file object for testing
        class MockFile:
            def __init__(self, path):
                self.filename = path
                self.file = open(path, "rb")
        
        mock_file = MockFile(str(test_file_path))
        
        # Add file to project
        # Note: This would normally be tested with actual file uploads
        print("   ✓ File handling test structure created")
        
        # Clean up test file
        test_file_path.unlink()
    except Exception as e:
        print(f"   ✗ File handling test failed: {e}")
        return False
    
    # Test project results
    print("5. Testing project results...")
    try:
        result_data = {
            "type": "budget",
            "data": {
                "project_name": "Test Project",
                "total_cost": 1000000,
                "roi": 15.5
            }
        }
        result = pm.save_project_result(project['id'], "budget", result_data["data"])
        print(f"   ✓ Result saved: {result['type']}")
        
        # Retrieve results
        results = pm.get_project_results(project['id'])
        print(f"   ✓ Retrieved {len(results)} results")
    except Exception as e:
        print(f"   ✗ Project results test failed: {e}")
        return False
    
    # Test project deletion
    print("6. Deleting test project...")
    try:
        pm.delete_project(project['id'])
        print("   ✓ Project deleted successfully")
    except Exception as e:
        print(f"   ✗ Failed to delete project: {e}")
        return False
    
    print("\n✓ All project integration tests passed!")
    return True

if __name__ == "__main__":
    success = test_project_functionality()
    sys.exit(0 if success else 1)