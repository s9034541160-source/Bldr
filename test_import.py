try:
    import main
    print("Import successful")
    print(f"Number of routes: {len(main.app.routes)}")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()