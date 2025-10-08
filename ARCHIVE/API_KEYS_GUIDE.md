# API Keys and Tokens Guide for Bldr Empire v2

This document lists all the API keys, tokens, and secrets required for the full functionality of the Bldr Empire v2 system.

## Required API Keys and Tokens

### 1. Database Credentials

**Neo4j Database**
- Variable: `NEO4J_PASSWORD`
- Purpose: Authentication for Neo4j graph database
- Default: `bldr` (change in production)

**Qdrant Vector Database**
- Variable: `QDRANT_API_KEY`
- Purpose: Authentication for Qdrant vector database
- Default: `your_qdrant_api_key_here`

### 2. Telegram Bot

**Telegram Bot Token**
- Variable: `TELEGRAM_BOT_TOKEN`
- Purpose: Authentication for Telegram bot integration
- How to get: Create a bot with BotFather on Telegram
- Default: `your_telegram_bot_token_here`

### 3. Google Services

**Google API Key**
- Variable: `GOOGLE_API_KEY`
- Purpose: Access to Google services (Drive, Docs, Sheets)
- How to get: Google Cloud Console API key
- Default: `your_google_api_key_here`

### 4. Security

**FastAPI Secret Key**
- Variable: `SECRET_KEY`
- Purpose: JWT token signing for API authentication
- How to generate: Use a strong random string
- Default: `your_fastapi_secret_key_here`

**Webhook Secret**
- Variable: `WEBHOOK_SECRET`
- Purpose: HMAC signature verification for webhooks
- How to generate: Use a strong random string
- Default: `your_webhook_secret_here`

### 5. Monitoring

**Sentry DSN**
- Variable: `SENTRY_DSN`
- Purpose: Error tracking and monitoring
- How to get: Create a project in Sentry.io
- Default: `your_sentry_dsn_here`

### 6. AI/ML Services

**LLM Base URL**
- Variable: `LLM_BASE_URL`
- Purpose: Connection to local LLM (Ollama, LM Studio, etc.)
- Default: `http://localhost:1234/v1`

## Configuration Files

### .env File Location
The system looks for configuration in:
1. `.env` file in the project root
2. Environment variables set in the system

### Example .env Configuration
```
# Database Configuration
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password_here

# Qdrant Configuration
QDRANT_PATH=data/qdrant_db
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key_here

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Google Services
GOOGLE_API_KEY=your_google_api_key_here

# Security
SECRET_KEY=your_strong_secret_key_here
WEBHOOK_SECRET=your_webhook_secret_here

# Monitoring
SENTRY_DSN=your_sentry_dsn_here

# AI/ML
LLM_BASE_URL=http://localhost:1234/v1
```

## How to Obtain Keys

### Telegram Bot Token
1. Open Telegram
2. Search for @BotFather
3. Send `/newbot` command
4. Follow instructions to create bot
5. Copy the provided token

### Google API Key
1. Go to Google Cloud Console
2. Create a new project or select existing one
3. Enable required APIs (Drive, Docs, Sheets)
4. Go to Credentials
5. Create API Key
6. Restrict the key to your domain/IP

### Sentry DSN
1. Go to sentry.io
2. Create account or log in
3. Create new project
4. Select FastAPI as platform
5. Copy the DSN from the setup instructions

## Security Best Practices

1. **Never commit real keys to version control**
   - Always use `.env` files
   - Add `.env` to `.gitignore`

2. **Use strong, random secrets**
   - Generate 32+ character random strings
   - Use different keys for different environments

3. **Rotate keys regularly**
   - Change passwords and API keys periodically
   - Monitor for unauthorized access

4. **Restrict API key scopes**
   - Only grant necessary permissions
   - Use key restrictions where available

## Testing Configuration

To verify your configuration:
1. Run `python core/bldr_api.py` to test backend
2. Run `python integrations/telegram_bot.py` to test Telegram bot
3. Check Docker logs for any authentication errors

## Troubleshooting

### Common Issues
1. **"Invalid token" errors**: Check that tokens are correctly copied without extra spaces
2. **"Permission denied"**: Verify API key scopes and restrictions
3. **"Connection refused"**: Ensure services are running and ports are correct

### Log Locations
- Backend API logs: Console output when running `python core/bldr_api.py`
- Telegram bot logs: Console output when running `python integrations/telegram_bot.py`
- Docker logs: `docker-compose logs` command