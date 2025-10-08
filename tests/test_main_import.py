# Test importing main.py and checking if endpoints are registered
try:
    import main
    print("Import successful")
    print(f"Number of routes: {len(main.app.routes)}")
    
    # Check if specific endpoints are registered
    endpoint_paths = [getattr(route, 'path', str(route)) for route in main.app.routes]
    
    print("Checking for specific endpoints:")
    for endpoint in ["/", "/health", "/auth/debug"]:
        if endpoint in endpoint_paths:
            print(f"  ✓ {endpoint} - Registered")
        else:
            print(f"  ✗ {endpoint} - Not registered")
            
    print("\nAll registered endpoints:")
    for path in sorted(endpoint_paths):
        print(f"  {path}")
        
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()