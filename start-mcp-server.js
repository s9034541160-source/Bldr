// MCP Server for Yandex Browser Frontend Error Capture
const { createServer } = require('@modelcontextprotocol/server');

async function main() {
  const server = createServer({
    name: 'Yandex Browser MCP Server',
    version: '1.0.0',
    port: process.env.MCP_SERVER_PORT || 3000,
    browserType: process.env.BROWSER_TYPE || 'yandex'
  });

  server.on('error', (error) => {
    console.error('MCP Server Error:', error);
  });

  server.on('frontendError', (errorData) => {
    console.log('Frontend Error Captured:', errorData);
    // Здесь можно добавить логику для обработки ошибок
    // Например, отправка в систему мониторинга или сохранение в файл
  });

  await server.start();
  console.log('MCP Server started on port', process.env.MCP_SERVER_PORT || 3000);
}

main().catch(console.error);