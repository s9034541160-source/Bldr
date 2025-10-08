# Bldr Empire v2 Launcher

## Quick Start
- **Start everything**: Run [one_click_start.bat](file:///c%3A/Bldr/one_click_start.bat)
- **Stop everything**: Run [one_click_stop.bat](file:///c%3A/Bldr/one_click_stop.bat)

## What happens when you start the system

When you run [one_click_start.bat](file:///c%3A/Bldr/one_click_start.bat), the following services start automatically:

1. **Redis Server** - For Celery message broker
2. **Celery Worker** - For background task processing
3. **Celery Beat** - For scheduled tasks
4. **FastAPI Backend** - API server on http://localhost:8000
5. **React Frontend** - Dashboard on http://localhost:3001
6. **Telegram Bot** - For user interaction

All services run in the background. Your default browser will automatically open to the dashboard.

## What happens when you stop the system

When you run [one_click_stop.bat](file:///c%3A/Bldr/one_click_stop.bat), all services are properly terminated.

## Troubleshooting

If services don't start properly:
1. Run [one_click_stop.bat](file:///c%3A/Bldr/one_click_stop.bat) to clean up any existing processes
2. Run [one_click_start.bat](file:///c%3A/Bldr/one_click_start.bat) again

If you need to restart just one service:
- For backend/API issues: Run [start_backend.bat](file:///c%3A/Bldr/start_backend.bat)
- For frontend issues: Go to web/bldr_dashboard and run `npm run dev`

## Service URLs

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:3001
- **Health Check**: http://localhost:8000/health
