from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query, Body
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
import asyncio
import os
import tempfile

try:
    from CANONICAL_FUNCTIONS.verify_api_token import verify_api_token
except Exception:
    def verify_api_token():  # type: ignore
        return {"sub": "admin", "role": "admin", "skip_auth": True}

router = APIRouter(prefix="/api/tools/registry", tags=["tools-registry"], dependencies=[Depends(verify_api_token)])

from core.tools_registry import registry, get_event_queue, remove_event_queue, start_watcher_if_needed
from core.tools_registry import ToolsRegistry


def _ensure_loaded():
    # Load existing tools on first access so pre-existing files are visible
    try:
        registry.load_all()
    except Exception:
        pass


@router.get('/list')
async def list_tools():
    try:
        # ensure watcher is running
        start_watcher_if_needed()
        _ensure_loaded()
        return {"status": "success", "tools": registry.list_tools()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/names')
async def list_tool_names():
    try:
        _ensure_loaded()
        out = []
        for key, lt in list(registry.tools.items()):
            try:
                out.append({
                    'key': key,
                    'manifest_name': getattr(lt.manifest, 'name', None),
                    'category': getattr(lt.manifest, 'category', None),
                    'status': lt.status,
                    'filepath': lt.filepath,
                })
            except Exception:
                continue
        return {"status": "success", "items": out, "count": len(out)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/info')
async def get_tool_info(name: str = Query(...)):
    try:
        _ensure_loaded()
        info = registry.get_info(name)
        if not info:
            # try reload all and search again
            _ensure_loaded()
            info = registry.get_info(name)
            if not info:
                # fuzzy match by manifest name or suffix
                for key, lt in list(registry.tools.items()):
                    try:
                        n = getattr(lt.manifest, 'name', None)
                        if (n and n.lower() == name.lower()) or key.lower().endswith('.'+name.lower()) or key.lower() == name.lower():
                            info = registry.get_info(key) or {
                                "manifest": lt.manifest.model_dump(),
                                "status": lt.status,
                                "error": lt.error,
                                "checksum": lt.checksum,
                                "mtime": lt.mtime,
                                "last_loaded": lt.last_loaded,
                                "filepath": lt.filepath,
                            }
                            break
                    except Exception:
                        continue
            if not info:
                raise HTTPException(status_code=404, detail="tool not found")
        return {"status": "success", "tool": info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/enable')
async def enable_tool(name: str = Query(...)):
    try:
        _ensure_loaded()
        ok = registry.set_enabled(name, True)
        if not ok:
            raise HTTPException(status_code=400, detail="cannot enable tool")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/disable')
async def disable_tool(name: str = Query(...)):
    try:
        _ensure_loaded()
        ok = registry.set_enabled(name, False)
        if not ok:
            raise HTTPException(status_code=400, detail="cannot disable tool (maybe system)")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/reload')
async def reload_tools(name: Optional[str] = Query(None)):
    try:
        _ensure_loaded()
        reloaded = registry.reload(name)
        return {"status": "success", "reloaded": reloaded}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/register')
async def register_tool(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith('.py'):
            raise HTTPException(status_code=400, detail="only .py files allowed")
        fd, path = tempfile.mkstemp(suffix='_'+file.filename)
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(await file.read())
            key = registry.register_file(path)
            return {"status": "success", "name": key}
        finally:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/stream')
async def stream_events():
    try:
        start_watcher_if_needed()
        queue = get_event_queue()
        async def event_generator():
            try:
                while True:
                    data = await queue.get()
                    yield f"data: {data}\n\n"
            except asyncio.CancelledError:
                pass
            finally:
                remove_event_queue(queue)
        return StreamingResponse(event_generator(), media_type='text/event-stream')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/update-manifest')
async def update_manifest(name: str = Query(...), patch: Dict[str, Any] = Body(...)):
    try:
        _ensure_loaded()
        ok = registry.update_manifest_override(name, patch)
        if not ok:
            _ensure_loaded()
            ok = registry.update_manifest_override(name, patch)
            if not ok:
                raise HTTPException(status_code=404, detail='tool not found')
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/execute')
async def execute_tool(name: str = Query(...), params: Dict[str, Any] = Body(default={})):  # kwargs
    try:
        _ensure_loaded()
        res = registry.execute(name, **(params or {}))
        if res.status == 'error' and 'not found' in (res.error or '').lower():
            _ensure_loaded()
            # try aliases
            alt = None
            for key in list(registry.tools.keys()):
                if key.lower().endswith('.'+name.lower()) or key.lower() == name.lower():
                    alt = key
                    break
            res = registry.execute(alt or name, **(params or {}))
        return res.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/create-template')
async def create_template(name: str = Query(...), namespace: str = Query('custom')):
    try:
        # basic sanitation
        safe_name = ''.join([c for c in name if c.isalnum() or c in ('_', '-')]).strip('_-') or 'new_tool'
        base_dir = registry.base_dir
        target_dir = os.path.join(base_dir, namespace)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, f"{safe_name}.py")
        if os.path.exists(target_path):
            raise HTTPException(status_code=400, detail='tool file already exists')
        template = f"""# namespace:{namespace}
from typing import Any, Dict
from pydantic import BaseModel

manifest = {{
    'name': '{safe_name}',
    'version': '0.1.0',
    'title': '{safe_name}',
    'description': 'Describe your tool',
    'category': 'other',
    'ui_placement': 'tools',
    'enabled': True,
    'system': False,
    'entrypoint': 'tools.{namespace}.{safe_name}:execute',
    'params': [
        {{ 'name': 'text', 'type': 'string', 'required': False, 'description': 'Input text' }}
    ],
    'outputs': ['result']
}}

def execute(**kwargs) -> Dict[str, Any]:
    text = kwargs.get('text') or 'Hello world'
    return {{ 'status': 'success', 'data': {{ 'result': f'You said: {{text}}' }} }}
"""
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(template)
        # load immediately
        key = registry.load_from_file(target_path)
        return {"status": "success", "name": key}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


