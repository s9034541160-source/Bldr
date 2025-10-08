#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
БЫСТРАЯ ДИАГНОСТИКА СОСТОЯНИЯ СИСТЕМЫ
=====================================

Проверяет ключевые компоненты исправленной архитектуры:
- Сервер и API endpoints
- Master Tools System адаптер
- Coordinator agent
- Specialist agents интеграция
- Role agents интеграция
"""

import os
import sys
import importlib.util
import requests
import json
from datetime import datetime

def check_server_api():
    """Проверка API сервера"""
    print("🖥️ Checking server and API...")
    
    results = {
        'server_running': False,
        'health_endpoint': False,
        'ai_chat_endpoint': False
    }
    
    try:
        # Проверяем health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        results['health_endpoint'] = response.status_code == 200
        
        if results['health_endpoint']:
            results['server_running'] = True
            print("✅ Server is running")
            print("✅ Health endpoint OK")
        
        # Проверяем AI chat endpoint
        test_payload = {
            "message": "test",
            "context_search": False,
            "max_context": 1
        }
        response = requests.post(
            "http://localhost:8000/api/ai/chat",
            json=test_payload,
            timeout=10
        )
        results['ai_chat_endpoint'] = response.status_code == 200
        
        if results['ai_chat_endpoint']:
            print("✅ AI chat endpoint responding")
        else:
            print(f"❌ AI chat endpoint error: {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Server not running on localhost:8000")
    except Exception as e:
        print(f"❌ Server check error: {e}")
    
    return results

def check_tools_adapter():
    """Проверка Master Tools System адаптера"""
    print("\n🔧 Checking Master Tools System adapter...")
    
    try:
        # Добавляем путь
        sys.path.append('C:/Bldr/core')
        
        # Проверяем импорт адаптера
        from tools_adapter import get_tools_adapter
        
        # Создаем адаптер
        tools_adapter = get_tools_adapter()
        
        if tools_adapter:
            print("✅ Tools adapter created successfully")
            
            # Проверяем список инструментов
            if hasattr(tools_adapter, 'get_available_tools'):
                tools = tools_adapter.get_available_tools()
                print(f"✅ Available tools: {len(tools)} tools")
                
                # Показываем несколько инструментов
                tool_names = list(tools.keys())[:5] if isinstance(tools, dict) else []
                if tool_names:
                    print(f"📋 Sample tools: {', '.join(tool_names)}")
                
                return True
            else:
                print("⚠️ Tools adapter missing get_available_tools method")
                return False
        else:
            print("❌ Failed to create tools adapter")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Tools adapter error: {e}")
        return False

def check_coordinator_agent():
    """Проверка coordinator agent"""
    print("\n🧠 Checking coordinator agent...")
    
    try:
        # Проверяем импорт
        from agents.coordinator_agent import CoordinatorAgent
        from tools_adapter import get_tools_adapter
        
        # Создаем адаптер и координатор
        tools_adapter = get_tools_adapter()
        coordinator = CoordinatorAgent(tools_system=tools_adapter)
        
        if coordinator:
            print("✅ Coordinator agent created")
            
            # Проверяем метод получения инструментов
            if hasattr(coordinator, 'get_available_tools'):
                try:
                    tools = coordinator.get_available_tools()
                    print(f"✅ Coordinator can access {len(tools)} tools")
                    return True
                except Exception as e:
                    print(f"❌ Coordinator tools access error: {e}")
                    return False
            else:
                print("⚠️ Coordinator missing get_available_tools method")
                return False
        else:
            print("❌ Failed to create coordinator")
            return False
            
    except ImportError as e:
        print(f"❌ Coordinator import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Coordinator error: {e}")
        return False

def check_specialist_agents():
    """Проверка specialist agents"""
    print("\n🤖 Checking specialist agents...")
    
    try:
        from agents.specialist_agents import SpecialistAgentsManager
        from tools_adapter import get_tools_adapter
        
        # Создаем адаптер и менеджер
        tools_adapter = get_tools_adapter()
        specialist_manager = SpecialistAgentsManager(tools_system=tools_adapter)
        
        if specialist_manager:
            print("✅ Specialist agents manager created")
            
            # Проверяем доступ к tools_system
            if hasattr(specialist_manager, 'tools_system') and specialist_manager.tools_system:
                print("✅ Specialist manager has tools_system access")
                return True
            else:
                print("❌ Specialist manager missing tools_system")
                return False
        else:
            print("❌ Failed to create specialist manager")
            return False
            
    except ImportError as e:
        print(f"❌ Specialist agents import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Specialist agents error: {e}")
        return False

def check_role_agents():
    """Проверка role agents"""
    print("\n🎭 Checking role agents...")
    
    try:
        from agents.roles_agents import RoleAgent
        from tools_adapter import get_tools_adapter
        
        # Создаем адаптер и role agent
        tools_adapter = get_tools_adapter()
        role_agent = RoleAgent("analyst", tools_system=tools_adapter)
        
        if role_agent:
            print("✅ Role agent created")
            
            # Проверяем метод _execute_master_tool
            if hasattr(role_agent, '_execute_master_tool'):
                print("✅ Role agent has _execute_master_tool method")
                return True
            else:
                print("❌ Role agent missing _execute_master_tool method")
                return False
        else:
            print("❌ Failed to create role agent")
            return False
            
    except ImportError as e:
        print(f"❌ Role agents import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Role agents error: {e}")
        return False

def check_file_exists(filepath, description):
    """Проверка существования файла"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ {description}: {filepath} ({size} bytes)")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def system_health_check():
    """Полная проверка здоровья системы"""
    print("🏥 SYSTEM HEALTH CHECK")
    print("="*50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Проверяем ключевые файлы
    print(f"\n📁 Checking key files...")
    files_check = [
        ("C:/Bldr/core/bldr_api.py", "Main API file"),
        ("C:/Bldr/core/tools_adapter.py", "Tools adapter"),
        ("C:/Bldr/agents/coordinator_agent.py", "Coordinator agent"),
        ("C:/Bldr/agents/specialist_agents.py", "Specialist agents"),
        ("C:/Bldr/agents/roles_agents.py", "Role agents"),
        ("C:/Bldr/test_fixed_architecture.py", "Architecture test"),
        ("C:/Bldr/run_final_test.py", "Final test runner")
    ]
    
    files_passed = 0
    for filepath, description in files_check:
        if check_file_exists(filepath, description):
            files_passed += 1
    
    # Проверяем компоненты
    print(f"\n🔍 Checking system components...")
    
    components = [
        ("Server & API", check_server_api),
        ("Tools Adapter", check_tools_adapter), 
        ("Coordinator Agent", check_coordinator_agent),
        ("Specialist Agents", check_specialist_agents),
        ("Role Agents", check_role_agents)
    ]
    
    components_passed = 0
    component_results = {}
    
    for name, check_func in components:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            result = check_func()
            component_results[name] = result
            if result:
                components_passed += 1
        except Exception as e:
            print(f"❌ {name} check failed: {e}")
            component_results[name] = False
    
    # Итоговый отчет
    print(f"\n{'='*50}")
    print("📊 HEALTH CHECK SUMMARY")
    print("="*50)
    
    print(f"📁 Files: {files_passed}/{len(files_check)} present")
    print(f"🔧 Components: {components_passed}/{len(components)} working")
    
    total_score = (files_passed + components_passed) / (len(files_check) + len(components)) * 100
    print(f"📈 Overall Health: {total_score:.1f}%")
    
    if total_score >= 90:
        print("🎉 EXCELLENT! System is healthy and ready")
    elif total_score >= 70:
        print("✅ GOOD! System mostly working, minor issues possible")
    elif total_score >= 50:
        print("⚠️ FAIR! Some components need attention")
    else:
        print("❌ POOR! Major issues need to be resolved")
    
    # Рекомендации
    print(f"\n📋 RECOMMENDATIONS:")
    
    if not component_results.get("Server & API", False):
        print("   🔌 Start the server: python app.py")
    
    if not component_results.get("Tools Adapter", False):
        print("   🔧 Check tools_adapter.py import and initialization")
        
    if not component_results.get("Coordinator Agent", False):
        print("   🧠 Check coordinator_agent.py integration with Master Tools System")
        
    if not component_results.get("Specialist Agents", False):
        print("   🤖 Check specialist_agents.py tools_system parameter")
        
    if not component_results.get("Role Agents", False):
        print("   🎭 Check roles_agents.py _execute_master_tool method")
    
    if total_score >= 90:
        print("   ✅ Ready for final testing: python run_final_test.py")
    
    return total_score >= 70

if __name__ == "__main__":
    print("🏥 Starting System Health Check...")
    healthy = system_health_check()
    exit(0 if healthy else 1)