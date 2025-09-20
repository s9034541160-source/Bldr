"""
Frontend Integration Test
Tests the integration between frontend components without backend dependencies
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_projects_component_structure():
    """Test that the Projects component has the required structure"""
    # Check if the Projects component file exists
    projects_file = Path("web/bldr_dashboard/src/components/Projects.tsx")
    assert projects_file.exists(), "Projects.tsx file should exist"
    
    # Read the file content
    with open(projects_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for required elements
    assert "edit-project" in content, "Should have edit project functionality"
    assert "delete-project" in content, "Should have delete project functionality"
    assert "attach-files" in content, "Should have attach files functionality"
    assert "scan-project-files" in content, "Should have scan files functionality"
    assert "Результаты" in content, "Should have project results functionality"
    
    print("✓ Projects component structure test passed")

def test_pro_features_component_structure():
    """Test that the ProFeatures component has the required structure"""
    # Check if the ProFeatures component file exists
    pro_features_file = Path("web/bldr_dashboard/src/components/ProFeaturesNew.tsx")
    assert pro_features_file.exists(), "ProFeaturesNew.tsx file should exist"
    
    # Read the file content
    with open(pro_features_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for required elements
    assert "handleProjectSelect" in content, "Should have project selection handler"
    assert "tool-project-select" in content, "Should have project selection dropdown"
    assert "Пакетный Парсинг Смет" in content, "Should have batch estimate parsing tab"
    assert "project_id" in content, "Should handle project ID in forms"
    assert "saveProjectResult" in content, "Should save results to projects"
    assert "getProjectResults" in content, "Should retrieve project results"
    
    print("✓ ProFeatures component structure test passed")

def test_api_service_integration():
    """Test that the API service has the required project methods"""
    # Check if the API service file exists
    api_service_file = Path("web/bldr_dashboard/src/services/api.ts")
    assert api_service_file.exists(), "api.ts file should exist"
    
    # Read the file content
    with open(api_service_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for required methods
    assert "getProjectResults" in content, "Should have getProjectResults method"
    assert "saveProjectResult" in content, "Should have saveProjectResult method"
    assert "addProjectFiles" in content, "Should have addProjectFiles method"
    assert "scanDirectoryForProject" in content, "Should have scanDirectoryForProject method"
    
    print("✓ API service integration test passed")

def test_backend_api_endpoints():
    """Test that the backend has the required API endpoints"""
    # Check if the projects API file exists
    projects_api_file = Path("core/projects_api.py")
    assert projects_api_file.exists(), "projects_api.py file should exist"
    
    # Read the file content
    with open(projects_api_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for required endpoints
    assert "/{project_id}/results" in content, "Should have project results endpoints"
    assert "save_project_result" in content, "Should have save_project_result method"
    assert "get_project_results" in content, "Should have get_project_results method"
    assert "scan_directory_for_project" in content, "Should have scan_directory_for_project method"
    
    print("✓ Backend API endpoints test passed")

def test_full_integration_flow():
    """Test the full integration flow"""
    print("Testing full integration flow...")
    
    # Test each component
    test_projects_component_structure()
    test_pro_features_component_structure()
    test_api_service_integration()
    test_backend_api_endpoints()
    
    print("🎉 Full frontend integration test completed successfully!")

if __name__ == "__main__":
    print("Running frontend integration tests...")
    test_full_integration_flow()