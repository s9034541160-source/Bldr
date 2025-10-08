# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: run_server
# Основной источник: C:\Bldr\backend\main.py
# Дубликаты (для справки):
#   - C:\Bldr\main.py
#================================================================================

from typing import Any

def run_server(app: Any, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
    """Start uvicorn server for provided FastAPI app (canonical)."""
    try:
        import uvicorn
        uvicorn.run(app, host=host, port=port, reload=debug)
    except Exception as e:
        print(f"Failed to start server: {e}")
