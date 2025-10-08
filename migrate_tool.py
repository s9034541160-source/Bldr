#!/usr/bin/env python3
"""
Автоматизированный скрипт для миграции инструментов в новый формат.
"""

import os
import sys
from typing import Dict, List, Any
from pathlib import Path

def create_tool_template(tool_name: str, category: str, description: str = "") -> str:
    """Создать шаблон файла инструмента."""
    
    template = f'''# namespace:{category}
from typing import Any, Dict
import time
from core.tools.base_tool import ToolManifest, ToolInterface, ToolParam, ToolParamType

# Создаем Pydantic модели для универсального представления
coordinator_interface = ToolInterface(
    purpose="{description}",
    input_requirements={{
        # TODO: Добавить параметры инструмента
        "param1": ToolParam(
            name="param1",
            type=ToolParamType.STRING,
            required=True,
            description="Описание параметра"
        )
    }},
    execution_flow=[
        "1. Валидация входных параметров",
        "2. Выполнение основной логики",
        "3. Обработка результатов",
        "4. Возврат результата"
    ],
    output_format={{
        "structure": {{
            "status": "success/error",
            "data": "object - результат выполнения",
            "execution_time": "float in seconds"
        }},
        "result_fields": {{
            "result": "string - основной результат",
            "metadata": "object - дополнительные данные"
        }}
    }},
    usage_guidelines={{
        "for_coordinator": [
            "Используйте для {description.lower()}",
            "Передавайте корректные параметры",
            "Обрабатывайте результаты"
        ],
        "for_models": [
            "Инструмент возвращает структурированный результат",
            "Используйте metadata для дополнительной информации"
        ]
    }},
    integration_notes={{
        "dependencies": ["Core system"],
        "performance": "Средняя скорость выполнения: 1-3 секунды",
        "reliability": "Высокая",
        "scalability": "Поддерживает стандартные нагрузки"
    }}
)

manifest = ToolManifest(
    name="{tool_name}",
    version="1.0.0",
    title="🔧 {tool_name.replace('_', ' ').title()}",
    description="{description}",
    category="{category}",
    ui_placement="tools",
    enabled=True,
    system=False,
    entrypoint="tools.{category}.{tool_name}:execute",
    params=[
        ToolParam(
            name="param1",
            type=ToolParamType.STRING,
            required=True,
            description="Описание параметра",
            ui={{
                "placeholder": "Введите значение...",
                "maxLength": 500
            }}
        )
    ],
    outputs=["result", "metadata"],
    permissions=["filesystem:read", "network:out"],
    tags=["{category}", "enterprise"],
    result_display={{
        "type": "text",
        "title": "Результат выполнения",
        "description": "Результат работы инструмента"
    }},
    documentation={{
        "examples": [
            {{
                "title": "Пример использования",
                "param1": "значение",
                "description": "Описание примера"
            }}
        ],
        "tips": [
            "Будьте точны в параметрах",
            "Проверяйте результаты"
        ]
    }},
    coordinator_interface=coordinator_interface
)

def execute(**kwargs) -> Dict[str, Any]:
    """Execute {tool_name} with enterprise-level features."""
    start_time = time.time()
    
    try:
        # Validate and parse parameters
        param1 = kwargs.get('param1', '').strip()
        if not param1:
            return {{
                'status': 'error',
                'error': 'Параметр param1 не может быть пустым',
                'execution_time': time.time() - start_time
            }}
        
        # TODO: Implement tool logic here
        result = {{
            'result': f'Обработано: {{param1}}',
            'metadata': {{
                'processed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'input_length': len(param1)
            }}
        }}
        
        execution_time = time.time() - start_time
        
        return {{
            'status': 'success',
            'data': result,
            'execution_time': execution_time,
            'result_type': 'text',
            'result_title': f'🔧 Результат {tool_name}',
            'result_content': result['result'],
            'metadata': result['metadata']
        }}
        
    except Exception as e:
        return {{ 
            'status': 'error', 
            'error': str(e),
            'execution_time': time.time() - start_time
        }}
'''
    
    return template

def create_tool_file(tool_name: str, category: str, description: str = ""):
    """Создать файл инструмента."""
    
    # Создаем директорию если не существует
    category_dir = Path(f"tools/{category}")
    category_dir.mkdir(parents=True, exist_ok=True)
    
    # Создаем файл
    file_path = category_dir / f"{tool_name}.py"
    
    if file_path.exists():
        print(f"⚠️ Файл {file_path} уже существует!")
        return False
    
    template = create_tool_template(tool_name, category, description)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"✅ Создан файл: {file_path}")
    return True

def main():
    """Основная функция."""
    print("🚀 АВТОМАТИЗИРОВАННАЯ МИГРАЦИЯ ИНСТРУМЕНТОВ")
    print("=" * 50)
    
    # Список инструментов для миграции
    tools_to_migrate = [
        {
            "name": "calculate_estimate",
            "category": "financial", 
            "description": "Расчет сметы строительного проекта по нормативам ГЭСН/ФЕР"
        },
        {
            "name": "create_gantt_chart",
            "category": "project_management",
            "description": "Создание диаграммы Ганта для планирования проекта"
        },
        {
            "name": "analyze_tender",
            "category": "analysis",
            "description": "Анализ тендерной документации и выявление рисков"
        },
        {
            "name": "generate_ppr",
            "category": "document_generation",
            "description": "Генерация проекта производства работ (ППР)"
        },
        {
            "name": "create_pie_chart",
            "category": "visual",
            "description": "Создание круговых диаграмм для визуализации данных"
        },
        {
            "name": "monte_carlo_sim",
            "category": "analysis",
            "description": "Монте-Карло симуляция для анализа рисков проекта"
        },
        {
            "name": "extract_text_from_pdf",
            "category": "document_processing",
            "description": "Извлечение текста из PDF документов"
        },
        {
            "name": "analyze_bentley_model",
            "category": "bim",
            "description": "Анализ 3D модели Bentley для выявления коллизий"
        }
    ]
    
    print(f"📋 Планируется миграция {len(tools_to_migrate)} инструментов:")
    for i, tool in enumerate(tools_to_migrate, 1):
        print(f"  {i}. {tool['name']} ({tool['category']})")
    
    print("\n🔧 Создание файлов инструментов...")
    
    created = 0
    for tool in tools_to_migrate:
        if create_tool_file(tool['name'], tool['category'], tool['description']):
            created += 1
    
    print(f"\n✅ Создано файлов: {created}/{len(tools_to_migrate)}")
    
    if created > 0:
        print("\n📝 Следующие шаги:")
        print("1. Отредактируйте созданные файлы - добавьте реальную логику")
        print("2. Заполните coordinator_interface подробно")
        print("3. Протестируйте через UI")
        print("4. Зарегистрируйте в tool_registry")
    
    return created > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
