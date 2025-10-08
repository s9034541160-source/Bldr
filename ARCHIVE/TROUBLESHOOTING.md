# Bldr Empire v2 - Troubleshooting Guide

## Common Issues and Solutions

### 1. Neo4j Connection Issues

**Problem**: The system cannot connect to Neo4j database
**Error Messages**:
- `Couldn't connect to localhost:7687`
- `Подключение не установлено, т.к. конечный компьютер отверг запрос на подключение`
- `The client is unauthorized due to authentication failure`
- `The client has provided incorrect authentication details too many times in a row`

**Solution**:
1. Make sure Neo4j is running:
   - Open Neo4j Desktop
   - Create or start a database instance
   - Ensure it's listening on port 7687

2. Run the Neo4j setup script:
   ```
   setup_neo4j.bat
   ```

3. If you continue to have issues, reset the authentication:
   - Stop Neo4j
   - Reset the DBMS password to the default value `neopassword` in Neo4j Desktop
   - Start the database instance
   - Run the setup script again

4. **Authentication Rate Limit Exceeded**:
   If you see `AuthenticationRateLimit` errors, you've made too many failed authentication attempts. Wait a few minutes and try again with the correct credentials, or reset the password as described above.

### 2. Ollama Module Missing

**Problem**: Warning about missing Ollama module
**Error Message**:
- `Ollama not available: No module named 'ollama'`

**Solution**:
This is just a warning. The system will use LM Studio instead of Ollama. No action needed unless you specifically want to use Ollama.

To install Ollama:
1. Download and install Ollama from https://ollama.ai
2. Install required models:
   ```
   ollama pull deepseek/deepseek-r1-0528-qwen3-8b
   ollama pull qwen/qwen2.5-vl-7b
   ollama pull mistralai/mistral-nemo-instruct-2407
   ```

### 3. Port Already in Use

**Problem**: Services fail to start because ports are already in use
**Error**: Port conflicts for Redis (6379), Qdrant (6333), Backend (8000), or Frontend (3001)

**Solution**:
1. Run the stop script to kill existing processes:
   ```
   one_click_stop.bat
   ```

2. If that doesn't work, manually kill the processes:
   ```
   taskkill /F /IM redis-server.exe
   taskkill /F /IM java.exe
   taskkill /F /IM node.exe
   taskkill /F /IM uvicorn.exe
   taskkill /F /IM python.exe
   ```

### 4. Template Creation Skipped

**Problem**: Template creation is skipped due to Neo4j issues
**Warning**:
- `Neo4j not available, skipping template creation`

**Solution**:
1. Fix the Neo4j connection issues (see #1 above)
2. Restart the system after Neo4j is properly configured

### 5. Docker/Qdrant Issues

**Problem**: Qdrant container fails to start
**Warning**:
- `Failed to start Qdrant container. Docker may not be properly configured.`

**Solution**:
1. Make sure Docker Desktop is installed and running
2. If Docker is not available, the system will use in-memory storage as fallback
3. For production use, install Docker Desktop from https://www.docker.com/products/docker-desktop/

## Manual Neo4j Setup Steps

1. **Install Neo4j Desktop**:
   - Download from https://neo4j.com/download/
   - Install and launch Neo4j Desktop

2. **Create a Database Instance**:
   - Click "New" -> "Local DBMS"
   - Set password to `neopassword` (default)
   - Click "Create"

3. **Start the Database**:
   - Click the "Start" button for your database instance
   - Wait for it to show as "Running"

4. **Configure Ports**:
   - Click on your database instance
   - Go to "Settings"
   - Ensure these ports are set:
     - Bolt: 7687
     - HTTP: 7474
     - HTTPS: 7473

5. **Run Setup Script**:
   ```
   setup_neo4j.bat
   ```

## Verifying Services

To check if services are running:

1. **Check ports**:
   ```
   netstat -an | findstr "7687"
   netstat -an | findstr "6379"
   netstat -an | findstr "8000"
   netstat -an | findstr "3001"
   ```

2. **Check processes**:
   ```
   tasklist | findstr "java"
   tasklist | findstr "redis"
   tasklist | findstr "node"
   tasklist | findstr "python"
   ```

## Health Check

To manually check if the backend is healthy:

1. Open browser and go to:
   ```
   http://localhost:8000/health
   ```

2. Or use PowerShell:
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET
   ```

A healthy response should look like:
```json
{
  "status": "ok",
  "components": {
    "db": "ok",
    "celery": "ok"
  }
}
```

## Important Notes

### Neo4j Protocol
The system now uses `neo4j://` protocol instead of `bolt://` for better compatibility with Neo4j Desktop.

### Default Credentials
The system uses Neo4j credentials (`neo4j`/`neopassword`) as configured in the .env file. Make sure these credentials match your Neo4j instance configuration.

### Manual Database Management
If you're experiencing persistent Neo4j issues:
1. Open Neo4j Desktop
2. Stop any running database instances
3. Delete the problematic database
4. Create a new database with default credentials
5. Start the new database instance