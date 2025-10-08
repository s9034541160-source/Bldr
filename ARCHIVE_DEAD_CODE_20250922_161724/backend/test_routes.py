from main import app as main_app
from core.bldr_api import app as tools_app
from fastapi.routing import APIRoute

print("Main app routes:")
for route in main_app.routes:
    if isinstance(route, APIRoute):
        print(f"  {route.path}")

print("\nTools app routes:")
for route in tools_app.routes:
    if isinstance(route, APIRoute):
        print(f"  {route.path}")