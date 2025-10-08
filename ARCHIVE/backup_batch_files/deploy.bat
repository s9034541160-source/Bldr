@echo off
echo Deploying Bldr Empire v2...

REM Stop any existing containers
echo Stopping existing containers...
docker-compose down

REM Pull latest images
echo Pulling latest images...
docker-compose pull

REM Start services
echo Starting services...
docker-compose up -d

echo Deployment complete!
echo Frontend available at http://localhost:3000
echo Backend API available at http://localhost:8000
pause