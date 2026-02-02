# SynapseBot

[English](./README.md) | 简体中文

一个轻量级、多渠道的 AI Agent 框架，集成 MCP（模型上下文协议），支持现代化 Web 界面、Slack 和飞书。

## ✨ 特性

### 核心功能

- 🤖 **AI Agent 框架** - 支持任何兼容 OpenAI API 的 LLM（DeepSeek、OpenAI、Azure OpenAI、Ollama 等），具备工具调用能力
- 🔌 **MCP 集成** - 连接多个 MCP 服务器以扩展功能
- 🎯 **可扩展技能** - 从系统和用户目录加载自定义技能
- 📡 **多渠道支持** - Web、Slack 和飞书集成
- 💬 **实时通信** - 基于 WebSocket 的流式传输，即时响应
- 📁 **文件处理** - 跨所有渠道上传和下载文件
- ⏰ **定时任务** - 原生支持 Cron 作业、重复任务以及基于自然语言的延时提醒

### 技术特性

- **事件驱动架构** - 集中式事件总线用于渠道通信
- **异步处理** - 非阻塞的 Agent 执行，支持流式传输
- **Markdown 渲染** - 完整的 GitHub Flavored Markdown 和代码高亮
- **国际化** - 多语言支持（英文、中文）
- **终端集成** - 内置 Web 终端，支持 PTY

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Poetry（Python 包管理器）

### 安装

1. **克隆仓库**

```bash
git clone <repository-url>
cd synapsebot
```

2. **安装 Python 依赖**

```bash
poetry install
```

3. **安装前端依赖**

```bash
cd web
npm install
cd ..
```

4. **配置环境**

```bash
# 复制示例配置
cp config.example.yaml config.yaml

# 编辑 config.yaml 并设置你的 LLM 配置
# 系统支持任何兼容 OpenAI API 的服务

# 示例 1：使用配置文件
# llm:
#   base_url: "https://api.openai.com/v1"
#   api_key: "sk-your-api-key-here"
#   model: "gpt-4"

# 示例 2：使用环境变量（推荐）
# llm:
#   base_url: "${LLM_BASE_URL}"
#   api_key: "${LLM_API_KEY}"
#   model: "${LLM_MODEL}"

# 然后设置环境变量：
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_API_KEY="sk-your-api-key-here"
export LLM_MODEL="gpt-4"
```

### 运行

**方式 1：使用主入口（推荐）**

```bash
# 启动服务器
poetry run python main.py server --host 0.0.0.0 --port 8000

# 或者开启自动重载用于开发
poetry run python main.py server --reload

# 启动 CLI 模式
poetry run python main.py cli
```

**方式 2：分别启动**

终端 1 - 后端：

```bash
poetry run uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

终端 2 - 前端：

```bash
cd web
npm run dev
```

**访问：**

- 前端：http://localhost:3000
- API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### Docker 部署

对于生产环境部署或容器化环境，使用 Docker：

```bash
# 使用设置脚本快速开始
./docker-setup.sh

# 或者手动使用 Docker Compose
docker compose up -d
```

**详细的构建和部署说明，请参阅 [BUILD.md](./BUILD.md)。**

## 📁 项目结构

```
synapsebot/
├── core/                       # 核心 Agent 逻辑
│   ├── agent.py               # 主 Agent，支持流式传输
│   ├── synapse_bot.py         # Agent 初始化和生命周期
│   ├── dispatcher.py          # 工具执行调度器
│   ├── eventbus.py            # 事件驱动通信
│   ├── llm.py                 # LLM 客户端封装
│   ├── mcp_client.py          # MCP 服务器连接
│   ├── tools.py               # 工具注册表
│   ├── skills.py              # 技能加载器
│   ├── config.py              # 配置管理
│   ├── logger.py              # 日志工具
│   └── channels/              # 渠道集成
│       ├── base.py            # 基础渠道接口
│       ├── web/               # Web 渠道（WebSocket）
│       ├── slack/             # Slack 集成
│       └── feishu/            # 飞书集成
├── server/                     # FastAPI 后端
│   └── main.py                # API 路由和 WebSocket 端点
├── cli/                        # 命令行界面
│   └── main.py                # 交互式 CLI
├── data/                       # 数据存储
│   ├── system/                # 系统资源
│   │   ├── mcp_config.json    # MCP 服务器配置
│   │   └── skills/            # 系统技能
│   ├── user/                  # 用户自定义资源
│   │   ├── mcp_config.json    # 用户 MCP 配置
│   │   └── skills/            # 用户技能
│   └── uploads/               # 上传的文件
├── web/                        # Next.js 前端
│   ├── app/                   # Next.js 应用目录
│   │   └── [locale]/          # 国际化路由
│   ├── components/            # React 组件
│   ├── lib/                   # 工具和 API 客户端
│   └── messages/              # i18n 翻译
├── main.py                     # 主入口
├── config.yaml                 # 配置文件
└── pyproject.toml             # Python 依赖
```

## 🔧 配置

### config.yaml

```yaml
llm:
  base_url: "https://api.openai.com/v1" # 任何兼容 OpenAI 的 API
  api_key: "${LLM_API_KEY}" # 使用环境变量（推荐）
  model: "gpt-4" # 模型名称

