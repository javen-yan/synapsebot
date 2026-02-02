# SynapseBot Build & Deployment Guide

This guide covers building, deploying, and running SynapseBot in various environments.

## Table of Contents

- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

## Local Development

### Prerequisites

- Python 3.10+
- Node.js 18+
- Poetry (Python package manager)

### Setup

1. **Clone the repository**

```bash
git clone <repository-url>
cd synapsebot
```

2. **Install Python dependencies**

```bash
poetry install
```

3. **Install frontend dependencies**

```bash
cd web
npm install
cd ..
```

4. **Configure environment**

```bash
# Copy example config
cp config.example.yaml config.yaml

# Edit config.yaml and add your API key
# SynapseBot supports any OpenAI-compatible API

# Example 1: DeepSeek
# llm:
#   vendor: "deepseek"
#   base_url: "https://api.deepseek.com"
#   api_key: "your-api-key-here"
#   model: "deepseek-chat"

# Example 2: OpenAI
# llm:
#   vendor: "openai"
#   base_url: "https://api.openai.com/v1"
#   api_key: "your-api-key-here"
#   model: "gpt-4"

# Example 3: Ollama (local)
# llm:
#   vendor: "ollama"
#   base_url: "http://localhost:11434/v1"
#   api_key: "dummy"
#   model: "llama2"
```

### Running Locally

**Option 1: Using the main entry point (Recommended)**

```bash
# Start the server
poetry run python main.py server --host 0.0.0.0 --port 8000

# Or with auto-reload for development
poetry run python main.py server --reload

# Start CLI mode
poetry run python main.py cli
```

**Option 2: Separate terminals**

Terminal 1 - Backend:

```bash
poetry run uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 - Frontend:

```bash
cd web
npm run dev
```

### Development Workflow

1. **Backend changes**: The server will auto-reload if you use `--reload` flag
2. **Frontend changes**: Next.js dev server has hot module replacement
3. **Configuration changes**: Restart the server to apply changes
4. **Skill changes**: Use the API or web interface to reload skills

## Docker Deployment

### Quick Start

The easiest way to deploy SynapseBot with Docker is using the provided setup script:

```bash
# Make the script executable
chmod +x docker-setup.sh

# Run the setup script
./docker-setup.sh
```

This script will:

1. Build the Docker image
2. Create necessary directories
3. Set up the `.env` file
4. Display usage instructions

### Manual Docker Build

If you prefer to build manually:

```bash
# Build the image
docker build -t synapsebot:local .

# Run the server
docker run -d \
  --name synapsebot-server \
  -p 8000:8000 \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/data:/app/data \
  -e DEEPSEEK_API_KEY=your-api-key \
  synapsebot:local
```

### Docker Compose

The recommended way to run SynapseBot with Docker is using Docker Compose:

1. **Configure environment variables**

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

2. **Start all services**

```bash
# Start backend and frontend
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

3. **Run CLI**

```bash
# Interactive CLI session
docker compose run --rm synapsebot-cli
```

### Docker Compose Services

The `docker-compose.yml` defines three services:

- **synapsebot-server**: Backend API server (port 8000)
- **synapsebot-web**: Frontend web interface (port 3000)
- **synapsebot-cli**: Interactive CLI (run with `docker compose run`)

### Volume Management

Docker Compose uses volumes to persist data:

- `synapsebot-home`: User home directory
- `./config.yaml`: Configuration file (read-only)
- `./data`: Data directory (skills, uploads, MCP config) - for Docker volumes

**Note:** The default data directory for non-Docker deployments is `~/.synapsebot`.

## Production Deployment

### Building for Production

1. **Build the frontend**

```bash
cd web
npm run build
cd ..
```

2. **Run the backend in production mode**

```bash
poetry run uvicorn server.main:app --host 0.0.0.0 --port 8000 --workers 4
```

3. **Serve the frontend**

```bash
cd web
npm start
```

### Docker Production Deployment

For production, use Docker Compose with additional configuration:

1. **Create a production docker-compose override**

Create `docker-compose.prod.yml`:

```yaml
services:
  synapsebot-server:
    restart: always
    environment:
      LOG_LEVEL: WARNING
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 4G
        reservations:
          cpus: "1"
          memory: 2G

  synapsebot-web:
    restart: always
    deploy:
      resources:
        limits:
          cpus: "1"
          memory: 2G
        reservations:
          cpus: "0.5"
          memory: 1G
```

2. **Deploy with both compose files**

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Reverse Proxy Configuration

For production, use a reverse proxy like Nginx or Caddy:

**Nginx example:**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

**Caddy example:**

```
your-domain.com {
    reverse_proxy /api/* localhost:8000
    reverse_proxy /ws/* localhost:8000
    reverse_proxy localhost:3000
}
```

### SSL/TLS Configuration

For production, always use HTTPS:

**With Caddy (automatic HTTPS):**

```
your-domain.com {
    reverse_proxy localhost:3000
}
```

**With Nginx + Certbot:**

```bash
sudo certbot --nginx -d your-domain.com
```

## Environment Variables

### Required Variables

| Variable                               | Description                                  | Example  |
| -------------------------------------- | -------------------------------------------- | -------- |
| `DEEPSEEK_API_KEY` or `OPENAI_API_KEY` | LLM API key (any OpenAI-compatible provider) | `sk-...` |

