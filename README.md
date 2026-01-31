# SynapseBot

English | [简体中文](./README_zh.md)

A lightweight, multi-channel AI agent framework with MCP (Model Context Protocol) integration, featuring modern web interface, Slack, and Feishu (Lark) support.

## ✨ Features

### Core Capabilities

- 🤖 **AI Agent Framework** - Powered by any OpenAI-compatible LLM (DeepSeek, OpenAI, Azure OpenAI, Ollama, etc.) with tool-calling support
- 🔌 **MCP Integration** - Connect to multiple MCP servers for extended capabilities
- 🎯 **Extensible Skills** - Load custom skills from system and user directories
- 📡 **Multi-Channel Support** - Web, Slack, and Feishu (Lark) integrations
- 💬 **Real-time Communication** - WebSocket-based streaming for instant responses
- 📁 **File Handling** - Upload and download files across all channels

### Technical Features

- **Event-Driven Architecture** - Centralized event bus for channel communication
- **Async Processing** - Non-blocking agent execution with streaming support
- **Markdown Rendering** - Full GitHub Flavored Markdown with syntax highlighting
- **Internationalization** - Multi-language support (English, Chinese)
- **Terminal Integration** - Built-in web terminal with PTY support

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Poetry (Python package manager)

### Installation

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
# The system supports any OpenAI-compatible API

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

### Running

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

**Access:**

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker Deployment

For production deployment or containerized environments, use Docker:

```bash
# Quick start with setup script
./docker-setup.sh

# Or manually with Docker Compose
docker compose up -d
```

**For detailed build and deployment instructions, see [BUILD.md](./BUILD.md).**

## 📁 Project Structure

```
synapsebot/
├── core/                       # Core agent logic
│   ├── agent.py               # Main agent with streaming support
│   ├── synapse_bot.py         # Agent initialization and lifecycle
│   ├── dispatcher.py          # Tool execution dispatcher
│   ├── eventbus.py            # Event-driven communication
│   ├── llm.py                 # LLM client wrapper
│   ├── mcp_client.py          # MCP server connection
│   ├── tools.py               # Tool registry
│   ├── skills.py              # Skills loader
│   ├── config.py              # Configuration management
│   ├── logger.py              # Logging utilities
│   └── channels/              # Channel integrations
│       ├── base.py            # Base channel interface
│       ├── web/               # Web channel (WebSocket)
│       ├── slack/             # Slack integration
│       └── feishu/            # Feishu (Lark) integration
├── server/                     # FastAPI backend
│   └── main.py                # API routes and WebSocket endpoints
├── cli/                        # Command-line interface
│   └── main.py                # Interactive CLI
├── data/                       # Data storage
│   ├── system/                # System resources
│   │   ├── mcp_config.json    # MCP server configuration
│   │   └── skills/            # System skills
│   ├── user/                  # User-defined resources
│   │   ├── mcp_config.json    # User MCP configuration
│   │   └── skills/            # User skills
│   └── uploads/               # Uploaded files
├── web/                        # Next.js frontend
│   ├── app/                   # Next.js app directory
│   │   └── [locale]/          # Internationalized routes
│   ├── components/            # React components
│   ├── lib/                   # Utilities and API client
│   └── messages/              # i18n translations
├── main.py                     # Main entry point
├── config.yaml                 # Configuration file
└── pyproject.toml             # Python dependencies
```

## 🔧 Configuration

### config.yaml

```yaml
llm:
  vendor: "deepseek" # Any OpenAI-compatible provider
  base_url: "https://api.deepseek.com"
  api_key: "${DEEPSEEK_API_KEY}" # Use env var or direct value
  model: "deepseek-chat"

storage:
  data_path: "./data" # Data storage directory

channels:
  slack:
    enabled: false # Enable Slack integration
    bot_token: "${SLACK_BOT_TOKEN}"
    app_token: "${SLACK_APP_TOKEN}"
  feishu:
    enabled: false # Enable Feishu integration
    app_id: "${FEISHU_APP_ID}"
    app_secret: "${FEISHU_APP_SECRET}"

log_level: "INFO" # Logging level
```

**Supported LLM Providers:**

SynapseBot works with any service that implements the OpenAI Chat Completions API, including:

- **DeepSeek** - `https://api.deepseek.com`
- **OpenAI** - `https://api.openai.com/v1`
- **Azure OpenAI** - `https://your-resource.openai.azure.com`
- **Ollama** (local) - `http://localhost:11434/v1`
- **LM Studio** (local) - `http://localhost:1234/v1`
- **Together AI** - `https://api.together.xyz/v1`
- **Groq** - `https://api.groq.com/openai/v1`
- And many more OpenAI-compatible services

### MCP Servers

Configure MCP servers in `data/user/mcp_config.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/allowed/directory"
      ]
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git", "--repository", "."]
    }
  }
}
```

### External MCP Servers

