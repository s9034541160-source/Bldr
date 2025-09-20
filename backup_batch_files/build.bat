@echo off
echo Building Bldr Empire v2...

REM Build backend
echo Building backend...
docker build -t bldr-backend .

REM Build frontend
echo Building frontend...
docker build -f web/bldr_dashboard/Dockerfile.frontend -t bldr-frontend web/bldr_dashboard

echo Build complete!
pause