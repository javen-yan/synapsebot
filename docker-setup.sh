#!/usr/bin/env bash
set -euo pipefail

# SynapseBot Docker Setup Script
# This script builds the Docker image and sets up the environment for running SynapseBot

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
IMAGE_NAME="${SYNAPSEBOT_IMAGE:-synapsebot:local}"
ENV_FILE="$ROOT_DIR/.env"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}==>${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}Warning:${NC} $1"
}

log_error() {
    echo -e "${RED}Error:${NC} $1" >&2
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        log_error "Missing dependency: $1"
        exit 1
    fi
}

# Check dependencies
require_cmd docker
if ! docker compose version >/dev/null 2>&1; then
    log_error "Docker Compose not available (try: docker compose version)"
    exit 1
fi

# Set default directories
SYNAPSEBOT_CONFIG_DIR="${SYNAPSEBOT_CONFIG_DIR:-$ROOT_DIR/config.yaml}"
SYNAPSEBOT_DATA_DIR="${SYNAPSEBOT_DATA_DIR:-$ROOT_DIR/data}"
SYNAPSEBOT_API_PORT="${SYNAPSEBOT_API_PORT:-8000}"
SYNAPSEBOT_WEB_PORT="${SYNAPSEBOT_WEB_PORT:-3000}"

# Create data directories if they don't exist
mkdir -p "$SYNAPSEBOT_DATA_DIR"/{system,user}/{skills,}
mkdir -p "$SYNAPSEBOT_DATA_DIR/uploads"

# Create MCP config files if they don't exist
if [[ ! -f "$SYNAPSEBOT_DATA_DIR/system/mcp_config.json" ]]; then
    echo '{"mcpServers": {}}' > "$SYNAPSEBOT_DATA_DIR/system/mcp_config.json"
fi
if [[ ! -f "$SYNAPSEBOT_DATA_DIR/user/mcp_config.json" ]]; then
    echo '{"mcpServers": {}}' > "$SYNAPSEBOT_DATA_DIR/user/mcp_config.json"
fi

# Check if config.yaml exists
if [[ ! -f "$SYNAPSEBOT_CONFIG_DIR" ]]; then
    if [[ -f "$ROOT_DIR/config.example.yaml" ]]; then
        log_warn "config.yaml not found, copying from config.example.yaml"
        cp "$ROOT_DIR/config.example.yaml" "$SYNAPSEBOT_CONFIG_DIR"
    else
        log_error "config.yaml not found and config.example.yaml doesn't exist"
        exit 1
    fi
fi

# Export environment variables
export SYNAPSEBOT_CONFIG_DIR
export SYNAPSEBOT_DATA_DIR
export SYNAPSEBOT_API_PORT
export SYNAPSEBOT_WEB_PORT
export SYNAPSEBOT_IMAGE="$IMAGE_NAME"

# Function to update or insert environment variables
upsert_env() {
    local file="$1"
    shift
    local -a keys=("$@")
    local tmp
    tmp="$(mktemp)"
    declare -A seen=()

    if [[ -f "$file" ]]; then
        while IFS= read -r line || [[ -n "$line" ]]; then
            # Skip comments and empty lines
            if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]]; then
                printf '%s\n' "$line" >>"$tmp"
                continue
            fi
            
            local key="${line%%=*}"
            local replaced=false
            for k in "${keys[@]}"; do
                if [[ "$key" == "$k" ]]; then
                    printf '%s=%s\n' "$k" "${!k-}" >>"$tmp"
                    seen["$k"]=1
                    replaced=true
                    break
                fi
            done
            if [[ "$replaced" == false ]]; then
                printf '%s\n' "$line" >>"$tmp"
            fi
        done <"$file"
    fi

    for k in "${keys[@]}"; do
        if [[ -z "${seen[$k]:-}" ]]; then
            printf '%s=%s\n' "$k" "${!k-}" >>"$tmp"
        fi
    done

    mv "$tmp" "$file"
}

# Create or update .env file
log_info "Updating .env file"
upsert_env "$ENV_FILE" \
    SYNAPSEBOT_CONFIG_DIR \
    SYNAPSEBOT_DATA_DIR \
    SYNAPSEBOT_API_PORT \
    SYNAPSEBOT_WEB_PORT \
    SYNAPSEBOT_IMAGE

# Check for API key
if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
    log_warn "DEEPSEEK_API_KEY not set in environment"
    log_warn "Please set it in .env file or export it before running docker compose"
fi

# Build Docker image
log_info "Building Docker image: $IMAGE_NAME"
docker build \
    -t "$IMAGE_NAME" \
    -f "$ROOT_DIR/Dockerfile" \
    "$ROOT_DIR"

log_info "Docker image built successfully"

# Display usage information
echo ""
log_info "Setup complete!"
echo ""
echo "Configuration:"
echo "  Config file: $SYNAPSEBOT_CONFIG_DIR"
echo "  Data directory: $SYNAPSEBOT_DATA_DIR"
echo "  API port: $SYNAPSEBOT_API_PORT"
echo "  Web port: $SYNAPSEBOT_WEB_PORT"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your API keys in .env file:"
echo "   export DEEPSEEK_API_KEY='your-api-key-here'"
echo "   # Optional: SLACK_BOT_TOKEN, SLACK_APP_TOKEN, FEISHU_APP_ID, FEISHU_APP_SECRET"
echo ""
echo "2. Start the services:"
echo "   docker compose up -d"
echo ""
echo "3. View logs:"
echo "   docker compose logs -f synapsebot-server"
echo "   docker compose logs -f synapsebot-web"
echo ""
echo "4. Access the application:"
echo "   Web UI: http://localhost:$SYNAPSEBOT_WEB_PORT"
echo "   API: http://localhost:$SYNAPSEBOT_API_PORT"
echo "   API Docs: http://localhost:$SYNAPSEBOT_API_PORT/docs"
echo ""
echo "5. Run CLI (interactive):"
echo "   docker compose run --rm synapsebot-cli"
echo ""
echo "6. Stop the services:"
echo "   docker compose down"
echo ""
echo "For more information, see BUILD.md"
