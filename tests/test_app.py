import main

# Print the number of routes registered in the app
print(f"Number of routes: {len(main.app.routes)}")

# Print the paths of all routes
print("Routes:")
for route in main.app.routes:
    print(f"  {route.path}")