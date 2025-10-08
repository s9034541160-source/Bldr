"""
Авто-тест настроек координатора/моделей. Позволяет выполнить несколько пресетов и сравнить ответы.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import os

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field

try:
    from CANONICAL_FUNCTIONS.verify_api_token import verify_api_token
except Exception:
    def verify_api_token():  # type: ignore
        return {"sub": "admin", "role": "admin", "skip_auth": True}

router = APIRouter(prefix="/api/settings/autotest", tags=["settings-autotest"], dependencies=[Depends(verify_api_token)])

# Runtime settings file
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SETTINGS_PATH = os.path.join(PROJECT_ROOT, 'settings.json')


def _load_settings() -> Dict[str, Any]:
    import json
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f) or {}
    except Exception:
        return {}
    return {}


def _save_settings(data: Dict[str, Any]) -> None:
    import json
    with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class VariantConfig(BaseModel):
    name: str = Field(..., description="Название варианта (V1/V2/V3)")
    coordinator: Optional[Dict[str, Any]] = None  # partial coordinator settings override
    models_overrides: Optional[Dict[str, Any]] = None  # role->patch

class AutoTestRequest(BaseModel):
    variants: List[VariantConfig]
    queries: Optional[List[str]] = None  # custom queries; if None, use defaults
    files: Optional[Dict[str, str]] = None  # { image?: path, audio?: path, document?: path }

class AutoTestResponse(BaseModel):
    status: str
    started_at: str
    finished_at: str
    total: int
    results: List[Dict[str, Any]]


def _default_queries() -> List[str]:
    return [
        "Найди по какому СП делать земляные работы и процитируй пункт",
        "Сделай короткий чек-лист технадзора по монолиту",
        "Сгенерируй служебную записку подрядчику по нарушению ограждений",
        "Построй краткий график работ устройства фундамента (3-5 этапов)",
        "Дай стоимость по ГЭСН 8-6-1.1 для объема 100 в Москве",
        "Что такое ППР и когда он обязателен?",
        "Кратко: требования по охране труда для работ на высоте"
    ]


def _apply_variant_overrides(variant: VariantConfig, original: Dict[str, Any]) -> Dict[str, Any]:
    # Build new settings dict applying overrides
    data = dict(original)
    if variant.coordinator:
        data['coordinator'] = {**(data.get('coordinator') or {}), **variant.coordinator}
    if variant.models_overrides:
        mo = dict(data.get('models_overrides') or {})
        for role, patch in (variant.models_overrides or {}).items():
            base = dict(mo.get(role) or {})
            base.update({k: v for k, v in (patch or {}).items() if v is not None})
            mo[role] = base
        data['models_overrides'] = mo
    return data


@router.post('/upload')
async def upload_autotest_file(file: UploadFile = File(...), kind: Optional[str] = Form(None)):
    try:
        import uuid, os
        base = os.path.join(PROJECT_ROOT, 'temp', 'autotest')
        os.makedirs(base, exist_ok=True)
        ext = ''
        try:
            name = file.filename or ''
            if '.' in name:
                ext = '.' + name.rsplit('.', 1)[-1]
        except Exception:
            pass
        path = os.path.join(base, f"{uuid.uuid4().hex}{ext}")
        content = await file.read()
        with open(path, 'wb') as f:
            f.write(content)
        return {"status": "success", "path": path, "name": file.filename, "size": len(content), "kind": kind}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/run', response_model=AutoTestResponse)
async def run_autotest(payload: AutoTestRequest):
    try:
        if not payload.variants or len(payload.variants) == 0:
            raise HTTPException(status_code=400, detail="Нужно передать хотя бы один вариант")
        started = datetime.now().isoformat()
        original = _load_settings()
        results: List[Dict[str, Any]] = []

        # Try to import coordinator
        from core.agents.coordinator_agent import CoordinatorAgent
        try:
            from core.unified_tools_system import UnifiedToolsSystem
        except Exception:
            UnifiedToolsSystem = None  # type: ignore

        queries = payload.queries or _default_queries()
        file_map = payload.files or {}

        for variant in payload.variants[:3]:
            # Apply overrides to settings.json
            try:
                new_settings = _apply_variant_overrides(variant, original)
                _save_settings(new_settings)
            except Exception:
                pass

            # Create fresh agent per variant (to pick up settings via request_context)
            agent = CoordinatorAgent()
            # Attach tools if available
            try:
                if UnifiedToolsSystem:
                    tools = UnifiedToolsSystem()
                    agent.set_tools_system(tools)
            except Exception:
                pass

            v_res: List[Dict[str, Any]] = []
            # Text queries
            for q in queries:
                try:
                    # Inject settings into request_context
                    agent.request_context = {
                        "channel": "autotest",
                        "attachments": [],
                        "settings": {"coordinator": (new_settings.get('coordinator') if 'new_settings' in locals() else (original.get('coordinator') or {}))}
                    }
                    ans = agent.process_request(q)
                except Exception as e:
                    ans = f"Ошибка: {e}"
                v_res.append({"type": "text", "query": q, "answer": ans})

            # Image test
            if file_map.get('image'):
                try:
                    agent.request_context = {
                        "channel": "autotest",
                        "attachments": [{"type": "image", "path": file_map.get('image'), "name": os.path.basename(file_map.get('image') or '')}],
                        "settings": {"coordinator": (new_settings.get('coordinator') if 'new_settings' in locals() else (original.get('coordinator') or {}))}
                    }
                    q = "Проанализируй изображение: найди объекты и дай краткие рекомендации"
                    ans = agent.process_request(q)
                    v_res.append({"type": "image", "query": q, "file": file_map.get('image'), "answer": ans})
                except Exception as e:
                    v_res.append({"type": "image", "query": "error", "file": file_map.get('image'), "answer": f"Ошибка: {e}"})

            # Audio test
            if file_map.get('audio'):
                try:
                    agent.request_context = {
                        "channel": "autotest",
                        "attachments": [{"type": "audio", "path": file_map.get('audio'), "name": os.path.basename(file_map.get('audio') or '')}],
                        "settings": {"coordinator": (new_settings.get('coordinator') if 'new_settings' in locals() else (original.get('coordinator') or {}))}
                    }
                    q = "Транскрибируй голосовое сообщение и дай краткий ответ"
                    ans = agent.process_request(q)
                    v_res.append({"type": "audio", "query": q, "file": file_map.get('audio'), "answer": ans})
                except Exception as e:
                    v_res.append({"type": "audio", "query": "error", "file": file_map.get('audio'), "answer": f"Ошибка: {e}"})

            # Document test
            if file_map.get('document'):
                try:
                    agent.request_context = {
                        "channel": "autotest",
                        "attachments": [{"type": "document", "path": file_map.get('document'), "name": os.path.basename(file_map.get('document') or '')}],
                        "settings": {"coordinator": (new_settings.get('coordinator') if 'new_settings' in locals() else (original.get('coordinator') or {}))}
                    }
                    q = "Кратко извлеки важные пункты из документа"
                    ans = agent.process_request(q)
                    v_res.append({"type": "document", "query": q, "file": file_map.get('document'), "answer": ans})
                except Exception as e:
                    v_res.append({"type": "document", "query": "error", "file": file_map.get('document'), "answer": f"Ошибка: {e}"})

            results.append({
                "variant": variant.name,
                "coordinator": (new_settings.get('coordinator') if 'new_settings' in locals() else (original.get('coordinator') or {})),
                "total": len(v_res),
                "items": v_res
            })

        # Restore original settings
        try:
            _save_settings(original)
        except Exception:
            pass

        finished = datetime.now().isoformat()
        return AutoTestResponse(status="success", started_at=started, finished_at=finished, total=len(results), results=results)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
