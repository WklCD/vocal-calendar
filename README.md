# Vocal Calendar — 语音驱动的智能日历

一个支持语音交互的日历管理系统，用户可以通过自然语言语音指令创建、修改、删除、查询日程，系统内置 NLU（自然语言理解）引擎，支持 AI 大模型解析和规则兜底，并提供每日简报、空闲时段推荐、冲突检测等智能辅助功能。

## 功能概览

| 功能模块 | 说明 |
|---------|------|
| 语音交互 | 浏览器端语音识别 → 后端 NLU 解析 → 执行日历操作 → 语音播报结果 |
| 日历管理 | 月/周/日视图切换、事件拖拽、右键菜单编辑删除、颜色分类 |
| AI 智能辅助 | 每日简报、空闲时段推荐、日程冲突检测 |
| 多层级提醒 | 事件级提醒（支持多条）、应用内弹窗 + 声音通知 |
| 用户系统 | 注册/登录、JWT 鉴权（access_token 30min + refresh_token 7d） |
| 数据导入导出 | 支持 iCal / JSON / CSV 格式导出，iCal 文件导入 |
| 分享链接 | 生成只读日历分享链接 |
| 天气与农历 | 基于地理位置显示当日天气、农历日期 |
| 节假日标记 | 日历上自动标注中国法定节假日 |

## 原创功能说明

本项目的**核心原创部分**包括：

1. **语音指令 NLU 引擎**：自研的自然语言理解服务（`backend/app/services/nlu_service.py`），采用 LLM + 规则兜底双层架构。LLM 层通过 Adapter 模式适配多家大模型（MiMo / 通义千问 / OpenAI / 智谱 GLM），规则层（`MockLLM`）使用正则表达式实现中文日历指令的离线解析，支持中文数字时间（如"下午五点"→17:00）、相对日期（明天/后天/大后天）等。

2. **渐进式事件匹配策略**（`backend/app/services/voice_service.py`）：语音删除/修改事件时，采用四级渐进匹配（标题+日期+时间 → 日期+时间 → 标题+日期 → 标题），避免误删同名事件。

3. **多轮对话上下文管理**（`backend/app/services/voice_context.py`）：基于 Redis 的语音会话上下文存储，支持追问式多轮对话（如用户说"开会"，系统追问"安排在什么时间？"）。

4. **LLM Adapter 模式**（`backend/app/services/llm/`）：统一的 LLM 抽象接口，新增大模型只需添加一个适配文件 + 配置项，无需修改业务代码。

5. **语音播报系统**：集成 MiMo TTS API 实现语音结果播报，支持多音色选择，前端有序列号并发控制防止播报乱序。

6. **空闲时段推荐**（`backend/app/services/ai_service.py`）：分析用户日历中的空闲时段，按优先级推荐可安排的时间段。

## 技术栈与依赖

### 前端

| 依赖 | 版本 | 用途 |
|------|------|------|
| React | ^19.2.6 | UI 框架 |
| Vite | ^8.0.12 | 构建工具 |
| TypeScript | ~6.0.2 | 类型系统 |
| Zustand | ^5.0.14 | 状态管理 |
| React Router DOM | ^7.16.0 | 路由 |
| FullCalendar（@fullcalendar/react, daygrid, timegrid, list, interaction） | ^6.1.20 | 日历视图 |
| Recharts | ^3.8.1 | 图表渲染 |
| Axios | ^1.16.1 | HTTP 请求 |
| React Hook Form | ^7.76.1 | 表单管理 |
| @hookform/resolvers | ^5.4.0 | 表单校验桥接 |
| Zod | ^4.4.3 | 数据校验 |
| Preact | ^10.29.2 | 轻量 UI 运行时 |

**开发依赖**：Vite React 插件、ESLint、Vitest、Testing Library（jest-dom / react / user-event）、jsdom、typescript-eslint、vite-plugin-mkcert

### 后端

| 依赖 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.115.0 | Web 框架 |
| Uvicorn | 0.30.6 | ASGI 服务器 |
| SQLAlchemy | 2.0.35 | ORM |
| Alembic | 1.13.2 | 数据库迁移 |
| psycopg2-binary | 2.9.9 | PostgreSQL 驱动 |
| Pydantic | 2.9.2 | 数据校验 |
| pydantic-settings | 2.5.2 | 配置管理 |
| python-dotenv | 1.0.1 | 环境变量加载 |
| Redis | 5.1.1 | 缓存/会话存储 |
| passlib[bcrypt] | 1.7.4 | 密码哈希 |
| bcrypt | 4.0.1 | 密码加密 |
| PyJWT | 2.9.0 | JWT 令牌 |
| httpx | 0.27.2 | 异步 HTTP 客户端（调用 LLM API） |
| APScheduler | 3.10.4 | 定时任务（提醒推送、每日简报） |
| LunarCalendar | 0.0.9 | 农历转换 |
| icalendar | 6.1.0 | iCal 格式解析/生成 |
| python-dateutil | 2.9.0 | 日期工具 |
| pytest-asyncio | 0.24.0 | 异步测试 |

### 基础设施

