import os
import sys
import json
import time
import types
import importlib.util
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
import threading
import asyncio

from pydantic import BaseModel, Field


class ToolParam(BaseModel):
    name: str
    type: str
    required: bool = False
    default: Any = None
    description: Optional[str] = None
    enum: Optional[List[Any]] = None
    ui: Optional[Dict[str, Any]] = None


class ToolManifest(BaseModel):
    name: str
    version: str
    title: str
    description: str
    category: str
    ui_placement: str
    enabled: bool = True
    system: bool = False
    entrypoint: str
    params: List[ToolParam] = []
    outputs: List[str] = []
    permissions: List[str] = []
    compatibility: Optional[Dict[str, str]] = None
    # UI configuration for result display
    result_display: Optional[Dict[str, Any]] = None


class ToolResult(BaseModel):
    status: str
    data: Dict[str, Any] = {}
    files: List[str] = []
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None
    execution_time: Optional[float] = None
    # Standardized result fields for UI display
    result_type: Optional[str] = None  # 'text', 'json', 'file', 'image', 'table', 'chart'
    result_title: Optional[str] = None
    result_content: Optional[str] = None  # For text results
    result_url: Optional[str] = None  # For file/image URLs
    result_table: Optional[List[Dict[str, Any]]] = None  # For table data
    result_chart_config: Optional[Dict[str, Any]] = None  # For chart configuration


@dataclass
class LoadedTool:
    manifest: ToolManifest
    module: types.ModuleType
    entry_func: Any
    filepath: str
    checksum: str
    mtime: float
    last_loaded: float = field(default_factory=lambda: time.time())
    status: str = "ok"  # ok|error|disabled
    error: Optional[str] = None