storage:
  data_path: "~/.synapsebot" # 数据存储目录

channels:
  slack:
    enabled: false # 启用 Slack 集成
    bot_token: "${SLACK_BOT_TOKEN}"
    app_token: "${SLACK_APP_TOKEN}"
  feishu:
    enabled: false # 启用飞书集成
    app_id: "${FEISHU_APP_ID}"
    app_secret: "${FEISHU_APP_SECRET}"

log_level: "INFO" # 日志级别
```

**环境变量：**

为 LLM 配置设置这些环境变量：

```bash
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_API_KEY="sk-your-api-key-here"
export LLM_MODEL="gpt-4"
```

**支持的 LLM 提供商：**

SynapseBot 可以与任何实现 OpenAI Chat Completions API 的服务配合使用，包括：

- **DeepSeek** - `https://api.deepseek.com`
- **OpenAI** - `https://api.openai.com/v1`
- **Azure OpenAI** - `https://your-resource.openai.azure.com`
- **Ollama**（本地）- `http://localhost:11434/v1`
- **LM Studio**（本地）- `http://localhost:1234/v1`
- **Together AI** - `https://api.together.xyz/v1`
- **Groq** - `https://api.groq.com/openai/v1`
- 以及更多兼容 OpenAI 的服务

### MCP 服务器

在 `data/user/mcp_config.json` 中配置 MCP 服务器：

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

### 外部 MCP 服务器

