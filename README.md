# AgentLite

English | [简体中文](./README_zh.md)

A lightweight AI agent framework with MCP (Model Context Protocol) integration, featuring a modern web interface with real-time streaming chat.

## ✨ Features

### Core Capabilities

- 🤖 **AI Agent Framework** - Powered by DeepSeek Chat with tool-calling support
- 🔌 **MCP Integration** - Connect to multiple MCP servers (filesystem, bash, git)
- 🎯 **Extensible Skills** - Load custom skills from system and user directories
- 💬 **Streaming Chat** - Real-time SSE streaming with typewriter effect
- 🎨 **Modern UI** - Next.js frontend with TailwindCSS and dark theme

### Technical Features

- **Silent Tool Execution** - Tools run in background without interrupting stream
- **Markdown Rendering** - Full GitHub Flavored Markdown with syntax highlighting
- **Performance Logging** - Detailed timing logs for debugging
- **Thinking Animation** - Visual feedback during agent processing

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Poetry (Python package manager)

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd agent-lite
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

# Edit config.yaml and add your DeepSeek API key
# llm:
#   api_key: "your-api-key-here"
```

### Running

**Terminal 1 - Backend:**

```bash
poetry run uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**

```bash
cd web
npm run dev
```

**Access:**

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
agent-lite/
├── core/                    # Core agent logic
│   ├── agent.py            # Main agent with streaming support
│   ├── agent_lite.py       # Agent initialization
│   ├── llm.py              # LLM client wrapper
│   ├── mcp_client.py       # MCP server connection
│   ├── tools.py            # Tool registry
│   ├── skills.py           # Skills loader
│   └── config.py           # Configuration management
├── data/
│   ├── system/             # System resources
│   │   ├── mcp_config.json # MCP server configuration
│   │   ├── mcp_server_*.py # MCP server implementations
│   │   └── skills/         # System skills
│   └── user/               # User-defined resources
│       └── skills/         # User skills
├── web/                    # Next.js frontend
│   ├── app/
│   │   ├── page.tsx        # Chat interface
│   │   ├── skills/         # Skills management
│   │   └── tools/          # Tools management
│   └── lib/
│       └── api.ts          # API client with SSE support
├── api.py                  # FastAPI backend
├── main.py                 # CLI entry point
└── config.yaml             # Configuration file
```

## 🔧 Configuration

### config.yaml

```yaml
llm:
  provider: "deepseek"
  model: "deepseek-chat"
  api_key: "your-api-key"
  base_url: "https://api.deepseek.com"

storage:
  system_skills_path: "./data/system/skills"
  user_skills_path: "./data/user/skills"

mcp_servers_config: "./data/system/mcp_config.json"
```

### MCP Servers

Configure MCP servers in `data/system/mcp_config.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "python",
      "args": ["-u", "./mcp_server_fs.py"]
    },
    "bash": {
      "command": "python",
      "args": ["-u", "./mcp_server_bash.py"]
    },
    "git": {
      "command": "python",
      "args": ["-u", "-m", "mcp_server_git", "--repository", "."]
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
3. Watch the "思考中..." animation while the agent processes
4. See the response stream in real-time with markdown formatting

### CLI

```bash
poetry run python main.py
```

### API

```bash
# Non-streaming
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# Streaming (SSE)
curl -N http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

## 🛠️ Creating Skills

Skills are located in `data/user/skills/`. Each skill is a directory with:

```
my-skill/
├── SKILL.md          # Skill documentation (required)
├── scripts/          # Executable scripts
└── resources/        # Additional resources
```

**SKILL.md format:**

```markdown
---
name: my-skill
description: A brief description
---

# Skill Documentation

Detailed instructions on how to use this skill...
```

## 🎨 Frontend Features

- **Dark Theme** - Sleek slate-900 background with cyan accents
- **Markdown Support** - Headings, code blocks, lists, links
- **Syntax Highlighting** - GitHub Dark theme for code
- **Responsive Design** - Works on desktop and mobile
- **Thinking Indicator** - Brain icon with animated dots

## 📝 License

MIT

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
