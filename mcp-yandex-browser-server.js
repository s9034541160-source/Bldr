#!/usr/bin/env node
/**
 * MCP Server for Yandex Browser Frontend Error Capture
 * Интеграция с Cursor IDE для мониторинга ошибок в Yandex Browser
 */

const express = require('express');
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
const cors = require('cors');
const bodyParser = require('body-parser');
const chalk = require('chalk');
const moment = require('moment');

class YandexBrowserMCPServer {
  constructor() {
    this.app = express();
    this.server = null;
    this.wss = null;
    this.port = process.env.MCP_SERVER_PORT || 3000;
    this.errorLogPath = path.join(__dirname, 'logs', 'yandex-browser-errors.json');
    this.configPath = path.join(__dirname, 'config', 'mcp-config.json');
    
    // Создаем директории если не существуют
    this.ensureDirectories();
    
    // Загружаем конфигурацию
    this.config = this.loadConfig();
    
    // Настройка Express
    this.setupExpress();
    
    // Настройка WebSocket
    this.setupWebSocket();
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

  loadConfig() {
    try {
      if (fs.existsSync(this.configPath)) {
        return JSON.parse(fs.readFileSync(this.configPath, 'utf8'));
      }
    } catch (error) {
      console.warn(chalk.yellow('⚠️ Ошибка загрузки конфигурации:', error.message));
    }
    
    // Конфигурация по умолчанию
    return {
      server: {
        name: 'Yandex Browser MCP Server',
        version: '1.0.0',
        port: this.port,
        browserType: 'yandex'
      },
      errorCapture: {
        enabled: true,
        logLevel: 'error',
        maxLogSize: '10MB',
        retentionDays: 30
      },
      cursor: {
        integration: true,
        autoReport: true,
        reportInterval: 5000
      }
    };
  }

  setupExpress() {
    // Middleware
    this.app.use(cors());
    this.app.use(bodyParser.json());
    this.app.use(bodyParser.urlencoded({ extended: true }));
    
    // Статические файлы
    this.app.use(express.static(__dirname));
    
    // API Routes
    this.app.post('/api/connect', (req, res) => {
      this.handleConnect(req, res);
    });
    
    this.app.post('/api/error', (req, res) => {
      this.handleError(req, res);
    });
    
    this.app.post('/api/errors/batch', (req, res) => {
      this.handleBatchErrors(req, res);
    });
    
    this.app.get('/api/status', (req, res) => {
      this.handleStatus(req, res);
    });
    
    this.app.get('/api/errors', (req, res) => {
      this.handleGetErrors(req, res);
    });
    
    // Главная страница
    this.app.get('/', (req, res) => {
      res.send(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>MCP Yandex Browser Server</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .status { color: #28a745; font-weight: bold; }
            .info { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 10px 0; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>🔧 MCP Yandex Browser Server</h1>
            <p class="status">✅ Сервер запущен и работает</p>
            <div class="info">
              <strong>Порт:</strong> ${this.port}<br>
              <strong>Версия:</strong> ${this.config.server.version}<br>
              <strong>Браузер:</strong> ${this.config.server.browserType}<br>
              <strong>Время запуска:</strong> ${moment().format('YYYY-MM-DD HH:mm:ss')}
            </div>
            <h3>🧪 Тестирование</h3>
            <p><a href="/test-yandex-browser.html" target="_blank">Открыть тестовую страницу</a></p>
            <h3>📊 API Endpoints</h3>
            <ul>
              <li>POST /api/connect - Подключение клиента</li>
              <li>POST /api/error - Отправка ошибки</li>
              <li>POST /api/errors/batch - Пакетная отправка</li>
              <li>GET /api/status - Статус сервера</li>
              <li>GET /api/errors - Получить ошибки</li>
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

  handleConnect(req, res) {
    const { sessionId, browserInfo } = req.body;
    
    console.log(chalk.blue(`🔗 Подключение клиента: ${sessionId}`));
    
    res.json({
      success: true,
      message: 'Подключение установлено',
      serverTime: new Date().toISOString(),
      sessionId: sessionId
    });
  }

  handleError(req, res) {
    const errorData = req.body;
    
    console.log(chalk.yellow(`🔍 Получена ошибка: ${errorData.type} - ${errorData.message}`));
    
    // Сохраняем ошибку
    this.saveErrorLog(errorData);
    
    res.json({
      success: true,
      message: 'Ошибка сохранена',
      timestamp: new Date().toISOString()
    });
  }

  handleBatchErrors(req, res) {
    const { errors } = req.body;
    
    console.log(chalk.blue(`📦 Получено ошибок: ${errors.length}`));
    
    // Сохраняем все ошибки
    errors.forEach(error => this.saveErrorLog(error));
    
    res.json({
      success: true,
      message: `Сохранено ${errors.length} ошибок`,
      timestamp: new Date().toISOString()
    });
  }

  handleStatus(req, res) {
    const status = {
      server: 'running',
      port: this.port,
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      timestamp: new Date().toISOString(),
      config: this.config
    };
    
    res.json(status);
  }

  handleGetErrors(req, res) {
    try {
      let errors = [];
      if (fs.existsSync(this.errorLogPath)) {
        errors = JSON.parse(fs.readFileSync(this.errorLogPath, 'utf8'));
      }
      
      const limit = parseInt(req.query.limit) || 50;
      const recentErrors = errors.slice(-limit);
      
      res.json({
        success: true,
        errors: recentErrors,
        total: errors.length,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  }

  handleWebSocketMessage(ws, data) {
    switch (data.type) {
      case 'ping':
        ws.send(JSON.stringify({ type: 'pong', timestamp: new Date().toISOString() }));
        break;
      case 'error':
        this.saveErrorLog(data.error);
        break;
      default:
        console.log(chalk.blue(`📨 WebSocket сообщение: ${data.type}`));
    }
  }

  saveErrorLog(errorData) {
    try {
      let logs = [];
      if (fs.existsSync(this.errorLogPath)) {
        logs = JSON.parse(fs.readFileSync(this.errorLogPath, 'utf8'));
      }
      
      const enrichedError = {
        ...errorData,
        timestamp: new Date().toISOString(),
        serverTime: moment().format('YYYY-MM-DD HH:mm:ss')
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

  async start() {
    try {
      console.log(chalk.cyan('🚀 Запуск MCP сервера для Yandex Browser...'));
      console.log(chalk.cyan('=' * 50));
      
      // Запуск HTTP сервера
      this.server = this.app.listen(this.port, () => {
        console.log(chalk.green(`✅ HTTP сервер запущен на порту ${this.port}`));
        console.log(chalk.green(`🌐 Откройте: http://localhost:${this.port}`));
      });
      
      console.log(chalk.green(`✅ WebSocket сервер запущен на порту ${this.port + 1}`));
      console.log(chalk.green(`🌐 Браузер: ${this.config.server.browserType}`));
      console.log(chalk.green(`📊 Мониторинг ошибок: ${this.config.errorCapture.enabled ? 'включен' : 'выключен'}`));
      console.log(chalk.green(`🔗 Интеграция с Cursor: ${this.config.cursor.integration ? 'активна' : 'неактивна'}`));
      
      // Периодическая отчетность
      if (this.config.cursor.integration) {
        this.startPeriodicReporting();
      }
      
    } catch (error) {
      console.error(chalk.red('❌ Ошибка запуска MCP сервера:', error));
      throw error;
    }
  }

  startPeriodicReporting() {
    setInterval(() => {
      console.log(chalk.blue(`📈 Периодический отчет: ${new Date().toLocaleTimeString()}`));
    }, this.config.cursor.reportInterval);
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
  const server = new YandexBrowserMCPServer();
  
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

module.exports = YandexBrowserMCPServer;