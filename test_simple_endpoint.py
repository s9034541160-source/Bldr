from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

print(f"Number of routes: {len(app.routes)}")
for route in app.routes:
    print(f"  {getattr(route, 'path', route)}")