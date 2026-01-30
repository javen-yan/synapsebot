# AgentLite

[English](./README.md) | 简体中文

> 一个轻量级的 AI Agent 框架，集成 MCP（模型上下文协议），提供现代化的实时流式聊天界面。

## ✨ 特性

### 核心功能

- 🤖 **AI Agent 框架** - 基于 DeepSeek Chat，支持工具调用
- 🔌 **MCP 集成** - 连接多个 MCP 服务器（文件系统、bash、git）
- 🎯 **可扩展技能** - 从系统和用户目录加载自定义技能
- 💬 **流式聊天** - 实时 SSE 流式传输，打字机效果
- 🎨 **现代界面** - Next.js 前端，TailwindCSS 深色主题

### 技术特性

- **静默工具执行** - 工具在后台运行，不中断流式输出
- **Markdown 渲染** - 完整的 GitHub Flavored Markdown 和代码高亮
- **性能日志** - 详细的计时日志用于调试
- **思考动画** - Agent 处理时的视觉反馈

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Poetry（Python 包管理器）

### 安装

1. **克隆仓库**

```bash
git clone <repository-url>
cd agent-lite
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

# 编辑 config.yaml 并添加你的 DeepSeek API Key
# llm:
#   api_key: "your-api-key-here"
```

### 运行

**终端 1 - 后端：**

```bash
poetry run uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

**终端 2 - 前端：**

```bash
cd web
npm run dev
```

**访问：**

- 前端：http://localhost:3000
- API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 📁 项目结构

```
agent-lite/
├── core/                    # 核心 agent 逻辑
│   ├── agent.py            # 主 agent，支持流式传输
│   ├── agent_lite.py       # Agent 初始化
│   ├── llm.py              # LLM 客户端封装
│   ├── mcp_client.py       # MCP 服务器连接
│   ├── tools.py            # 工具注册表
│   ├── skills.py           # 技能加载器
│   └── config.py           # 配置管理
├── data/
│   ├── system/             # 系统资源
│   │   ├── mcp_config.json # MCP 服务器配置
│   │   ├── mcp_server_*.py # MCP 服务器实现
│   │   └── skills/         # 系统技能
│   └── user/               # 用户自定义资源
│       └── skills/         # 用户技能
├── web/                    # Next.js 前端
│   ├── app/
│   │   ├── page.tsx        # 聊天界面
│   │   ├── skills/         # 技能管理
│   │   └── tools/          # 工具管理
│   └── lib/
│       └── api.ts          # API 客户端，支持 SSE
├── api.py                  # FastAPI 后端
├── main.py                 # CLI 入口
└── config.yaml             # 配置文件
```

## 🔧 配置

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

### MCP 服务器

在 `data/system/mcp_config.json` 中配置 MCP 服务器：

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

### 外部 MCP 服务器

你可以从 [AgentSkills.io](https://agentskills.io) 发现和连接更多 MCP 服务器。该平台提供了丰富的 MCP 服务器集合，包括：

- 数据库连接（PostgreSQL, MySQL, MongoDB 等）
- API 集成（GitHub, Slack, Google 等）
- 开发工具（Docker, Kubernetes 等）
- 数据处理工具

访问 [https://agentskills.io](https://agentskills.io) 浏览可用的 MCP 服务器并查看集成说明。

## 💡 使用方法

### Web 界面

1. 打开 http://localhost:3000
2. 在输入框中输入你的消息
3. 观察"思考中..."动画，等待 agent 处理
4. 实时查看带有 markdown 格式的流式响应

### 命令行

```bash
poetry run python main.py
```

### API

```bash
# 非流式
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好！"}'

# 流式（SSE）
curl -N http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "你好！"}'
```

## 🛠️ 创建技能

技能位于 `data/user/skills/`。每个技能是一个目录，包含：

```
my-skill/
├── SKILL.md          # 技能文档（必需）
├── scripts/          # 可执行脚本
└── resources/        # 其他资源
```

**SKILL.md 格式：**

```markdown
---
name: my-skill
description: 简短描述
---

# 技能文档

关于如何使用此技能的详细说明...
```

## 🎨 前端特性

- **深色主题** - 优雅的 slate-900 背景配青色强调色
- **Markdown 支持** - 标题、代码块、列表、链接
- **代码高亮** - GitHub Dark 主题
- **响应式设计** - 支持桌面和移动端
- **思考指示器** - 脑图标配动画点

## 许可证

MIT

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。
