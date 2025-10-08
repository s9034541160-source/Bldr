# Redis Installation Guide for Windows

## Option 1: Using Docker (Recommended)

The easiest way to run Redis on Windows is using Docker:

1. Install Docker Desktop from https://www.docker.com/products/docker-desktop
2. Run the following command:
   ```bash
   docker run -d -p 6379:6379 --name bldr-redis redis:alpine
   ```

## Option 2: Using Windows Subsystem for Linux (WSL)

1. Install WSL2 if you haven't already:
   ```powershell
   wsl --install
   ```

2. Install Redis in your Linux distribution:
   ```bash
   sudo apt update
   sudo apt install redis-server
   ```

3. Start Redis:
   ```bash
   sudo service redis-server start
   ```

## Option 3: Using Windows Package Manager (winget)

1. Install Redis using winget:
   ```powershell
   winget install Redis.Redis
   ```

2. Start Redis service:
   ```powershell
   redis-server
   ```

## Option 4: Manual Installation

1. Download Redis for Windows from https://github.com/tporadowski/redis/releases
2. Extract to a folder (e.g., C:\redis)
3. Add the folder to your PATH environment variable
4. Start Redis:
   ```powershell
   redis-server
   ```

## Verification

To verify Redis is running, open a command prompt and run:
```powershell
redis-cli ping
```

If Redis is running correctly, you should see:
```
PONG
```

## Troubleshooting

### Error: "redis-server is not recognized"

This means Redis is not installed or not in your PATH. Follow one of the installation options above.

### Error: "Could not connect to Redis"

This means Redis is not running. Start the Redis server using one of the methods above.

### Port already in use

If port 6379 is already in use, you can:
1. Stop the existing Redis process:
   ```powershell
   taskkill /f /im redis-server.exe
   ```
2. Or use a different port:
   ```powershell
   redis-server --port 6380
   ```