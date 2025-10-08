import main

# Test if the root endpoint function works
try:
    # The root function is async, so we need to await it
    import asyncio
    result = asyncio.run(main.root())
    print("Root endpoint function works")
    print(f"Result type: {type(result)}")
    print(f"Result length: {len(str(result)) if hasattr(result, '__str__') else 'N/A'}")
except Exception as e:
    print(f"Root endpoint function failed: {e}")
    import traceback
    traceback.print_exc()