Discover and connect to more MCP servers from [AgentSkills.io](https://agentskills.io). The platform provides a rich collection of MCP servers, including:

- Database connections (PostgreSQL, MySQL, MongoDB, etc.)
- API integrations (GitHub, Slack, Google, etc.)
- Development tools (Docker, Kubernetes, etc.)
- Data processing tools

Visit [https://agentskills.io](https://agentskills.io) to browse available MCP servers and view integration instructions.

## 💡 Usage

### Web Interface

1. Open http://localhost:3000
2. Type your message in the input box
3. Watch the thinking animation while the agent processes
4. See the response stream in real-time with markdown formatting
5. Upload files by clicking the attachment icon
6. Download generated files directly from the chat

### CLI

```bash
poetry run python main.py cli
```

Interactive command-line interface with rich formatting and streaming support.

### API

```bash
# Health check
curl http://localhost:8000/health

# List skills
curl http://localhost:8000/skills

# List MCP tools
curl http://localhost:8000/mcp/tools

# Upload file
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/file.txt"

# Download file
curl http://localhost:8000/files/{filename}
```

## 🔌 Channel Integrations

### Web Channel

The web channel provides a modern, responsive interface with:

- Real-time WebSocket communication
- File upload and download
- Markdown rendering with syntax highlighting
- Multi-language support (i18n)
- Integrated web terminal

**Configuration:** Enabled by default, no additional setup required.

### Slack Integration

SynapseBot supports real-time interaction via Slack using Socket Mode, allowing for direct messages, channel mentions, and file sharing.

#### Setup Guide

1. **Create a Slack App**
   - Go to [Slack API: Applications](https://api.slack.com/apps)
   - Click "Create New App" and choose "From an app manifest"
   - Select your workspace

2. **Configure Manifest**
   - Copy the contents of `core/channels/slack/manifest.yaml` from this repository
   - Paste it into the YAML editor in Slack
   - Verify the permissions and settings (Socket Mode enabled, Event Subscriptions, etc.)
   - Click "Create"

3. **Install & Tokens**
   - **Install to Workspace**: Go to "Basic Information" and install the app
   - **Bot Token**: Go to "OAuth & Permissions" and copy the `Bot User OAuth Token` (starts with `xoxb-`)
   - **App Token**: Go to "Basic Information" > "App-Level Tokens", create one with `connections:write` scope, and copy it (starts with `xapp-`)

#### Configuration

Add the tokens to your `config.yaml` or use environment variables:

```yaml
channels:
  slack:
    enabled: true
    bot_token: "xoxb-your-token" # OR set env var SLACK_BOT_TOKEN
    app_token: "xapp-your-token" # OR set env var SLACK_APP_TOKEN
```

#### Usage Features

- **Direct Chat**: DM the bot for private assistance
- **Channel Support**: Invite the bot to any channel (`/invite @SynapseBot`) and mention it to trigger a response
- **File Handling**:
  - **Upload to Bot**: Drag and drop files in the chat. The bot automatically downloads and can process them
  - **Download from Bot**: The bot can generate files and send them back to you as valid Slack attachments
- **Real-time Status**: See "Thinking...", "Calling tool..." updates during processing

### Feishu (Lark) Integration

SynapseBot supports real-time interaction via Feishu (Lark) using WebSocket.

#### Setup Guide

1. **Create a Feishu App**
   - Go to [Feishu Open Platform](https://open.feishu.cn/app)
   - Click "Create App" and select "Custom App"
   - Enter your app name and description

2. **Enable Bot Features**
   - Go to "Add Features" > "Bot" and click "Add"
   - Go to "Permissions & Scopes" and add the following permissions:
     - `im:message` (Receive messages)
     - `im:message:send_as_bot` (Send messages)
     - `im:resource` (Upload/Download files)

3. **Get Credentials**
   - Go to "Credentials & Basic Info" and copy `App ID` and `App Secret`

#### Configuration

Add the credentials to your `config.yaml` or use environment variables:

```yaml
channels:
  feishu:
    enabled: true
    app_id: "cli_..." # OR set env var FEISHU_APP_ID
    app_secret: "..." # OR set env var FEISHU_APP_SECRET
```

#### Usage Features

- **Direct Chat**: Send messages directly to the bot
- **Real-time Status**: See "思考中...", "调用工具..." updates during processing
- **File Handling**: Upload and download files seamlessly

## 🎯 Skills System

Skills are modular capabilities that can be loaded into the agent. Each skill is defined by a `SKILL.md` file with YAML frontmatter.

### Skill Structure

```
data/user/skills/my_skill/
├── SKILL.md           # Skill definition with frontmatter
├── examples/          # Example files (optional)
├── scripts/           # Helper scripts (optional)
└── resources/         # Additional resources (optional)
```

### Creating a Skill

Create a `SKILL.md` file with the following format:

```markdown
---
name: My Skill
description: A brief description of what this skill does
---

# Detailed Instructions

Provide detailed instructions on how to use this skill...
```

### Managing Skills

- **Upload**: Use the web interface to upload skill ZIP files
- **List**: View all available skills via API or web interface
- **Delete**: Remove skills via API or web interface
- **Reload**: Skills are automatically reloaded when uploaded or deleted

## 🎨 Frontend Features

- **Modern UI** - Clean, responsive design with dark theme
- **Markdown Support** - Headings, code blocks, lists, links, tables
- **Syntax Highlighting** - GitHub Dark theme for code blocks
- **File Management** - Drag-and-drop upload, inline download links
- **Internationalization** - English and Chinese support
- **Web Terminal** - Integrated xterm.js terminal with PTY support
- **Real-time Updates** - WebSocket-based streaming responses

## 🛠️ Development

### Running Tests

```bash
# Backend tests (if available)
poetry run pytest

# Frontend tests
cd web
npm test
```

### Building for Production

For detailed production deployment instructions, including Docker, reverse proxy configuration, SSL/TLS setup, and monitoring, see **[BUILD.md](./BUILD.md)**.

**Quick production build:**

```bash
# Build frontend
cd web
npm run build
npm start

# Run backend in production mode
poetry run uvicorn server.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Code Style

- **Python**: Follow PEP 8 guidelines
- **TypeScript/React**: Follow ESLint configuration
- **Formatting**: Use consistent indentation and naming conventions

## 📝 License

MIT

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### How to Contribute

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [Next.js](https://nextjs.org/)
- MCP integration via [Model Context Protocol](https://modelcontextprotocol.io/)
- Slack integration via [Slack Bolt](https://slack.dev/bolt-python/)
- Feishu integration via [Lark Open API](https://open.feishu.cn/)