| 组件 | 说明 |
|------|------|
| PostgreSQL 16 | 主数据库 |
| Redis 7 | 缓存、语音会话上下文、提醒队列 |
| Docker & Docker Compose | 容器化部署 |

## 从 GitHub 部署的完整步骤

### 1. 克隆仓库

```bash
git clone https://github.com/WklCD/vocal-calendar.git
cd vocal-calendar
```

### 2. 环境要求

- **Docker & Docker Compose**（用于启动 PostgreSQL 和 Redis）
- **Node.js 20+**（前端构建）
- **Python 3.12+**（后端运行）
- **Chrome 或 Edge 浏览器**（语音功能依赖 Web Speech API）

### 3. 启动数据库和 Redis

```bash
docker compose up -d postgres redis
```

等待容器健康检查通过（首次启动需要拉取镜像）：

```bash
docker compose ps  # 确认 postgres 和 redis 状态为 healthy
```

### 4. 启动后端

```bash
cd backend

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 执行数据库迁移
alembic upgrade head

# （可选）配置 LLM API Key —— 不配置则使用 MockLLM 规则解析
# 在 backend/ 目录下创建 .env 文件：
echo 'MIMO_API_KEY=your-key-here' >> .env
echo 'LLM_PROVIDER=mimo' >> .env

# 启动后端服务
uvicorn app.main:app --reload --port 8000
```

后端启动后访问 `http://localhost:8000/docs` 可查看 API 文档（Swagger UI）。

### 5. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端启动后访问 `https://localhost:5173` 即可使用。

> **注意**：前端开发服务器使用 HTTPS（本地自签名证书已包含在 `frontend/certs/` 目录中），浏览器可能会提示证书不受信任，点击"继续访问"即可。HTTPS 是 Web Speech API 的要求。

### 6. 使用语音功能

1. 在 Chrome 或 Edge 浏览器中打开 `https://localhost:5173`
2. 注册/登录账号
3. 点击右下角的麦克风按钮
4. 允许浏览器使用麦克风
5. 说出指令，例如：
   - "帮我创建明天下午三点的会议"
   - "修改明天的会议到下午五点"
   - "删除明天5点的会议"
   - "明天有什么安排"

### 7. 运行测试

```bash
# 后端测试
cd backend
pytest -v

# 前端测试
cd frontend
npx vitest run
```

## 项目结构

```
vocal-calendar/
├── frontend/                    # React SPA
│   ├── src/
│   │   ├── features/            # 功能模块（auth, calendar, voice, events, reminders, ai, settings, weather, holidays, share）
│   │   ├── hooks/               # 自定义 Hooks（useSpeechRecognition, useSpeechSynthesis, useAudioVisualizer）
│   │   ├── stores/              # Zustand 状态管理
│   │   ├── services/            # API 调用层
│   │   ├── styles/              # CSS 变量、全局样式、主题
│   │   └── components/          # 共享 UI 组件
│   ├── certs/                   # 本地 HTTPS 证书
│   └── package.json
├── backend/                     # FastAPI API 服务
│   ├── app/
│   │   ├── api/                 # 路由（auth, events, categories, reminders, voice, ai, websocket, export_import）
│   │   ├── services/            # 业务逻辑层
│   │   │   ├── llm/             # LLM 适配器（base → qwen / openai / glm / mimo / mock + factory）
│   │   │   ├── voice_service.py # 语音指令执行引擎
│   │   │   ├── nlu_service.py   # NLU 解析服务
│   │   │   └── voice_context.py # 多轮对话上下文
│   │   ├── models/              # SQLAlchemy 模型
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   └── core/                # 配置、安全（JWT+bcrypt）、数据库、WebSocket
│   ├── alembic/                 # 数据库迁移脚本
│   ├── tests/                   # 测试
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml           # PostgreSQL + Redis
├── docs/                        # 设计文档与开发计划
└── README.md
```

## 数据流

```
用户语音 → 浏览器 Web Speech API (zh-CN)
  → VoicePanel 发送文本到 /api/voice/command
  → VoiceService.process_command()
      → NLUService.parse_command()
          → LLM Adapter 解析（或 MockLLM 规则解析）
          → 相对日期后处理
          → 生成响应文本
      → _execute_action() 执行对应操作
          → _create_event / _delete_event / _query_events / _modify_event
      → 记录语音日志
  → 返回结果 → TTS 语音播报 → 刷新日历
```

## 环境变量说明

在 `backend/` 目录下创建 `.env` 文件可覆盖默认配置：

```env
# 数据库（默认值与 docker-compose.yml 一致）
DATABASE_URL=postgresql://vocal_user:vocal_pass@localhost:5432/vocal_calendar

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT 密钥（生产环境务必修改）
JWT_SECRET_KEY=your-production-secret-key

# LLM 配置（不配置则使用 MockLLM 规则解析，无需 API Key 即可使用语音功能）
LLM_PROVIDER=mock          # 可选: mock / mimo / qwen / openai / glm
MIMO_API_KEY=              # 小米 MiMo API Key
QWEN_API_KEY=              # 通义千问 API Key
OPENAI_API_KEY=            # OpenAI API Key
GLM_API_KEY=               # 智谱 GLM API Key
```