你可以从 [AgentSkills.io](https://agentskills.io) 发现和连接更多 MCP 服务器。该平台提供了丰富的 MCP 服务器集合，包括：

- 数据库连接（PostgreSQL、MySQL、MongoDB 等）
- API 集成（GitHub、Slack、Google 等）
- 开发工具（Docker、Kubernetes 等）
- 数据处理工具

访问 [https://agentskills.io](https://agentskills.io) 浏览可用的 MCP 服务器并查看集成说明。

## 💡 使用方法

### Web 界面

1. 打开 http://localhost:3000
2. 在输入框中输入你的消息
3. 观察思考动画，等待 Agent 处理
4. 实时查看带有 Markdown 格式的流式响应
5. 点击附件图标上传文件
6. 直接从聊天中下载生成的文件

### 命令行

```bash
poetry run python main.py cli
```

交互式命令行界面，支持丰富格式和流式传输。

### API

```bash
# 健康检查
curl http://localhost:8000/health

# 列出技能
curl http://localhost:8000/skills

# 列出 MCP 工具
curl http://localhost:8000/mcp/tools

# 上传文件
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/file.txt"

# 下载文件
curl http://localhost:8000/files/{filename}
```

### 定时任务

您可以使用自然语言要求 Agent 安排任务：

- "10 分钟后提醒我休息"
- "每小时检查一次服务器状态"
- "每天上午 9 点发送每日报告"

Agent 将使用内部的 Cron 服务自动管理这些任务。

## 🔌 渠道集成

### Web 渠道

Web 渠道提供现代化、响应式的界面，具有：

- 实时 WebSocket 通信
- 文件上传和下载
- Markdown 渲染和代码高亮
- 多语言支持（i18n）
- 集成 Web 终端

**配置：** 默认启用，无需额外设置。

### Slack 集成

SynapseBot 支持通过 Socket Mode 与 Slack 进行实时交互，支持私信、频道提及和文件共享。

#### 设置指南

1. **创建 Slack 应用**
   - 前往 [Slack API: Applications](https://api.slack.com/apps)
   - 点击 "Create New App" 并选择 "From an app manifest"
   - 选择你的工作区

2. **配置 Manifest**
   - 复制本仓库中 `core/channels/slack/manifest.yaml` 的内容
   - 将其粘贴到 Slack 的 YAML 编辑器中
   - 确认权限和设置（已启用 Socket Mode、事件订阅等）
   - 点击 "Create"

3. **安装与令牌**
   - **安装到工作区**：前往 "Basic Information" 并安装应用
   - **Bot Token**：前往 "OAuth & Permissions" 并复制 `Bot User OAuth Token`（以 `xoxb-` 开头）
   - **App Token**：前往 "Basic Information" > "App-Level Tokens"，创建一个具有 `connections:write` 权限的 token 并复制（以 `xapp-` 开头）

#### 配置

将令牌添加到您的 `config.yaml` 或使用环境变量：

```yaml
channels:
  slack:
    enabled: true
    bot_token: "xoxb-your-token" # 或者设置环境变量 SLACK_BOT_TOKEN
    app_token: "xapp-your-token" # 或者设置环境变量 SLACK_APP_TOKEN
```

#### 使用功能

- **直接聊天**：私信机器人获取私人助手支持
- **频道支持**：将机器人邀请到任何频道（`/invite @SynapseBot`）并提及它以触发响应
- **文件处理**：
  - **上传给机器人**：在聊天中拖放文件。机器人会自动下载并处理它们
  - **从机器人下载**：机器人可以生成文件并作为有效的 Slack 附件发送回给您
- **实时状态**：在处理过程中查看 "Thinking..."、"Calling tool..." 更新

### 飞书集成

SynapseBot 支持通过 WebSocket 与飞书进行实时交互。

#### 设置指南

1. **创建飞书应用**
   - 前往 [飞书开放平台](https://open.feishu.cn/app)
   - 点击"创建应用"并选择"企业自建应用"
   - 输入应用名称和描述

2. **启用机器人功能**
   - 前往"添加应用能力" > "机器人"并点击"添加"
   - 前往"权限管理"并添加以下权限：
     - `im:message`（接收消息）
     - `im:message:send_as_bot`（发送消息）
     - `im:resource`（上传/下载文件）

3. **获取凭证**
   - 前往"凭证与基础信息"并复制 `App ID` 和 `App Secret`

#### 配置

将凭证添加到您的 `config.yaml` 或使用环境变量：

```yaml
channels:
  feishu:
    enabled: true
    app_id: "cli_..." # 或者设置环境变量 FEISHU_APP_ID
    app_secret: "..." # 或者设置环境变量 FEISHU_APP_SECRET
```

#### 使用功能

- **直接聊天**：直接向机器人发送消息
- **实时状态**：在处理过程中查看 "思考中..."、"调用工具..." 更新
- **文件处理**：无缝上传和下载文件

## 🎯 技能系统

技能是可以加载到 Agent 中的模块化功能。每个技能由一个带有 YAML 前置元数据的 `SKILL.md` 文件定义。

### 技能结构

```
data/user/skills/my_skill/
├── SKILL.md           # 技能定义，包含前置元数据
├── examples/          # 示例文件（可选）
├── scripts/           # 辅助脚本（可选）
└── resources/         # 附加资源（可选）
```

### 创建技能

创建一个 `SKILL.md` 文件，格式如下：

```markdown
---
name: My Skill
description: 关于此技能功能的简要描述
---

# 详细说明

提供关于如何使用此技能的详细说明...
```

### 管理技能

- **上传**：使用 Web 界面上传技能 ZIP 文件
- **列出**：通过 API 或 Web 界面查看所有可用技能
- **删除**：通过 API 或 Web 界面删除技能
- **重载**：上传或删除时自动重载技能

## 🎨 前端特性

- **现代界面** - 简洁、响应式设计，深色主题
- **Markdown 支持** - 标题、代码块、列表、链接、表格
- **代码高亮** - GitHub Dark 主题的代码块
- **文件管理** - 拖放上传、内联下载链接
- **国际化** - 英文和中文支持
- **Web 终端** - 集成 xterm.js 终端，支持 PTY
- **实时更新** - 基于 WebSocket 的流式响应

## 🛠️ 开发

### 运行测试

```bash
# 后端测试（如果可用）
poetry run pytest

# 前端测试
cd web
npm test
```

### 生产构建

详细的生产环境部署说明，包括 Docker、反向代理配置、SSL/TLS 设置和监控，请参阅 **[BUILD.md](./BUILD.md)**。

**快速生产构建：**

```bash
# 构建前端
cd web
npm run build
npm start

# 以生产模式运行后端
poetry run uvicorn server.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 代码风格

- **Python**：遵循 PEP 8 指南
- **TypeScript/React**：遵循 ESLint 配置
- **格式化**：使用一致的缩进和命名约定

## 📝 许可证

MIT

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

### 如何贡献

1. Fork 本仓库
2. 创建你的特性分支（`git checkout -b feature/amazing-feature`）
3. 提交你的更改（`git commit -m 'Add some amazing feature'`）
4. 推送到分支（`git push origin feature/amazing-feature`）
5. 打开一个 Pull Request

## 🙏 致谢

- 使用 [FastAPI](https://fastapi.tiangolo.com/) 构建
- 前端由 [Next.js](https://nextjs.org/) 驱动
- 通过 [Model Context Protocol](https://modelcontextprotocol.io/) 集成 MCP
- 通过 [Slack Bolt](https://slack.dev/bolt-python/) 集成 Slack
- 通过 [Lark Open API](https://open.feishu.cn/) 集成飞书
