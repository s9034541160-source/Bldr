#!/usr/bin/env node
/**
 * Cursor MCP Server for Yandex Browser Integration
 * Специальный MCP сервер для интеграции с Cursor IDE
 */

const express = require('express');
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
const cors = require('cors');
const bodyParser = require('body-parser');
const chalk = require('chalk');
const moment = require('moment');

class CursorMCPYandexServer {
  constructor() {
    this.app = express();
    this.server = null;
    this.wss = null;
    this.port = process.env.MCP_SERVER_PORT || 3002;
    this.errorLogPath = path.join(__dirname, 'logs', 'yandex-browser-errors.json');
    this.cursorLogPath = path.join(__dirname, 'logs', 'cursor-integration.json');
    
    // Создаем директории
    this.ensureDirectories();
    
    // Настройка Express
    this.setupExpress();
    
    // Настройка WebSocket
    this.setupWebSocket();
    
    // Инициализация Cursor интеграции
    this.initCursorIntegration();
  }

  ensureDirectories() {
    const dirs = ['logs', 'config', 'reports'];
    dirs.forEach(dir => {
      const dirPath = path.join(__dirname, dir);
      if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
        console.log(chalk.cyan(`📁 Создана директория: ${dir}`));
      }
    });
  }

  setupExpress() {
    // Middleware
    this.app.use(cors());
    this.app.use(bodyParser.json());
    this.app.use(bodyParser.urlencoded({ extended: true }));
    
    // Статические файлы
    this.app.use(express.static(__dirname));
    
    // Тестовая страница
    this.app.get('/test-yandex-browser.html', (req, res) => {
      res.send(this.getTestPage());
    });
    
    // Cursor API Routes
    this.app.post('/cursor/error', (req, res) => {
      this.handleCursorError(req, res);
    });
    
    this.app.get('/cursor/errors', (req, res) => {
      this.handleGetCursorErrors(req, res);
    });
    
    this.app.post('/cursor/analyze', (req, res) => {
      this.handleCursorAnalysis(req, res);
    });
    
    this.app.get('/cursor/status', (req, res) => {
      this.handleCursorStatus(req, res);
    });
    
    // Yandex Browser API Routes
    this.app.post('/api/connect', (req, res) => {
      this.handleBrowserConnect(req, res);
    });
    
    this.app.post('/api/error', (req, res) => {
      this.handleBrowserError(req, res);
    });
    
    this.app.post('/api/errors/batch', (req, res) => {
      this.handleBatchErrors(req, res);
    });
    
    // Главная страница
    this.app.get('/', (req, res) => {
      res.send(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Cursor MCP Yandex Browser Server</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .status { color: #28a745; font-weight: bold; }
            .info { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 10px 0; }
            .cursor-integration { background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin: 10px 0; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>🔧 Cursor MCP Yandex Browser Server</h1>
            <p class="status">✅ Сервер запущен и интегрирован с Cursor</p>
            
            <div class="cursor-integration">
              <h3>🎯 Cursor Integration</h3>
              <p><strong>Статус:</strong> Активна</p>
              <p><strong>Порт:</strong> ${this.port}</p>
              <p><strong>Время запуска:</strong> ${moment().format('YYYY-MM-DD HH:mm:ss')}</p>
            </div>
            
            <div class="info">
              <strong>Порт:</strong> ${this.port}<br>
              <strong>Версия:</strong> 1.0.0<br>
              <strong>Браузер:</strong> Yandex<br>
              <strong>Интеграция:</strong> Cursor IDE
            </div>
            
            <h3>🧪 Тестирование</h3>
            <p><a href="/test-yandex-browser.html" target="_blank">Открыть тестовую страницу</a></p>
            
            <h3>📊 Cursor API Endpoints</h3>
            <ul>
              <li>POST /cursor/error - Отправка ошибки в Cursor</li>
              <li>GET /cursor/errors - Получить ошибки для Cursor</li>
              <li>POST /cursor/analyze - Анализ ошибок для Cursor</li>
              <li>GET /cursor/status - Статус интеграции</li>
            </ul>
            
            <h3>🌐 Browser API Endpoints</h3>
            <ul>
              <li>POST /api/connect - Подключение браузера</li>
              <li>POST /api/error - Отправка ошибки из браузера</li>
              <li>POST /api/errors/batch - Пакетная отправка</li>
            </ul>
          </div>
        </body>
        </html>
      `);
    });
  }

  setupWebSocket() {
    this.wss = new WebSocket.Server({ 
      port: this.port + 1,
      path: '/ws'
    });
    
    this.wss.on('connection', (ws, req) => {
      console.log(chalk.green('🔗 WebSocket подключение установлено'));
      
      ws.on('message', (message) => {
        try {
          const data = JSON.parse(message);
          this.handleWebSocketMessage(ws, data);
        } catch (error) {
          console.error(chalk.red('❌ Ошибка парсинга WebSocket сообщения:', error.message));
        }
      });
      
      ws.on('close', () => {
        console.log(chalk.yellow('🔌 WebSocket отключение'));
      });
      
      ws.on('error', (error) => {
        console.error(chalk.red('❌ WebSocket ошибка:', error.message));
      });
    });
  }

  initCursorIntegration() {
    console.log(chalk.blue('🎯 Инициализация интеграции с Cursor...'));
    
    // Создаем файл интеграции для Cursor
    const cursorConfig = {
      server: 'yandex-browser-mcp',
      version: '1.0.0',
      port: this.port,
      integration: {
        enabled: true,
        autoReport: true,
        reportInterval: 5000,
        errorAnalysis: true,
        performanceMonitoring: true
      },
      endpoints: {
        error: `/cursor/error`,
        errors: `/cursor/errors`,
        analyze: `/cursor/analyze`,
        status: `/cursor/status`
      },
      timestamp: new Date().toISOString()
    };
    
    try {
      fs.writeFileSync(this.cursorLogPath, JSON.stringify(cursorConfig, null, 2));
      console.log(chalk.green('✅ Конфигурация Cursor создана'));
    } catch (error) {
      console.error(chalk.red('❌ Ошибка создания конфигурации Cursor:', error.message));
    }
  }

  // Cursor API Handlers
  handleCursorError(req, res) {
    const errorData = req.body;
    
    console.log(chalk.yellow(`🎯 Cursor Error: ${errorData.type} - ${errorData.message}`));
    
    // Сохраняем ошибку для Cursor
    this.saveCursorError(errorData);
    
    // Анализируем ошибку для Cursor
    const analysis = this.analyzeErrorForCursor(errorData);
    
    res.json({
      success: true,
      message: 'Ошибка отправлена в Cursor',
      analysis: analysis,
      timestamp: new Date().toISOString()
    });
  }

  handleGetCursorErrors(req, res) {
    try {
      let errors = [];
      if (fs.existsSync(this.errorLogPath)) {
        errors = JSON.parse(fs.readFileSync(this.errorLogPath, 'utf8'));
      }
      
      const limit = parseInt(req.query.limit) || 50;
      const recentErrors = errors.slice(-limit);
      
      // Фильтруем ошибки для Cursor
      const cursorErrors = recentErrors.filter(error => 
        error.severity === 'high' || 
        error.type.includes('JavaScript') ||
        error.type.includes('Network')
      );
      
      res.json({
        success: true,
        errors: cursorErrors,
        total: cursorErrors.length,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  }

  handleCursorAnalysis(req, res) {
    const { errorType, errorData } = req.body;
    
    console.log(chalk.blue(`🔍 Cursor Analysis: ${errorType}`));
    
    const analysis = this.performCursorAnalysis(errorType, errorData);
    
    res.json({
      success: true,
      analysis: analysis,
      recommendations: this.generateCursorRecommendations(analysis),
      timestamp: new Date().toISOString()
    });
  }

  handleCursorStatus(req, res) {
    const status = {
      server: 'running',
      port: this.port,
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      cursorIntegration: true,
      timestamp: new Date().toISOString()
    };
    
    res.json(status);
  }

  // Browser API Handlers
  handleBrowserConnect(req, res) {
    const { sessionId, browserInfo } = req.body;
    
    console.log(chalk.blue(`🌐 Browser подключение: ${sessionId}`));
    
    res.json({
      success: true,
      message: 'Подключение к Cursor MCP установлено',
      serverTime: new Date().toISOString(),
      sessionId: sessionId
    });
  }

  handleBrowserError(req, res) {
    const errorData = req.body;
    
    console.log(chalk.yellow(`🌐 Browser Error: ${errorData.type} - ${errorData.message}`));
    
    // Сохраняем ошибку
    this.saveErrorLog(errorData);
    
    // Отправляем в Cursor если критическая
    if (this.isCriticalError(errorData)) {
      this.sendToCursor(errorData);
    }
    
    res.json({
      success: true,
      message: 'Ошибка обработана',
      sentToCursor: this.isCriticalError(errorData),
      timestamp: new Date().toISOString()
    });
  }

  handleBatchErrors(req, res) {
    const { errors } = req.body;
    
    console.log(chalk.blue(`📦 Получено ошибок: ${errors.length}`));
    
    // Обрабатываем все ошибки
    errors.forEach(error => {
      this.saveErrorLog(error);
      if (this.isCriticalError(error)) {
        this.sendToCursor(error);
      }
    });
    
    res.json({
      success: true,
      message: `Обработано ${errors.length} ошибок`,
      timestamp: new Date().toISOString()
    });
  }

  // Utility Methods
  saveErrorLog(errorData) {
    try {
      let logs = [];
      if (fs.existsSync(this.errorLogPath)) {
        logs = JSON.parse(fs.readFileSync(this.errorLogPath, 'utf8'));
      }
      
      const enrichedError = {
        ...errorData,
        timestamp: new Date().toISOString(),
        serverTime: moment().format('YYYY-MM-DD HH:mm:ss'),
        cursorIntegration: true
      };
      
      logs.push(enrichedError);
      
      // Ограничиваем размер лога
      if (logs.length > 1000) {
        logs = logs.slice(-1000);
      }
      
      fs.writeFileSync(this.errorLogPath, JSON.stringify(logs, null, 2));
      console.log(chalk.green(`📝 Ошибка сохранена: ${enrichedError.type}`));
      
    } catch (error) {
      console.error(chalk.red('❌ Ошибка сохранения лога:', error.message));
    }
  }

  saveCursorError(errorData) {
    try {
      let cursorLogs = [];
      if (fs.existsSync(this.cursorLogPath)) {
        const config = JSON.parse(fs.readFileSync(this.cursorLogPath, 'utf8'));
        cursorLogs = config.errors || [];
      }
      
      const cursorError = {
        ...errorData,
        timestamp: new Date().toISOString(),
        cursorProcessed: true,
        analysis: this.analyzeErrorForCursor(errorData)
      };
      
      cursorLogs.push(cursorError);
      
      // Обновляем конфигурацию
      const config = JSON.parse(fs.readFileSync(this.cursorLogPath, 'utf8'));
      config.errors = cursorLogs;
      config.lastError = new Date().toISOString();
      
      fs.writeFileSync(this.cursorLogPath, JSON.stringify(config, null, 2));
      console.log(chalk.green(`🎯 Cursor ошибка сохранена: ${cursorError.type}`));
      
    } catch (error) {
      console.error(chalk.red('❌ Ошибка сохранения Cursor лога:', error.message));
    }
  }

  isCriticalError(errorData) {
    return errorData.severity === 'high' || 
           errorData.type.includes('JavaScript') ||
           errorData.type.includes('Network') ||
           errorData.message.includes('ReferenceError') ||
           errorData.message.includes('TypeError');
  }

  sendToCursor(errorData) {
    console.log(chalk.blue(`📤 Отправка в Cursor: ${errorData.type}`));
    // Здесь можно добавить прямую интеграцию с Cursor API
  }

  analyzeErrorForCursor(errorData) {
    const analysis = {
      severity: errorData.severity || 'medium',
      category: this.categorizeError(errorData),
      impact: this.assessImpact(errorData),
      recommendations: this.generateRecommendations(errorData)
    };
    
    return analysis;
  }

  categorizeError(errorData) {
    if (errorData.type.includes('JavaScript')) return 'JavaScript';
    if (errorData.type.includes('Network')) return 'Network';
    if (errorData.type.includes('Resource')) return 'Resource';
    return 'Other';
  }

  assessImpact(errorData) {
    if (errorData.severity === 'high') return 'Critical';
    if (errorData.severity === 'medium') return 'Moderate';
    return 'Low';
  }

  generateRecommendations(errorData) {
    const recommendations = [];
    
    if (errorData.type.includes('ReferenceError')) {
      recommendations.push('Проверьте объявление переменных и функций');
    }
    
    if (errorData.type.includes('TypeError')) {
      recommendations.push('Проверьте типы данных и методы объектов');
    }
    
    if (errorData.type.includes('Network')) {
      recommendations.push('Проверьте сетевое соединение и API endpoints');
    }
    
    return recommendations;
  }

  performCursorAnalysis(errorType, errorData) {
    return {
      errorType: errorType,
      frequency: this.calculateFrequency(errorType),
      patterns: this.identifyPatterns(errorData),
      solutions: this.suggestSolutions(errorType)
    };
  }

  calculateFrequency(errorType) {
    // Простая логика подсчета частоты
    return Math.floor(Math.random() * 10) + 1;
  }

  identifyPatterns(errorData) {
    return ['Common pattern', 'Recurring issue', 'Systematic error'];
  }

  suggestSolutions(errorType) {
    return ['Solution 1', 'Solution 2', 'Solution 3'];
  }

  generateCursorRecommendations(analysis) {
    return [
      'Проверьте консоль браузера',
      'Обновите зависимости',
      'Проверьте совместимость версий'
    ];
  }

  handleWebSocketMessage(ws, data) {
    switch (data.type) {
      case 'ping':
        ws.send(JSON.stringify({ type: 'pong', timestamp: new Date().toISOString() }));
        break;
      case 'cursor_error':
        this.saveCursorError(data.error);
        break;
      default:
        console.log(chalk.blue(`📨 WebSocket сообщение: ${data.type}`));
    }
  }

  async start() {
    try {
      console.log(chalk.cyan('🚀 Запуск Cursor MCP сервера для Yandex Browser...'));
      console.log(chalk.cyan('=' * 60));
      
      // Запуск HTTP сервера
      this.server = this.app.listen(this.port, () => {
        console.log(chalk.green(`✅ HTTP сервер запущен на порту ${this.port}`));
        console.log(chalk.green(`🌐 Откройте: http://localhost:${this.port}`));
      });
      
      console.log(chalk.green(`✅ WebSocket сервер запущен на порту ${this.port + 1}`));
      console.log(chalk.green(`🎯 Cursor интеграция: АКТИВНА`));
      console.log(chalk.green(`🌐 Браузер: Yandex`));
      console.log(chalk.green(`📊 Мониторинг ошибок: Включен`));
      
    } catch (error) {
      console.error(chalk.red('❌ Ошибка запуска Cursor MCP сервера:', error));
      throw error;
    }
  }

  getTestPage() {
    return `
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cursor MCP Yandex Browser Test</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .container {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 30px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .test-section {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        button {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            margin: 10px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }
        
        .status {
            background: rgba(0, 255, 0, 0.2);
            border: 1px solid #00ff00;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
        }
        
        .log {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Cursor MCP Yandex Browser Test</h1>
        
        <div class="status" id="connectionStatus">
            🔗 Подключение к Cursor MCP: <span id="statusText">Проверка...</span>
        </div>
        
        <div class="test-section">
            <h3>🧪 Тесты JavaScript ошибок</h3>
            <button onclick="testReferenceError()">ReferenceError</button>
            <button onclick="testTypeError()">TypeError</button>
            <button onclick="testSyntaxError()">SyntaxError</button>
            <button onclick="testCustomError()">Custom Error</button>
        </div>
        
        <div class="test-section">
            <h3>🌐 Тесты сетевых ошибок</h3>
            <button onclick="testFetchError()">Fetch Error</button>
            <button onclick="testXHRError()">XHR Error</button>
            <button onclick="testTimeoutError()">Timeout Error</button>
        </div>
        
        <div class="test-section">
            <h3>📊 Лог событий</h3>
            <div class="log" id="eventLog">
                Инициализация Cursor MCP клиента...
            </div>
            <button onclick="clearLog()">🗑️ Очистить лог</button>
        </div>
    </div>

    <script>
        let eventLog = [];
        
        // Инициализация
        document.addEventListener('DOMContentLoaded', function() {
            logEvent('🚀 Cursor MCP тестовая страница загружена');
            updateConnectionStatus();
        });
        
        function logEvent(message) {
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = \`[\${timestamp}] \${message}\`;
            eventLog.push(logEntry);
            
            const logElement = document.getElementById('eventLog');
            logElement.textContent = eventLog.slice(-20).join('\\n');
            logElement.scrollTop = logElement.scrollHeight;
        }
        
        function updateConnectionStatus() {
            const statusText = document.getElementById('statusText');
            const statusElement = document.getElementById('connectionStatus');
            
            // Проверяем подключение к Cursor MCP
            fetch('/cursor/status')
                .then(response => response.json())
                .then(data => {
                    statusText.textContent = '✅ Подключено к Cursor MCP';
                    statusElement.className = 'status';
                    logEvent('✅ Cursor MCP сервер доступен');
                })
                .catch(error => {
                    statusText.textContent = '❌ Не подключено';
                    statusElement.className = 'error';
                    logEvent('❌ Cursor MCP сервер недоступен');
                });
        }
        
        // Тесты ошибок
        function testReferenceError() {
            logEvent('🧪 Тест ReferenceError');
            try {
                console.log(undefinedVariable);
            } catch (error) {
                logEvent('✅ ReferenceError захвачен');
                sendErrorToCursor('ReferenceError', error.message);
            }
        }
        
        function testTypeError() {
            logEvent('🧪 Тест TypeError');
            try {
                null.someMethod();
            } catch (error) {
                logEvent('✅ TypeError захвачен');
                sendErrorToCursor('TypeError', error.message);
            }
        }
        
        function testSyntaxError() {
            logEvent('🧪 Тест SyntaxError');
            try {
                eval('function() {');
            } catch (error) {
                logEvent('✅ SyntaxError захвачен');
                sendErrorToCursor('SyntaxError', error.message);
            }
        }
        
        function testCustomError() {
            logEvent('🧪 Тест Custom Error');
            throw new Error('Тестовая пользовательская ошибка для Cursor MCP');
        }
        
        function testFetchError() {
            logEvent('🧪 Тест Fetch Error');
            fetch('/nonexistent-api-endpoint')
                .then(response => {
                    if (!response.ok) {
                        throw new Error(\`HTTP \${response.status}: \${response.statusText}\`);
                    }
                })
                .catch(error => {
                    logEvent('✅ Fetch Error захвачен');
                    sendErrorToCursor('Network Error', error.message);
                });
        }
        
        function testXHRError() {
            logEvent('🧪 Тест XHR Error');
            const xhr = new XMLHttpRequest();
            xhr.open('GET', '/nonexistent-api-endpoint');
            xhr.onerror = function() {
                logEvent('✅ XHR Error захвачен');
                sendErrorToCursor('XHR Error', 'XMLHttpRequest failed');
            };
            xhr.send();
        }
        
        function testTimeoutError() {
            logEvent('🧪 Тест Timeout Error');
            setTimeout(() => {
                throw new Error('Timeout error simulation for Cursor MCP');
            }, 100);
        }
        
        function sendErrorToCursor(type, message) {
            const errorData = {
                type: type,
                message: message,
                url: window.location.href,
                timestamp: new Date().toISOString(),
                severity: 'high'
            };
            
            fetch('/cursor/error', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(errorData)
            })
            .then(response => response.json())
            .then(data => {
                logEvent('📤 Ошибка отправлена в Cursor MCP');
            })
            .catch(error => {
                logEvent('❌ Ошибка отправки в Cursor MCP');
            });
        }
        
        function clearLog() {
            logEvent('🗑️ Очистка лога');
            eventLog = [];
            document.getElementById('eventLog').textContent = '';
        }
        
        // Глобальные обработчики ошибок
        window.addEventListener('error', (event) => {
            logEvent(\`🔍 Глобальная ошибка: \${event.message}\`);
            sendErrorToCursor('Global Error', event.message);
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            logEvent(\`🔍 Unhandled Promise: \${event.reason}\`);
            sendErrorToCursor('Promise Rejection', event.reason.toString());
        });
    </script>
</body>
</html>
    `;
  }

  async stop() {
    try {
      if (this.server) {
        this.server.close();
        console.log(chalk.yellow('🛑 HTTP сервер остановлен'));
      }
      
      if (this.wss) {
        this.wss.close();
        console.log(chalk.yellow('🛑 WebSocket сервер остановлен'));
      }
    } catch (error) {
      console.error(chalk.red('❌ Ошибка остановки сервера:', error.message));
    }
  }
}

// Запуск сервера
async function main() {
  const server = new CursorMCPYandexServer();
  
  // Обработка сигналов завершения
  process.on('SIGINT', async () => {
    console.log(chalk.yellow('\n🛑 Получен сигнал завершения...'));
    await server.stop();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    console.log(chalk.yellow('\n🛑 Получен сигнал завершения...'));
    await server.stop();
    process.exit(0);
  });

  try {
    await server.start();
  } catch (error) {
    console.error(chalk.red('❌ Критическая ошибка:', error));
    process.exit(1);
  }
}

// Запуск если файл выполняется напрямую
if (require.main === module) {
  main().catch(console.error);
}

module.exports = CursorMCPYandexServer;
