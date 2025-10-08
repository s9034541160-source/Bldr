from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница API"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SuperBuilder Tools API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { text-align: center; color: #2c3e50; }
            .section { margin: 30px 0; padding: 20px; border-left: 4px solid #3498db; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { color: #27ae60; font-weight: bold; }
            a { color: #3498db; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏗️ SuperBuilder Tools API</h1>
                <p>REST API для инструментов анализа строительных проектов</p>
            </div>
            
            <div class="section">
                <h2>📚 Документация</h2>
                <p>
                    <a href="/docs" target="_blank">Swagger UI</a> | 
                    <a href="/redoc" target="_blank">ReDoc</a>
                </p>
            </div>
            
            <div class="section">
                <h2>🔧 Основные endpoints</h2>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> /api/tools/analyze/estimate</div>
                    <p>Анализ сметной документации</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> /api/tools/analyze/images</div>
                    <p>Анализ изображений и чертежейей</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> /api/tools/analyze/documents</div>
                    <p>Анализ проектных документов</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> /api/tools/jobs/{job_id}/status</div>
                    <p>Получить статус задачи</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> /api/tools/jobs/active</div>
                    <p>Список активных задач</p>
                </div>
            </div>
            
            <div class="section">
                <h2>🔗 WebSocket</h2>
                <p>
                    <strong>URL:</strong> ws://localhost:8000/ws/<br>
                    <strong>Использование:</strong> Real-time уведомления о статусе задач
                </p>
            </div>
            
            <div class="section">
                <h2>💡 Статус системы</h2>
                <div class="endpoint">
                    <div><span class="method">GET</span> /api/tools/health</div>
                    <p>Проверка работоспособности системы</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> /api/tools/info</div>
                    <p>Информация о доступных инструментах</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

print(f"Number of routes: {len(app.routes)}")
for route in app.routes:
    print(f"  {getattr(route, 'path', route)}")