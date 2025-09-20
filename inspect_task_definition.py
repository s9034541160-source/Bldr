import os
import sys
import ast
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def inspect_task_definition():
    """Inspect the task definition in celery_norms.py"""
    print("🔍 Inspecting task definition...")
    print("=" * 50)
    
    try:
        # Read the celery_norms.py file
        task_file = os.path.join(os.path.dirname(__file__), 'core', 'celery_norms.py')
        with open(task_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content)
        
        # Find the task decorator
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if this function has a task decorator
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        # Check if it's a celery_app.task call
                        if isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr == 'task':
                                print(f"✅ Found task function: {node.name}")
                                
                                # Extract decorator arguments
                                for keyword in decorator.keywords:
                                    if keyword.arg == 'name':
                                        if isinstance(keyword.value, ast.Constant):
                                            task_name = keyword.value.value
                                            print(f"   Task name: {task_name}")
                                            return task_name
        
        print("❌ No task decorator found")
        return None
        
    except Exception as e:
        print(f"❌ Task inspection failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    task_name = inspect_task_definition()
    if task_name:
        print(f"\n🎉 Task '{task_name}' is properly defined!")
    else:
        print(f"\n❌ Task definition issue detected!")