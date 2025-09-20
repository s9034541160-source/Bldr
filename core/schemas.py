from typing import Any, Dict, Optional
from pydantic import BaseModel

class BaseResponse(BaseModel):
    status: str
    data: Optional[Any] = None
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


def ok(data: Any = None, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"status": "success", "data": data, "error": None, "meta": meta}


def err(error: Any, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"status": "error", "data": None, "error": str(error), "meta": meta}


# Helpers for optional unified wrapping
UNIFY_QUERY_PARAM = "unify"
UNIFY_HEADER = "X-Response-Format"
UNIFY_HEADER_VALUE = "unified"
UNIFY_ACCEPT = "application/vnd.bldr.v2+json"


def should_unify(request) -> bool:
    """Return True if the client requested unified response format.
    Triggers on:
    - ?unify=true
    - X-Response-Format: unified
    - Accept: application/vnd.bldr.v2+json
    """
    try:
        if request is None:
            return False
        qp = request.query_params.get(UNIFY_QUERY_PARAM)
        if qp and qp.lower() in ("1", "true", "yes"):  # ?unify=true
            return True
        hdr = request.headers.get(UNIFY_HEADER, "").lower()
        if hdr == UNIFY_HEADER_VALUE:
            return True
        accept = request.headers.get("accept", "")
        if UNIFY_ACCEPT in accept:
            return True
    except Exception:
        return False
    return False


def unify_body(obj: Any) -> Dict[str, Any]:
    """Wrap arbitrary object into unified schema if it is not already unified.
    If obj is a dict with 'status' key, pass-through.
    """
    if isinstance(obj, dict) and "status" in obj:
        return obj
    return ok(obj)
