#!/usr/bin/env python3
"""
Full Project-Tool Integration Test

This test verifies the complete flow:
1. Create a project
2. Attach files/folder to the project
3. Run tools on the project
4. Save results to the project
5. Retrieve results from the project
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from openpyxl import Workbook

# Add the core directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from core.projects_api import ProjectManager, ProjectCreate

def create_test_smeta_file(file_path):
    """Create a test smeta Excel file"""
    wb = Workbook()
    ws = wb.active
    if ws:
        ws.title = "Смета"
        
        # Add headers
        headers = ['Код', 'Наименование', 'Ед.изм.', 'Количество', 'Цена', 'Сумма']
        ws.append(headers)
    
    # Add sample data
    data = [
        ['ГЭСН 01-01-001-01', 'Подготовка строительной площадки', 'га', 1.5, 50000, 75000],
        ['ГЭСН 01-02-001-01', 'Устройство временных дорог', 'км', 2.0, 300000, 600000],
        ['ГЭСН 02-01-001-01', 'Разработка грунта экскаватором', 'м3', 1000, 150, 150000]
    ]
    
    if ws:
        for row in data:
            ws.append(row)
    
    wb.save(file_path)

def test_full_project_tool_integration():
    """Test the complete project-tool integration flow"""
    print("🧪 Testing full project-tool integration flow...")
    
    # Initialize project manager
    pm = ProjectManager()
    
    # 1. Create a project
    print("1. Creating project...")
    project_data = ProjectCreate(
        name="Тестовый проект интеграции",
        code="TEST-2025-001",
        location="Екатеринбург",
        status="active"
    )
    
    try:
        project = pm.create_project(project_data)
        project_id = project["id"]
        print(f"   ✅ Project created with ID: {project_id}")
    except Exception as e:
        print(f"   ❌ Failed to create project: {e}")
        return False
    
    # 2. Create test files
    print("2. Creating test files...")
    temp_dir = tempfile.mkdtemp()
    try:
        # Create test smeta file
        smeta_file = os.path.join(temp_dir, "test_smeta.xlsx")
        create_test_smeta_file(smeta_file)
        
        # Create test RD file
        rd_file = os.path.join(temp_dir, "test_rd.pdf")
        with open(rd_file, "w") as f:
            f.write("Тестовый файл РД")
        
        # Create test graph file
        graph_file = os.path.join(temp_dir, "test_gantt.mpp")
        with open(graph_file, "w") as f:
            f.write("Тестовый файл графика")
        
        print(f"   ✅ Test files created in: {temp_dir}")
    except Exception as e:
        print(f"   ❌ Failed to create test files: {e}")
        return False
    
    # 3. Attach files to project using directory scan
    print("3. Attaching files to project...")
    try:
        result = pm.scan_directory_for_project(project_id, temp_dir)
        print(f"   ✅ Files attached: {result['added']} files")
        print(f"      - Сметы: {result['smeta_count']}")
        print(f"      - РД: {result['rd_count']}")
        print(f"      - Графики: {result['graphs_count']}")
    except Exception as e:
        print(f"   ❌ Failed to attach files: {e}")
        return False
    
    # 4. Verify files were attached
    print("4. Verifying attached files...")
    try:
        files = pm.get_project_files(project_id)
        print(f"   ✅ Files retrieved: {len(files)} files")
        for file in files:
            print(f"      - {file['name']} ({file['type']})")
    except Exception as e:
        print(f"   ❌ Failed to retrieve files: {e}")
        return False
    
    # 5. Test tool result saving
    print("5. Testing tool result saving...")
    try:
        # Simulate a tool result
        tool_result = {
            "status": "success",
            "budget": {
                "project_name": "Тестовый проект интеграции",
                "total_cost": 1500000,
                "sections": [
                    {"code": "ГЭСН 01", "name": "Подготовительные работы", "total_cost": 675000},
                    {"code": "ГЭСН 02", "name": "Земляные работы", "total_cost": 150000}
                ]
            },
            "roi": 18.5
        }
        
        saved_result = pm.save_project_result(project_id, "budget_calculation", tool_result)
        print(f"   ✅ Tool result saved with ID: {saved_result['id']}")
    except Exception as e:
        print(f"   ❌ Failed to save tool result: {e}")
        return False
    
    # 6. Retrieve saved results
    print("6. Retrieving saved results...")
    try:
        results = pm.get_project_results(project_id)
        print(f"   ✅ Results retrieved: {len(results)} results")
        for result in results:
            print(f"      - {result['type']} (created: {result['created_at']})")
    except Exception as e:
        print(f"   ❌ Failed to retrieve results: {e}")
        return False
    
    # 7. Verify project data was updated
    print("7. Verifying project data...")
    try:
        updated_project = pm.get_project(project_id)
        print(f"   ✅ Project updated:")
        print(f"      - Files count: {updated_project['files_count']}")
        print(f"      - ROI: {updated_project['roi']}%")
    except Exception as e:
        print(f"   ❌ Failed to verify project data: {e}")
        return False
    
    # Clean up
    print("8. Cleaning up...")
    try:
        # Delete project (which also deletes attached files)
        pm.delete_project(project_id)
        # Remove temp directory
        shutil.rmtree(temp_dir)
        print("   ✅ Cleanup completed")
    except Exception as e:
        print(f"   ⚠️  Cleanup warning: {e}")
    
    print("🎉 Full project-tool integration test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_full_project_tool_integration()
    sys.exit(0 if success else 1)