**Note:** The variable name depends on your configuration in `config.yaml`. You can use any name (e.g., `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, `AZURE_API_KEY`) as long as it matches the `api_key` field in your config.

### Optional Variables

| Variable                | Description         | Default                                     |
| ----------------------- | ------------------- | ------------------------------------------- |
| `SLACK_BOT_TOKEN`       | Slack bot token     | -                                           |
| `SLACK_APP_TOKEN`       | Slack app token     | -                                           |
| `FEISHU_APP_ID`         | Feishu app ID       | -                                           |
| `FEISHU_APP_SECRET`     | Feishu app secret   | -                                           |
| `SYNAPSEBOT_API_PORT`   | API server port     | `8000`                                      |
| `SYNAPSEBOT_WEB_PORT`   | Web frontend port   | `3000`                                      |
| `SYNAPSEBOT_CONFIG_DIR` | Config file path    | `./config.yaml`                             |
| `SYNAPSEBOT_DATA_DIR`   | Data directory path | `./data` (Docker) / `~/.synapsebot` (local) |
| `LOG_LEVEL`             | Logging level       | `INFO`                                      |

### Setting Environment Variables

**For local development:**

```bash
export DEEPSEEK_API_KEY=your-api-key
```

**For Docker:**

```bash
# In .env file
DEEPSEEK_API_KEY=your-api-key
```

**For Docker Compose:**

```yaml
# In docker-compose.yml
environment:
  DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY}
```

## Troubleshooting

### Common Issues

#### 1. Docker build fails

**Problem:** Frontend build fails during Docker build

**Solution:**

```bash
# Build frontend locally first to check for errors
cd web
npm run build

# If successful, rebuild Docker image
docker build --no-cache -t synapsebot:local .
```

#### 2. Permission denied errors

**Problem:** Container can't write to mounted volumes

**Solution:**

```bash
# Fix permissions on data directory
chmod -R 755 ./data
chown -R 1000:1000 ./data
```

#### 3. API connection refused

**Problem:** Frontend can't connect to backend

**Solution:**

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check Docker network
docker compose ps
docker compose logs synapsebot-server

# Verify NEXT_PUBLIC_API_URL in .env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### 4. MCP servers not connecting

**Problem:** MCP tools not available

**Solution:**

```bash
# Check MCP configuration
cat data/user/mcp_config.json

# Reload MCP servers via API
curl -X POST http://localhost:8000/mcp/reload

# Check logs for MCP errors
docker compose logs synapsebot-server | grep -i mcp
```

#### 5. Out of memory errors

**Problem:** Container crashes with OOM

**Solution:**

```bash
# Increase Docker memory limit
docker compose down
# Edit docker-compose.yml and add:
# deploy:
#   resources:
#     limits:
#       memory: 4G
docker compose up -d
```

### Health Checks

**Check backend health:**

```bash
curl http://localhost:8000/health
```

**Check Docker container health:**

```bash
docker compose ps
docker inspect synapsebot-server | grep -A 10 Health
```

**View logs:**

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f synapsebot-server

# Last 100 lines
docker compose logs --tail=100 synapsebot-server
```

### Performance Tuning

**Backend workers:**

```bash
# Increase number of workers for production
poetry run uvicorn server.main:app --workers 4
```

**Docker resource limits:**

```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      cpus: "2"
      memory: 4G
```

**Frontend optimization:**

```bash
# Build with production optimizations
cd web
NODE_ENV=production npm run build
```

## Monitoring

### Logs

**View real-time logs:**

```bash
docker compose logs -f
```

**Export logs:**

```bash
docker compose logs > synapsebot.log
```

### Metrics

**Container stats:**

```bash
docker stats synapsebot-server synapsebot-web
```

**API metrics:**

```bash
# Access FastAPI metrics
curl http://localhost:8000/docs
```

## Backup and Restore

### Backup

```bash
# Backup data directory
tar -czf synapsebot-backup-$(date +%Y%m%d).tar.gz data/

# Backup Docker volumes
docker run --rm -v synapsebot_synapsebot-home:/data -v $(pwd):/backup \
  alpine tar -czf /backup/volume-backup-$(date +%Y%m%d).tar.gz /data
```

### Restore

```bash
# Restore data directory
tar -xzf synapsebot-backup-20260131.tar.gz

# Restore Docker volume
docker run --rm -v synapsebot_synapsebot-home:/data -v $(pwd):/backup \
  alpine tar -xzf /backup/volume-backup-20260131.tar.gz -C /
```

## Security Best Practices

1. **Never commit secrets**: Use `.env` files and keep them out of version control
2. **Use non-root user**: The Docker image runs as user `synapsebot` (uid 1000)
3. **Limit network exposure**: Use reverse proxy and firewall rules
4. **Regular updates**: Keep dependencies up to date
5. **Secure API keys**: Rotate keys regularly and use environment variables
6. **Enable HTTPS**: Always use SSL/TLS in production
7. **Monitor logs**: Watch for suspicious activity

## Additional Resources

- [README.md](./README.md) - Project overview and features
- [README_zh.md](./README_zh.md) - Chinese documentation
- [config.example.yaml](./config.example.yaml) - Configuration reference
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
