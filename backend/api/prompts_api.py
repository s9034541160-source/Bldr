"""
API для управления внешними промптами ролей и правилами фактической точности (Markdown).
Поддерживает загрузку текущего текста, обновление (сохранение в core/prompts/active) и сброс к дефолту
(чтение из config.MODELS_CONFIG/FACTUAL_ACCURACY_RULES без необходимости отдельных default-файлов).
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

try:
    # Авторизация как в остальных защищенных эндпоинтах
    from CANONICAL_FUNCTIONS.verify_api_token import verify_api_token
except Exception:
    def verify_api_token():  # type: ignore
        return {"sub": "admin", "role": "admin", "skip_auth": True}

try:
    # Источники дефолтного содержания
    from core.config import MODELS_CONFIG, FACTUAL_ACCURACY_RULES
except Exception as e:
    MODELS_CONFIG = {}
    FACTUAL_ACCURACY_RULES = ""

router = APIRouter(prefix="/api/settings", tags=["settings"], dependencies=[Depends(verify_api_token)])

# Директории хранения активных (переопределённых) markdown-файлов
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PROMPTS_DIR = os.path.join(PROJECT_ROOT, 'core', 'prompts')
ACTIVE_DIR = os.path.join(PROMPTS_DIR, 'active')

os.makedirs(ACTIVE_DIR, exist_ok=True)

# ----- Модели -----
class PromptUpdateRequest(BaseModel):
    content: str = Field(..., description="Markdown содержания промпта роли")

class PromptInfo(BaseModel):
    role: str
    title: str
    source: str  # active | default
    updated_at: Optional[str] = None

class PromptResponse(BaseModel):
    role: str
    title: str
    content: str
    source: str  # active | default
    updated_at: Optional[str] = None

class RulesUpdateRequest(BaseModel):
    content: str

class RulesResponse(BaseModel):
    content: str
    source: str
    updated_at: Optional[str] = None

# ----- Утилиты -----

def _active_prompt_path(role_key: str) -> str:
    # Приведём ключ к безопасному имени файла
    safe = ''.join(c for c in role_key if c.isalnum() or c in ('_', '-', '.'))
    return os.path.join(ACTIVE_DIR, f"{safe}.md")


def _active_rules_path() -> str:
    return os.path.join(ACTIVE_DIR, 'factual_rules.md')


def _read_text(path: str) -> Optional[str]:
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception:
        return None
    return None


def _write_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def _get_role_title(role_key: str) -> str:
    try:
        name = MODELS_CONFIG.get(role_key, {}).get('name')
        return name or role_key
    except Exception:
        return role_key


def _build_default_prompt_md(role_key: str) -> str:
    """Собрать дефолтный markdown промпт из config.MODELS_CONFIG."""
    cfg = MODELS_CONFIG.get(role_key) or {}
    title = cfg.get('name', role_key)
    desc = cfg.get('description', '').strip()
    tools = cfg.get('tool_instructions', '').strip()
    responsibilities = cfg.get('responsibilities', [])
    exclusions = cfg.get('exclusions', [])
    interaction_rules = cfg.get('interaction_rules', [])

    lines: List[str] = []
    lines.append(f"# {title}")
    if desc:
        lines.append("\n## Описание")
        lines.append(desc)
    if tools:
        lines.append("\n## Инструкции по инструментам")
        lines.append("````markdown\n" + tools + "\n````")
    if responsibilities:
        lines.append("\n## Ответственности")
        for item in responsibilities:
            lines.append(f"- {item}")
    if exclusions:
        lines.append("\n## Исключения")
        for item in exclusions:
            lines.append(f"- {item}")
    if interaction_rules:
        lines.append("\n## Правила взаимодействия")
        for item in interaction_rules:
            lines.append(f"- {item}")
    # Отдельно правила фактической точности мы не встраиваем — они редактируются отдельно
    return "\n".join(lines).strip() or f"# {role_key}\n(пусто)"


def _get_prompt(role_key: str) -> PromptResponse:
    path = _active_prompt_path(role_key)
    active = _read_text(path)
    title = _get_role_title(role_key)
    if active is not None:
        updated = datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
        return PromptResponse(role=role_key, title=title, content=active, source='active', updated_at=updated)
    # default (конструируем из config.py)
    default_md = _build_default_prompt_md(role_key)
    return PromptResponse(role=role_key, title=title, content=default_md, source='default', updated_at=None)


def _list_prompts() -> List[PromptInfo]:
    roles = list(MODELS_CONFIG.keys()) if isinstance(MODELS_CONFIG, dict) else []
    infos: List[PromptInfo] = []
    for rk in roles:
        path = _active_prompt_path(rk)
        source = 'active' if os.path.exists(path) else 'default'
        updated = datetime.fromtimestamp(os.path.getmtime(path)).isoformat() if os.path.exists(path) else None
        infos.append(PromptInfo(role=rk, title=_get_role_title(rk), source=source, updated_at=updated))
    return infos


def _get_rules() -> RulesResponse:
    path = _active_rules_path()
    active = _read_text(path)
    if active is not None:
        return RulesResponse(content=active, source='active', updated_at=datetime.fromtimestamp(os.path.getmtime(path)).isoformat())
    # default из config
    return RulesResponse(content=str(FACTUAL_ACCURACY_RULES or '').strip(), source='default', updated_at=None)

# ----- Эндпоинты -----

@router.get('/prompts/list', response_model=List[PromptInfo])
async def list_prompts():
    try:
        return _list_prompts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/prompts/{role_key}', response_model=PromptResponse)
async def get_prompt(role_key: str):
    try:
        if role_key not in (MODELS_CONFIG.keys() if isinstance(MODELS_CONFIG, dict) else []):
            raise HTTPException(status_code=404, detail=f"Неизвестная роль: {role_key}")
        return _get_prompt(role_key)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/prompts/{role_key}', response_model=PromptResponse)
async def update_prompt(role_key: str, payload: PromptUpdateRequest):
    try:
        if role_key not in (MODELS_CONFIG.keys() if isinstance(MODELS_CONFIG, dict) else []):
            raise HTTPException(status_code=404, detail=f"Неизвестная роль: {role_key}")
        path = _active_prompt_path(role_key)
        _write_text(path, payload.content or '')
        return _get_prompt(role_key)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/prompts/{role_key}/reset', response_model=PromptResponse)
async def reset_prompt(role_key: str):
    try:
        if role_key not in (MODELS_CONFIG.keys() if isinstance(MODELS_CONFIG, dict) else []):
            raise HTTPException(status_code=404, detail=f"Неизвестная роль: {role_key}")
        path = _active_prompt_path(role_key)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
        return _get_prompt(role_key)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/factual-rules', response_model=RulesResponse)
async def get_rules():
    try:
        return _get_rules()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/factual-rules', response_model=RulesResponse)
async def update_rules(payload: RulesUpdateRequest):
    try:
        path = _active_rules_path()
        _write_text(path, payload.content or '')
        return _get_rules()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/factual-rules/reset', response_model=RulesResponse)
async def reset_rules():
    try:
        path = _active_rules_path()
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
        return _get_rules()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from core.config import get_capabilities_prompt

# Preview endpoint: effective prompt + effective model info
@router.get('/prompts/preview')
async def preview_prompt(role: str):
    try:
        # Load effective model info from settings.json overrides
        import json as _json, os as _os
        settings_path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), 'settings.json')
        models_overrides = {}
        try:
            if _os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    data = _json.load(f) or {}
                    models_overrides = data.get('models_overrides') or {}
        except Exception:
            models_overrides = {}
        base_cfg = MODELS_CONFIG.get(role, {})
        ov = models_overrides.get(role, {}) if isinstance(models_overrides, dict) else {}
        eff = dict(base_cfg)
        if isinstance(ov, dict):
            for k in ('model', 'base_url', 'temperature', 'max_tokens', 'timeout'):
                if k in ov and ov[k] not in (None, ''):
                    eff[k] = ov[k]
        prompt_text = get_capabilities_prompt(role) or ''
        return {
            'role': role,
            'effective_model': {
                'model': eff.get('model'),
                'base_url': eff.get('base_url'),
                'temperature': eff.get('temperature'),
                'max_tokens': eff.get('max_tokens'),
                'timeout': eff.get('timeout')
            },
            'prompt': prompt_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

__all__ = ["router"]
