"""
ProcessFactory - генератор кода для бизнес-процессов
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ProcessFactory:
    """Фабрика для генерации кода бизнес-процессов"""
    
    def __init__(self, base_path: str = "backend/modules"):
        """
        Args:
            base_path: Базовый путь для модулей процессов
        """
        self.base_path = Path(base_path)
        self.templates_path = Path("backend/core/process_factory/templates")
    
    def create_process(
        self,
        process_id: str,
        process_name: str,
        description: str,
        process_type: str = "standard",
        inputs: Optional[List[Dict[str, str]]] = None,
        outputs: Optional[List[Dict[str, str]]] = None,
        steps: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Создание нового бизнес-процесса
        
        Args:
            process_id: ID процесса (например, F1.01)
            process_name: Название процесса
            description: Описание процесса
            process_type: Тип процесса (standard, document, calculation, approval, integration)
            inputs: Список входных данных
            outputs: Список выходных данных
            steps: Список шагов процесса
            
        Returns:
            Информация о созданных файлах
        """
        process_dir = self.base_path / process_id.lower().replace(".", "_")
        process_dir.mkdir(parents=True, exist_ok=True)
        
        created_files = []
        
        # Генерация структуры модуля
        files_to_create = [
            ("__init__.py", self._generate_init(process_id, process_name)),
            ("agent.py", self._generate_agent(process_id, process_name, description, steps)),
            ("schemas.py", self._generate_schemas(process_id, inputs, outputs)),
            ("service.py", self._generate_service(process_id, process_name, steps)),
            ("api.py", self._generate_api(process_id, process_name)),
            ("README.md", self._generate_readme(process_id, process_name, description, inputs, outputs, steps)),
        ]
        
        for filename, content in files_to_create:
            file_path = process_dir / filename
            file_path.write_text(content, encoding="utf-8")
            created_files.append(str(file_path))
            logger.info(f"Created {file_path}")
        
        return {
            "process_id": process_id,
            "process_name": process_name,
            "directory": str(process_dir),
            "files": created_files
        }
    
    def _generate_init(self, process_id: str, process_name: str) -> str:
        """Генерация __init__.py"""
        return f'''"""
{process_name} - {process_id}
"""

from .agent import {self._to_class_name(process_id)}Agent
from .service import {self._to_class_name(process_id)}Service
from .schemas import *

__all__ = ["{self._to_class_name(process_id)}Agent", "{self._to_class_name(process_id)}Service"]
'''
    
    def _generate_agent(
        self,
        process_id: str,
        process_name: str,
        description: str,
        steps: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Генерация агента процесса"""
        class_name = self._to_class_name(process_id)
        
        steps_code = ""
        if steps:
            for i, step in enumerate(steps, 1):
                step_name = step.get("name", f"Step {i}")
                steps_code += f'        # {step_name}\n'
        
        return f'''"""
Агент для процесса {process_id}: {process_name}
"""

from backend.core.agent import Agent
from typing import Dict, Any
from .service import {class_name}Service


class {class_name}Agent(Agent):
    """Агент для выполнения процесса {process_id}"""
    
    def __init__(self):
        super().__init__(
            agent_id="{process_id.lower()}",
            name="{process_name}",
            description="{description}"
        )
        self.service = {class_name}Service()
    
    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение процесса {process_id}"""
        # Парсинг входных данных из контекста
        inputs = context.get("inputs", {{}})
        
        # Выполнение шагов процесса
{steps_code}
        # Вызов сервиса для выполнения бизнес-логики
        result = self.service.execute(inputs)
        
        return {{
            "process_id": "{process_id}",
            "task": task,
            "result": result,
            "context": context
        }}
'''
    
    def _generate_schemas(
        self,
        process_id: str,
        inputs: Optional[List[Dict[str, str]]],
        outputs: Optional[List[Dict[str, str]]]
    ) -> str:
        """Генерация Pydantic схем"""
        class_name = self._to_class_name(process_id)
        
        input_fields = ""
        if inputs:
            for inp in inputs:
                field_name = inp.get("name", "field")
                field_type = inp.get("type", "str")
                input_fields += f'    {field_name}: {field_type}\n'
        else:
            input_fields = "    # Добавьте поля входных данных\n"
        
        output_fields = ""
        if outputs:
            for out in outputs:
                field_name = out.get("name", "field")
                field_type = out.get("type", "str")
                output_fields += f'    {field_name}: {field_type}\n'
        else:
            output_fields = "    # Добавьте поля выходных данных\n"
        
        return f'''"""
Pydantic схемы для процесса {process_id}
"""

from pydantic import BaseModel
from typing import Optional


class {class_name}Input(BaseModel):
    """Входные данные для процесса {process_id}"""
{input_fields}


class {class_name}Output(BaseModel):
    """Выходные данные процесса {process_id}"""
{output_fields}
'''
    
    def _generate_service(
        self,
        process_id: str,
        process_name: str,
        steps: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Генерация сервиса процесса"""
        class_name = self._to_class_name(process_id)
        
        steps_code = ""
        if steps:
            for i, step in enumerate(steps, 1):
                step_name = step.get("name", f"Step {i}")
                steps_code += f'        # Шаг {i}: {step_name}\n'
                steps_code += f'        # TODO: Реализовать логику шага\n\n'
        
        return f'''"""
Сервис для процесса {process_id}: {process_name}
"""

from typing import Dict, Any
from .schemas import {class_name}Input, {class_name}Output
import logging

logger = logging.getLogger(__name__)


class {class_name}Service:
    """Сервис для выполнения бизнес-логики процесса {process_id}"""
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнение процесса {process_id}
        
        Args:
            inputs: Входные данные процесса
            
        Returns:
            Результат выполнения процесса
        """
        logger.info(f"Executing process {process_id}")
        
{steps_code}
        # TODO: Реализовать бизнес-логику процесса
        
        return {{
            "status": "completed",
            "process_id": "{process_id}",
            "result": {{}}
        }}
'''
    
    def _generate_api(self, process_id: str, process_name: str) -> str:
        """Генерация API эндпоинтов"""
        class_name = self._to_class_name(process_id)
        route_name = process_id.lower().replace(".", "_")
        
        return f'''"""
API эндпоинты для процесса {process_id}: {process_name}
"""

from fastapi import APIRouter, Depends, HTTPException
from backend.middleware.rbac import get_current_user, require_permission
from backend.models.auth import User
from .schemas import {class_name}Input, {class_name}Output
from .service import {class_name}Service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/{route_name}", tags=["{process_id}"])

service = {class_name}Service()


@router.post("/execute", response_model={class_name}Output)
@require_permission("process", "execute")
async def execute_process(
    inputs: {class_name}Input,
    current_user: User = Depends(get_current_user)
):
    """Выполнение процесса {process_id}"""
    try:
        result = service.execute(inputs.dict())
        return {class_name}Output(**result)
    except Exception as e:
        logger.error(f"Process execution error: {{e}}")
        raise HTTPException(status_code=500, detail=str(e))
'''
    
    def _generate_readme(
        self,
        process_id: str,
        process_name: str,
        description: str,
        inputs: Optional[List[Dict[str, str]]],
        outputs: Optional[List[Dict[str, str]]],
        steps: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Генерация README для процесса"""
        readme = f'''# {process_id}: {process_name}

{description}

## Входные данные

'''
        if inputs:
            for inp in inputs:
                readme += f'- **{inp.get("name")}** ({inp.get("type", "str")}): {inp.get("description", "")}\n'
        else:
            readme += "- Нет входных данных\n"
        
        readme += "\n## Выходные данные\n\n"
        if outputs:
            for out in outputs:
                readme += f'- **{out.get("name")}** ({out.get("type", "str")}): {out.get("description", "")}\n'
        else:
            readme += "- Нет выходных данных\n"
        
        readme += "\n## Шаги процесса\n\n"
        if steps:
            for i, step in enumerate(steps, 1):
                readme += f'{i}. {step.get("name", f"Step {i}")}\n'
        else:
            readme += "1. TODO: Определить шаги процесса\n"
        
        readme += f'''
## API

- `POST /api/{process_id.lower().replace(".", "_")}/execute` - Выполнение процесса

## Использование

```python
from backend.modules.{process_id.lower().replace(".", "_")} import {self._to_class_name(process_id)}Agent

agent = {self._to_class_name(process_id)}Agent()
result = agent.execute("task", {{"inputs": {{}}}})
```
'''
        return readme
    
    def _to_class_name(self, process_id: str) -> str:
        """Преобразование ID процесса в имя класса"""
        # F1.01 -> F1_01 -> F101
        return process_id.replace(".", "_").replace("-", "_").title().replace("_", "")


# Глобальный экземпляр фабрики
process_factory = ProcessFactory()

