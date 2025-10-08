"""
API для назначения моделей на роли (role → model) с быстрым переключением через UI.
Данные хранятся в settings.json (ключ 'models_overrides'), совместно с координаторскими настройками.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, RootModel

try:
    from CANONICAL_FUNCTIONS.verify_api_token import verify_api_token
except Exception:
    def verify_api_token():  # type: ignore
        return {"sub": "admin", "role": "admin", "skip_auth": True}

try:
    from core.config import MODELS_CONFIG
except Exception:
    MODELS_CONFIG = {}

router = APIRouter(prefix="/api/settings", tags=["settings-models"], dependencies=[Depends(verify_api_token)])

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SETTINGS_PATH = os.path.join(PROJECT_ROOT, 'settings.json')

# ====== UTILS ======

def _load_settings() -> Dict[str, Any]:
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f) or {}
    except Exception:
        return {}
    return {}


def _save_settings(data: Dict[str, Any]) -> None:
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save settings.json: {e}")


def _get_overrides() -> Dict[str, Any]:
    data = _load_settings()
    return data.get('models_overrides') or {}


def _set_overrides(overrides: Dict[str, Any]) -> None:
    data = _load_settings()
    data['models_overrides'] = overrides or {}
    _save_settings(data)


# ====== MODELS LIST ======
DEFAULT_BASE_URL = os.getenv('LM_STUDIO_BASE_URL', 'http://127.0.0.1:1234/v1')

# Библиотека популярных моделей (быстрый выбор)
CURATED_MODELS = [
    {"id": "deepseek/deepseek-r1-0528-qwen3-8b", "label": "DeepSeek-R1-0528-Qwen3-8B", "base_url": DEFAULT_BASE_URL, "temperature": 0.3, "max_tokens": 4096},
    {"id": "qwen/qwen3-coder-30b", "label": "Qwen3-Coder-30B", "base_url": DEFAULT_BASE_URL, "temperature": 0.2, "max_tokens": 8192},
    {"id": "qwen/qwen2.5-vl-7b", "label": "Qwen2.5-VL-7B (Vision)", "base_url": DEFAULT_BASE_URL, "temperature": 0.3, "max_tokens": 4096},
    {"id": "mistralai/mistral-nemo-instruct-2407", "label": "Mistral-Nemo-Instruct-2407", "base_url": DEFAULT_BASE_URL, "temperature": 0.2, "max_tokens": 4096},
    {"id": "anthropic/claude-3.5-sonnet", "label": "Claude 3.5 Sonnet (OpenAI-compatible gateway)", "base_url": DEFAULT_BASE_URL, "temperature": 0.2, "max_tokens": 8192},
]


def _unique_models_from_config() -> List[Dict[str, Any]]:
    uniq: Dict[str, Dict[str, Any]] = {}
    try:
        for role, cfg in (MODELS_CONFIG or {}).items():
            mid = str(cfg.get('model') or '')
            if not mid:
                continue
            base_url = cfg.get('base_url') or DEFAULT_BASE_URL
            key = f"{mid}@{base_url}"
            if key not in uniq:
                uniq[key] = {
                    "id": mid,
                    "label": cfg.get('name') or mid,
                    "base_url": base_url,
                    "temperature": cfg.get('temperature', 0.3),
                    "max_tokens": cfg.get('max_tokens', 4096)
                }
    except Exception:
        pass
    return list(uniq.values())


@router.get('/roles')
async def list_roles():
    try:
        roles = []
        for k, v in (MODELS_CONFIG or {}).items():
            roles.append({"role": k, "title": v.get('name') or k})
        return {"roles": roles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/models/available')
async def list_available_models():
    try:
        models = _unique_models_from_config()
        # Merge curated (avoid duplicates by id@base)
        seen = {f"{m['id']}@{m.get('base_url')}" for m in models}
        for cm in CURATED_MODELS:
            key = f"{cm['id']}@{cm.get('base_url')}"
            if key not in seen:
                models.append(cm)
                seen.add(key)
        return {"models": models, "default_base_url": DEFAULT_BASE_URL}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/role-models')
async def get_role_models():
    try:
        overrides = _get_overrides()
        data = {}
        for role, cfg in (MODELS_CONFIG or {}).items():
            ov = overrides.get(role) or {}
            eff = dict(cfg)
            eff.update({k: v for k, v in ov.items() if v not in (None, '')})
            data[role] = {
                "effective": {
                    "model": eff.get('model'),
                    "base_url": eff.get('base_url'),
                    "temperature": eff.get('temperature'),
                    "max_tokens": eff.get('max_tokens'),
                    "timeout": eff.get('timeout')
                },
                "override": ov,
                "default": {
                    "model": cfg.get('model'),
                    "base_url": cfg.get('base_url'),
                    "temperature": cfg.get('temperature'),
                    "max_tokens": cfg.get('max_tokens'),
                    "timeout": cfg.get('timeout')
                }
            }
        return {"roles": data, "updated_at": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/json')
async def get_full_settings_json():
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f) or {}
        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/json/download')
async def download_full_settings_json():
    try:
        if not os.path.exists(SETTINGS_PATH):
            raise HTTPException(status_code=404, detail='settings.json not found')
        return FileResponse(SETTINGS_PATH, media_type='application/json', filename='settings.json')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/json/open')
async def open_settings_in_editor():
    """Open settings.json with the OS default associated editor (Notepad on Windows)."""
    try:
        if not os.path.exists(SETTINGS_PATH):
            # Create empty file to allow editing
            with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
                f.write('{}')
        # Windows-specific: os.startfile
        try:
            os.startfile(SETTINGS_PATH)  # type: ignore[attr-defined]
            return {"status": "ok", "message": "Открыто в системном редакторе"}
        except AttributeError:
            # Non-Windows: try xdg-open / open
            import subprocess, sys
            cmd = ['xdg-open', SETTINGS_PATH] if sys.platform.startswith('linux') else ['open', SETTINGS_PATH]
            subprocess.Popen(cmd)
            return {"status": "ok", "message": "Открыто в системном редакторе"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RoleModelsUpdate(RootModel[Dict[str, Dict[str, Any]]]):
    # mapping role-> partial override { model, base_url?, temperature?, max_tokens?, timeout? }
    pass


@router.put('/role-models')
async def update_role_models(payload: RoleModelsUpdate):
    try:
        updates = payload.root if isinstance(payload.root, dict) else {}
        overrides = _get_overrides()
        for role, patch in updates.items():
            if role not in MODELS_CONFIG:
                continue
            cur = overrides.get(role) or {}
            for k in ('model', 'base_url', 'temperature', 'max_tokens', 'timeout'):
                if k in patch:
                    val = patch.get(k)
                    if val in (None, ''):
                        if k in cur:
                            del cur[k]
                    else:
                        cur[k] = val
            if cur:
                overrides[role] = cur
            elif role in overrides:
                del overrides[role]
        _set_overrides(overrides)
        return {"status": "ok", "overrides": overrides, "updated_at": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/models/reload-coordinator')
async def reload_coordinator_model():
    try:
        from core.model_manager import model_manager
        # Unload all coordinator entries
        keys = [k for k in list(model_manager.model_cache.keys()) if k.startswith('coordinator_')]
        for key in keys:
            try:
                model_manager._unload_model(key)  # type: ignore
            except Exception:
                pass
        # Force recreate
        client = model_manager.get_model_client('coordinator')
        ok = client is not None
        return {"status": "ok" if ok else "error", "reloaded": ok, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/models/clear-cache')
async def clear_models_cache(keep_coordinator: bool = Query(True, description="Сохранить координатора в кеше")):
    try:
        from core.model_manager import model_manager
        if keep_coordinator:
            model_manager.force_cleanup()
        else:
            model_manager.clear_all_models()
        return {"status": "ok", "kept_coordinator": keep_coordinator, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/role-models/reset')
async def reset_role_models(role: Optional[str] = Query(None, description="Если указана роль — сбросить только её")):
    try:
        overrides = _get_overrides()
        if role:
            overrides.pop(role, None)
        else:
            overrides = {}
        _set_overrides(overrides)
        return {"status": "ok", "overrides": overrides, "updated_at": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]