def _file_checksum(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


class ToolsRegistry:
    def __init__(self, base_dir: Optional[str] = None) -> None:
        self.base_dir = base_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tools')
        self.tools: Dict[str, LoadedTool] = {}
        self.overrides_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.json')
        os.makedirs(self.base_dir, exist_ok=True)
        # subscribers for live events (asyncio.Queue[str])
        self._subscribers: List[asyncio.Queue] = []
        self._watch_thread: Optional[threading.Thread] = None
        self._watch_stop = threading.Event()

    def _apply_overrides(self, manifest: ToolManifest) -> ToolManifest:
        try:
            if os.path.exists(self.overrides_path):
                with open(self.overrides_path, 'r', encoding='utf-8') as f:
                    data = json.load(f) or {}
                ov = (data.get('tools_overrides') or {}).get(manifest.name)
                if isinstance(ov, dict):
                    if 'enabled' in ov and not manifest.system:
                        manifest.enabled = bool(ov['enabled'])
                    if 'ui_placement' in ov and isinstance(ov['ui_placement'], str):
                        manifest.ui_placement = ov['ui_placement']
                    # optional editable metadata overrides
                    for k in ('title', 'description', 'category'):
                        if k in ov and isinstance(ov[k], str) and ov[k].strip():
                            setattr(manifest, k, ov[k])
                    # params override (replace list fully if provided)
                    if isinstance(ov.get('params'), list):
                        try:
                            manifest.params = [ToolParam.model_validate(p) if not isinstance(p, ToolParam) else p for p in ov['params']]
                        except Exception:
                            pass
        except Exception:
            pass
        return manifest

    def _load_module_from_path(self, path: str) -> Tuple[types.ModuleType, Any, ToolManifest]:
        spec = importlib.util.spec_from_file_location(f"bldr_tool_{hashlib.md5(path.encode()).hexdigest()}", path)
        if spec is None or spec.loader is None:
            raise RuntimeError("spec load failed")
        module = importlib.util.module_from_spec(spec)
        loader = spec.loader
        assert loader is not None
        loader.exec_module(module)  # type: ignore[arg-type]
        manifest = getattr(module, 'manifest', None)
        if manifest is None:
            raise RuntimeError("manifest not found in tool module")
        if isinstance(manifest, dict):
            manifest = ToolManifest(**manifest)
        elif not isinstance(manifest, ToolManifest):
            manifest = ToolManifest.model_validate(manifest)
        manifest = self._apply_overrides(manifest)
        # Resolve entrypoint
        entry = getattr(module, 'execute', None)
        if not entry and isinstance(manifest.entrypoint, str):
            # entrypoint like pkg.mod:func not used for loaded module; prefer module.execute
            pass
        if not entry:
            raise RuntimeError("execute() not found in tool module")
        return module, entry, manifest

    def scan(self) -> List[str]:
        found: List[str] = []
        for root, _, files in os.walk(self.base_dir):
            for fn in files:
                if fn.endswith('.py') and not fn.startswith('_'):
                    found.append(os.path.join(root, fn))
        return found

    def load_all(self) -> None:
        for path in self.scan():
            try:
                self.load_from_file(path)
            except Exception as e:
                # record error entry with minimal info
                key = os.path.splitext(os.path.relpath(path, self.base_dir))[0].replace(os.sep, '.')
                self.tools[key] = LoadedTool(
                    manifest=ToolManifest(
                        name=key, version="0.0.0", title=key, description=str(e),
                        category="general", ui_placement="tools", enabled=False, system=False,
                        entrypoint="",
                    ),
                    module=types.ModuleType(key), entry_func=lambda **_: None,
                    filepath=path, checksum=_file_checksum(path), mtime=os.path.getmtime(path),
                    status="error", error=str(e)
                )

    def load_from_file(self, path: str) -> str:
        module, entry, manifest = self._load_module_from_path(path)
        name = manifest.name or os.path.splitext(os.path.basename(path))[0]
        key = name
        # cleanup old module with same key
        for mod_name in list(sys.modules.keys()):
            if mod_name.startswith('bldr_tool_'):
                # best-effort; allow multiple co-exist
                pass
        lt = LoadedTool(
            manifest=manifest,
            module=module,
            entry_func=entry,
            filepath=path,
            checksum=_file_checksum(path),
            mtime=os.path.getmtime(path),
            status=('disabled' if (not manifest.enabled and not manifest.system) else 'ok')
        )
        self.tools[key] = lt
        # on_load hook
        try:
            if hasattr(module, 'on_load') and callable(getattr(module, 'on_load')):
                module.on_load()
        except Exception:
            pass
        # publish event
        self._publish({"type": "tool_loaded", "name": key, "mtime": lt.mtime, "checksum": lt.checksum})
        return key

    def reload(self, name: Optional[str] = None) -> List[str]:
        reloaded: List[str] = []
        for key, lt in list(self.tools.items()):
            if name and key != name:
                continue
            try:
                # on_unload
                try:
                    if hasattr(lt.module, 'on_unload') and callable(getattr(lt.module, 'on_unload')):
                        lt.module.on_unload()
                except Exception:
                    pass
                self.load_from_file(lt.filepath)
                reloaded.append(key)
            except Exception as e:
                lt.status = 'error'
                lt.error = str(e)
        if reloaded:
            self._publish({"type": "tools_reloaded", "names": reloaded})
        return reloaded

    def get_info(self, name: str) -> Optional[Dict[str, Any]]:
        lt = self.tools.get(name)
        if not lt:
            return None
        return {
            'manifest': lt.manifest.model_dump(),
            'status': lt.status,
            'error': lt.error,
            'checksum': lt.checksum,
            'mtime': lt.mtime,
            'last_loaded': lt.last_loaded,
            'filepath': lt.filepath,
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for key, lt in self.tools.items():
            info = self.get_info(key)
            if info:
                items.append(info)
        return items

    def set_enabled(self, name: str, enabled: bool) -> bool:
        lt = self.tools.get(name)
        if not lt:
            return False
        if lt.manifest.system and not enabled:
            return False
        lt.manifest.enabled = enabled
        lt.status = 'ok' if enabled else 'disabled'
        # persist override
        try:
            data = {}
            if os.path.exists(self.overrides_path):
                with open(self.overrides_path, 'r', encoding='utf-8') as f:
                    data = json.load(f) or {}
            to = data.get('tools_overrides') or {}
            to[name] = { **(to.get(name) or {}), 'enabled': enabled }
            data['tools_overrides'] = to
            with open(self.overrides_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        self._publish({"type": "tool_enabled" if enabled else "tool_disabled", "name": name})
        return True

    def update_manifest_override(self, name: str, patch: Dict[str, Any]) -> bool:
        lt = self.tools.get(name)
        if not lt:
            return False
        # persist override
        data = {}
        try:
            if os.path.exists(self.overrides_path):
                with open(self.overrides_path, 'r', encoding='utf-8') as f:
                    data = json.load(f) or {}
        except Exception:
            data = {}
        to = data.get('tools_overrides') or {}
        cur = to.get(name) or {}
        allowed = {'enabled', 'ui_placement', 'title', 'description', 'category', 'params'}
        for k, v in (patch or {}).items():
            if k in allowed:
                cur[k] = v
        to[name] = cur
        data['tools_overrides'] = to
        try:
            with open(self.overrides_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        # apply to in-memory manifest immediately
        try:
            self.tools[name].manifest = self._apply_overrides(self.tools[name].manifest)
            self._publish({"type": "tool_manifest_updated", "name": name})
        except Exception:
            pass
        return True

    def register_file(self, temp_path: str) -> str:
        # Move file into base_dir under namespace if present in first line: # namespace:norms
        ns = 'custom'
        try:
            with open(temp_path, 'r', encoding='utf-8') as f:
                first = f.readline()
            if first.startswith('# namespace:'):
                ns = first.split(':', 1)[1].strip() or 'custom'
        except Exception:
            pass
        target_dir = os.path.join(self.base_dir, ns)
        os.makedirs(target_dir, exist_ok=True)
        basename = os.path.basename(temp_path)
        if not basename.endswith('.py'):
            basename += '.py'
        target = os.path.join(target_dir, basename)
        os.replace(temp_path, target)
        key = self.load_from_file(target)
        self._publish({"type": "tool_registered", "name": key})
        return key

    def execute(self, name: str, **kwargs) -> ToolResult:
        lt = self.tools.get(name)
        if not lt:
            return ToolResult(status='error', error=f'tool {name} not found')
        if lt.status != 'ok':
            return ToolResult(status='error', error=f'tool {name} disabled or error')
        import time as _t
        t0 = _t.time()
        try:
            res = lt.entry_func(**kwargs)
            if hasattr(res, '__await__'):
                # allow sync wrapper to return awaitable; run inline
                import asyncio
                res = asyncio.get_event_loop().run_until_complete(res)  # best-effort in sync context
            if isinstance(res, dict):
                data = res
                return ToolResult(status=data.get('status', 'success'), data=data.get('data') or data, files=data.get('files') or [], metadata=data.get('metadata') or {}, error=data.get('error'))
            if isinstance(res, ToolResult):
                return res
            return ToolResult(status='success', data={'result': res})
        except Exception as e:
            return ToolResult(status='error', error=str(e))
        finally:
            # simple timing
            pass

# Singleton
registry = ToolsRegistry()

# --- Live updates / SSE helpers ---
def get_event_queue() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    registry._subscribers.append(q)
    return q

def remove_event_queue(q: asyncio.Queue) -> None:
    try:
        registry._subscribers.remove(q)
    except ValueError:
        pass

def start_watcher_if_needed() -> None:
    if registry._watch_thread and registry._watch_thread.is_alive():
        return
    def _loop():
        last_mtimes: Dict[str, float] = {}
        while not registry._watch_stop.is_set():
            try:
                for path in registry.scan():
                    try:
                        m = os.path.getmtime(path)
                    except Exception:
                        continue
                    if path not in last_mtimes:
                        last_mtimes[path] = m
                        continue
                    if m != last_mtimes[path]:
                        last_mtimes[path] = m
                        try:
                            # find key by filepath
                            name = None
                            for k, lt in list(registry.tools.items()):
                                if lt.filepath == path:
                                    name = k
                                    break
                            if name:
                                registry.reload(name)
                            else:
                                # new file discovered
                                registry.load_from_file(path)
                        except Exception:
                            pass
                # detect deleted files
                existing_paths = set(registry.scan())
                for k, lt in list(registry.tools.items()):
                    if lt.filepath and lt.filepath not in existing_paths:
                        registry.tools.pop(k, None)
                        registry._publish({"type": "tool_removed", "name": k})
                time.sleep(1.0)
            except Exception:
                time.sleep(1.0)
    registry._watch_stop.clear()
    registry._watch_thread = threading.Thread(target=_loop, daemon=True)
    registry._watch_thread.start()

def stop_watcher() -> None:
    if registry._watch_thread and registry._watch_thread.is_alive():
        registry._watch_stop.set()
        try:
            registry._watch_thread.join(timeout=2.0)
        except Exception:
            pass

def _publish_event_to_queue(q: asyncio.Queue, payload: Dict[str, Any]) -> None:
    try:
        q.put_nowait(json.dumps(payload, ensure_ascii=False))
    except Exception:
        pass

def _publish(payload: Dict[str, Any]) -> None:
    registry._publish(payload)

def _ensure_coroutine(func: Callable, *args, **kwargs):
    try:
        res = func(*args, **kwargs)
        return res
    except Exception:
        return None

def _queue_cleanup():
    # best-effort cleanup of closed loops
    pass

def _safe_iter_subscribers() -> List[asyncio.Queue]:
    return list(registry._subscribers)

def _publish_to_all(payload: Dict[str, Any]) -> None:
    for q in _safe_iter_subscribers():
        _publish_event_to_queue(q, payload)

# attach method to registry
def _registry_publish(self, payload: Dict[str, Any]) -> None:
    _publish_to_all(payload)

ToolsRegistry._publish = _registry_publish  # type: ignore[attr-defined]

