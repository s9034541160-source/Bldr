/**
 * Yandex Browser Client для интеграции с MCP сервером
 * Внедряется в веб-страницы для мониторинга ошибок
 */

class YandexBrowserMCPClient {
  constructor(config = {}) {
    this.config = {
      serverUrl: config.serverUrl || 'http://localhost:3000',
      apiKey: config.apiKey || 'mcp-yandex-browser-key-2024',
      sessionId: this.generateSessionId(),
      browserInfo: this.getBrowserInfo(),
      ...config
    };
    
    this.isConnected = false;
    this.errorQueue = [];
    this.retryCount = 0;
    this.maxRetries = 3;
    
    this.init();
  }

  generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  getBrowserInfo() {
    return {
      userAgent: navigator.userAgent,
      language: navigator.language,
      platform: navigator.platform,
      cookieEnabled: navigator.cookieEnabled,
      onLine: navigator.onLine,
      screen: {
        width: screen.width,
        height: screen.height,
        colorDepth: screen.colorDepth
      },
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      },
      url: window.location.href,
      referrer: document.referrer,
      timestamp: new Date().toISOString()
    };
  }

  init() {
    console.log('🔗 Yandex Browser MCP Client инициализирован');
    
    // Устанавливаем обработчики ошибок
    this.setupErrorHandlers();
    
    // Подключаемся к серверу
    this.connect();
    
    // Периодическая отправка очереди ошибок
    setInterval(() => {
      this.flushErrorQueue();
    }, 5000);
  }

  setupErrorHandlers() {
    // Глобальные ошибки JavaScript
    window.addEventListener('error', (event) => {
      this.captureError({
        type: 'JavaScript Error',
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error ? event.error.stack : '',
        url: window.location.href
      });
    });

    // Ошибки промисов
    window.addEventListener('unhandledrejection', (event) => {
      this.captureError({
        type: 'Unhandled Promise Rejection',
        message: event.reason ? event.reason.toString() : 'Unknown promise rejection',
        stack: event.reason ? event.reason.stack : '',
        url: window.location.href
      });
    });

    // Ошибки ресурсов (изображения, скрипты, стили)
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        this.captureError({
          type: 'Resource Error',
          message: `Failed to load resource: ${event.target.src || event.target.href}`,
          element: event.target.tagName,
          src: event.target.src || event.target.href,
          url: window.location.href
        });
      }
    }, true);

    // Ошибки сети
    this.setupNetworkErrorHandling();
  }

  setupNetworkErrorHandling() {
    // Перехватываем fetch запросы
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      try {
        const response = await originalFetch(...args);
        if (!response.ok) {
          this.captureError({
            type: 'Network Error',
            message: `HTTP ${response.status}: ${response.statusText}`,
            url: args[0],
            status: response.status,
            statusText: response.statusText
          });
        }
        return response;
      } catch (error) {
        this.captureError({
          type: 'Network Error',
          message: error.message,
          url: args[0],
          stack: error.stack
        });
        throw error;
      }
    };

    // Перехватываем XMLHttpRequest
    const originalXHR = window.XMLHttpRequest;
    window.XMLHttpRequest = function() {
      const xhr = new originalXHR();
      const originalOpen = xhr.open;
      const originalSend = xhr.send;

      xhr.open = function(method, url, ...args) {
        this._method = method;
        this._url = url;
        return originalOpen.apply(this, [method, url, ...args]);
      };

      xhr.send = function(...args) {
        this.addEventListener('error', () => {
          this.captureError({
            type: 'XHR Error',
            message: 'XMLHttpRequest failed',
            url: this._url,
            method: this._method,
            status: this.status
          });
        });

        this.addEventListener('load', () => {
          if (this.status >= 400) {
            this.captureError({
              type: 'XHR Error',
              message: `HTTP ${this.status}: ${this.statusText}`,
              url: this._url,
              method: this._method,
              status: this.status,
              statusText: this.statusText
            });
          }
        });

        return originalSend.apply(this, args);
      };

      return xhr;
    };
  }

  captureError(errorData) {
    const enrichedError = {
      ...errorData,
      sessionId: this.config.sessionId,
      browserInfo: this.config.browserInfo,
      timestamp: new Date().toISOString(),
      severity: this.calculateSeverity(errorData)
    };

    // Добавляем в очередь
    this.errorQueue.push(enrichedError);
    
    console.log('🔍 Ошибка захвачена:', enrichedError.type, enrichedError.message);
    
    // Пытаемся отправить немедленно
    this.sendError(enrichedError);
  }

  calculateSeverity(errorData) {
    if (errorData.type === 'JavaScript Error' && 
        (errorData.message.includes('ReferenceError') || 
         errorData.message.includes('TypeError'))) {
      return 'high';
    }
    
    if (errorData.type === 'Network Error' && 
        errorData.status >= 500) {
      return 'high';
    }
    
    if (errorData.type === 'Resource Error') {
      return 'medium';
    }
    
    return 'low';
  }

  async connect() {
    try {
      const response = await fetch(`${this.config.serverUrl}/api/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.apiKey}`
        },
        body: JSON.stringify({
          sessionId: this.config.sessionId,
          browserInfo: this.config.browserInfo
        })
      });

      if (response.ok) {
        this.isConnected = true;
        this.retryCount = 0;
        console.log('✅ Подключение к MCP серверу установлено');
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.warn('⚠️ Ошибка подключения к MCP серверу:', error.message);
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    if (this.retryCount < this.maxRetries) {
      this.retryCount++;
      const delay = Math.pow(2, this.retryCount) * 1000; // Экспоненциальная задержка
      
      setTimeout(() => {
        console.log(`🔄 Попытка переподключения ${this.retryCount}/${this.maxRetries}`);
        this.connect();
      }, delay);
    } else {
      console.error('❌ Максимальное количество попыток переподключения исчерпано');
    }
  }

  async sendError(errorData) {
    if (!this.isConnected) {
      return; // Ошибка будет отправлена при переподключении
    }

    try {
      const response = await fetch(`${this.config.serverUrl}/api/error`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.apiKey}`
        },
        body: JSON.stringify(errorData)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      console.log('📤 Ошибка отправлена на сервер');
    } catch (error) {
      console.warn('⚠️ Ошибка отправки на сервер:', error.message);
      this.isConnected = false;
      this.scheduleReconnect();
    }
  }

  async flushErrorQueue() {
    if (this.errorQueue.length === 0 || !this.isConnected) {
      return;
    }

    const errors = [...this.errorQueue];
    this.errorQueue = [];

    try {
      const response = await fetch(`${this.config.serverUrl}/api/errors/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.apiKey}`
        },
        body: JSON.stringify({ errors })
      });

      if (response.ok) {
        console.log(`📤 Отправлено ${errors.length} ошибок из очереди`);
      } else {
        // Возвращаем ошибки в очередь
        this.errorQueue.unshift(...errors);
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.warn('⚠️ Ошибка отправки очереди:', error.message);
      this.errorQueue.unshift(...errors);
      this.isConnected = false;
      this.scheduleReconnect();
    }
  }

  // Публичные методы для внешнего использования
  getSessionInfo() {
    return {
      sessionId: this.config.sessionId,
      isConnected: this.isConnected,
      errorQueueLength: this.errorQueue.length,
      browserInfo: this.config.browserInfo
    };
  }

  disconnect() {
    this.isConnected = false;
    console.log('🔌 Отключение от MCP сервера');
  }
}

// Автоматическая инициализация если скрипт загружен в браузере
if (typeof window !== 'undefined') {
  // Создаем глобальный экземпляр
  window.YandexBrowserMCP = new YandexBrowserMCPClient();
  
  // Экспортируем для использования в модулях
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = YandexBrowserMCPClient;
  }
}

// Экспорт для Node.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = YandexBrowserMCPClient;
}
