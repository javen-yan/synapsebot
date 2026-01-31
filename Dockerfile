# Multi-stage build for SynapseBot
FROM node:20-bookworm AS frontend-builder

WORKDIR /app/web

# Copy frontend package files
COPY web/package*.json ./
RUN npm ci

# Copy frontend source
COPY web/ ./

# Build frontend
RUN npm run build

# Main application image
FROM python:3.12-slim-bookworm

# Install system dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Install Node.js for frontend serving
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

# Copy Python dependency files
COPY pyproject.toml poetry.lock ./

# Install Python dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root --only main

# Copy application code
COPY . .

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/web/.next ./web/.next
COPY --from=frontend-builder /app/web/node_modules ./web/node_modules

# Create data directories
RUN mkdir -p /app/data/system/skills \
    /app/data/user/skills \
    /app/data/uploads && \
    echo '{"mcpServers": {}}' > /app/data/system/mcp_config.json && \
    echo '{"mcpServers": {}}' > /app/data/user/mcp_config.json

# Security hardening: Create non-root user
RUN useradd -m -u 1000 synapsebot && \
    chown -R synapsebot:synapsebot /app

USER synapsebot

# Expose ports
EXPOSE 8000 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden)
CMD ["python", "main.py", "server", "--host", "0.0.0.0", "--port", "8000"]
