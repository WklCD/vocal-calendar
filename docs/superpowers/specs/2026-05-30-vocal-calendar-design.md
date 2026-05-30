# Vocal Calendar — 系统设计文档

> **项目名称**：vocal-calendar（语音日历工具）
> **文档版本**：v1.0
> **创建日期**：2026-05-30
> **状态**：已确认

---

## 1. 项目概述

### 1.1 目标

从零开发一个语音驱动的日历工具，运行在 Web 端，支持语音交互管理日程、AI 智能辅助、多层级提醒，界面采用活力多彩风格（Google Calendar 风格）。

### 1.2 核心流程

```
brainstorming → writing-plans → subagent-driven-development → test-driven-development → requesting-code-review → 交付
```

### 1.3 技术栈总览

| 层级 | 技术 | 用途 |
|------|------|------|
| 前端框架 | React 18 + Vite 6 | 核心框架 + 构建工具 |
| 路由 | React Router v6 | 页面路由管理 |
| 状态管理 | Zustand | 全局状态 |
| 样式 | Vanilla CSS + CSS Variables | 主题系统、动画 |
| 日历组件 | FullCalendar React | 日/周/月/议程视图 |
| 语音 | Web Speech API | 浏览器原生语音转文字 + TTS |
| 后端框架 | Python FastAPI | 异步高性能 API |
| 数据库 | PostgreSQL 16 | 主数据存储 |
| ORM | SQLAlchemy 2.0 + Alembic | 映射 + 迁移 |
| 缓存 | Redis | 会话管理 + 任务队列 |
| 定时任务 | APScheduler | 事件提醒定时触发 |
| 认证 | JWT（PyJWT） | 无状态用户认证 |
| 实时通信 | FastAPI WebSocket | 实时提醒推送 |
| 数据校验 | Pydantic v2 | 请求/响应校验 |
| AI | 通义千问 / OpenAI / 智谱 | 自然语言理解（可切换） |
| 部署 | Docker + Docker Compose + Nginx | 容器化编排 |

---

## 2. 整体架构

### 2.1 架构方案

采用**经典分层架构**，前后端完全分离：

```
前端 React ←→ 后端 FastAPI ←→ PostgreSQL / Redis
                     ↓
               LLM 适配层 ← Qwen / GPT / GLM
```

- 前后端通过 REST API + WebSocket 通信
- 后端按 `routers → services → models` 分层
- LLM 层用 Adapter 模式，统一接口 + 配置驱动切换

### 2.2 项目结构

```
vocal-calendar/
├── frontend/                  # React 前端
│   ├── src/
│   │   ├── components/        # 通用 UI 组件（Button, Modal, Toast...）
│   │   ├── features/          # 按功能模块组织
│   │   │   ├── auth/          # 登录/注册
│   │   │   ├── calendar/      # 日历视图（日/周/月/议程）
│   │   │   ├── voice/         # 语音交互（录音、识别、波形）
│   │   │   ├── events/        # 事件 CRUD
│   │   │   ├── reminders/     # 提醒管理
│   │   │   ├── ai/            # AI 功能（冲突检测、摘要）
│   │   │   └── settings/      # 设置（主题、账户）
│   │   ├── hooks/             # 自定义 hooks（useSpeech, useCalendar...）
│   │   ├── stores/            # Zustand stores
│   │   ├── services/          # API 调用层
│   │   ├── utils/             # 工具函数
│   │   ├── styles/            # 全局样式、CSS 变量、主题
│   │   └── App.tsx
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
│
├── backend/                   # FastAPI 后端
│   ├── app/
│   │   ├── api/               # 路由层（按模块拆分）
│   │   │   ├── auth.py
│   │   │   ├── events.py
│   │   │   ├── reminders.py
│   │   │   ├── voice.py
│   │   │   ├── ai.py
│   │   │   └── websocket.py
│   │   ├── services/          # 业务逻辑层
│   │   │   ├── auth_service.py
│   │   │   ├── event_service.py
│   │   │   ├── reminder_service.py
│   │   │   ├── voice_service.py
│   │   │   ├── llm/           # LLM 抽象层
│   │   │   │   ├── base.py    # 抽象接口
│   │   │   │   ├── qwen.py    # 通义千问适配器
│   │   │   │   ├── openai.py  # OpenAI 适配器
│   │   │   │   ├── glm.py     # 智谱 GLM 适配器
│   │   │   │   └── factory.py # 工厂：根据配置创建实例
│   │   │   └── nlu_service.py # 自然语言理解
│   │   ├── models/            # SQLAlchemy 模型
│   │   │   ├── user.py
│   │   │   ├── event.py
│   │   │   ├── reminder.py
│   │   │   └── voice_log.py
│   │   ├── schemas/           # Pydantic 请求/响应模型
│   │   ├── core/              # 配置、安全、依赖注入
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── tasks/             # APScheduler 定时任务
│   │   └── main.py            # FastAPI 入口
│   ├── alembic/               # 数据库迁移
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml         # 前端 + 后端 + PostgreSQL + Redis
├── nginx/                     # Nginx 配置（反向代理）
├── docs/                      # 设计文档、开发计划
├── .gitignore
└── README.md
```

### 2.3 设计原则

- 前端按 **feature 模块** 组织，每个 feature 自带 components + hooks + store slice
- 后端按 **routers → services → models** 三层分离
- LLM 层独立为 **Adapter 模式**，新增 LLM 只需加一个适配器文件 + 配置

---

## 3. 数据库设计

### 3.1 ER 关系

```
Users 1──N Events 1──N Reminders
Users 1──N VoiceLogs
Users 1──N Categories
```

### 3.2 表结构

#### users

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| email | VARCHAR(255) | 唯一，登录账号 |
| username | VARCHAR(100) | 显示名 |
| password_hash | VARCHAR(255) | bcrypt 加密 |
| avatar_url | VARCHAR(500) | 可选头像 |
| theme | VARCHAR(20) | light / dark，默认 light |
| created_at | TIMESTAMP | 注册时间 |
| updated_at | TIMESTAMP | 最后更新 |

#### events

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | FK → users.id |
| title | VARCHAR(200) | 事件标题 |
| description | TEXT | 备注 |
| start_time | TIMESTAMP | 开始时间 |
| end_time | TIMESTAMP | 结束时间 |
| is_all_day | BOOLEAN | 全天事件 |
| location | VARCHAR(300) | 地点 |
| category_id | UUID | FK → categories.id，可空 |
| priority | SMALLINT | 1-5，默认 3 |
| color | VARCHAR(7) | 自定义颜色 #hex |
| recurrence_rule | VARCHAR(100) | iCal RRULE 格式 |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### reminders

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| event_id | UUID | FK → events.id |
| user_id | UUID | FK → users.id |
| remind_at | TIMESTAMP | 提醒触发时间 |
| type | VARCHAR(20) | push / voice / both |
| status | VARCHAR(20) | pending / sent / dismissed |
| created_at | TIMESTAMP | |

#### voice_logs

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | FK → users.id |
| raw_text | TEXT | 语音转文字原文 |
| parsed_intent | VARCHAR(50) | LLM 解析的意图 |
| parsed_entities | JSONB | 解析出的实体（时间、标题等） |
| response_text | TEXT | 系统回复 |
| created_at | TIMESTAMP | |

#### categories

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | FK → users.id |
| name | VARCHAR(50) | 分类名 |
| color | VARCHAR(7) | 分类颜色 |
| icon | VARCHAR(50) | 图标名 |

### 3.3 索引策略

- `events`：`(user_id, start_time)` 复合索引 — 日历查询核心路径
- `reminders`：`(user_id, status, remind_at)` — 定时任务扫描
- `voice_logs`：`(user_id, created_at)` — 历史查询

---

## 4. API 接口设计

### 4.1 认证模块 `/api/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册（email + password + username） |
| POST | `/api/auth/login` | 登录，返回 access_token + refresh_token |
| POST | `/api/auth/refresh` | 刷新 token |
| GET | `/api/auth/me` | 获取当前用户信息 |
| PUT | `/api/auth/me` | 更新用户设置（主题、头像等） |

### 4.2 事件模块 `/api/events`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/events` | 查询事件（支持 `start`, `end` 时间范围参数） |
| POST | `/api/events` | 创建事件 |
| GET | `/api/events/{id}` | 获取单个事件 |
| PUT | `/api/events/{id}` | 更新事件 |
| DELETE | `/api/events/{id}` | 删除事件 |
| GET | `/api/events/search?q=` | 全文搜索 |

### 4.3 分类模块 `/api/categories`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/categories` | 获取用户的所有分类 |
| POST | `/api/categories` | 创建分类 |
| PUT | `/api/categories/{id}` | 更新分类 |
| DELETE | `/api/categories/{id}` | 删除分类 |

### 4.4 提醒模块 `/api/reminders`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/reminders` | 获取用户的提醒列表 |
| PUT | `/api/reminders/{id}/dismiss` | 关闭提醒 |

### 4.5 语音模块 `/api/voice`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/voice/command` | 提交语音文本，返回解析结果 + 执行动作 |
| GET | `/api/voice/logs` | 获取语音指令历史 |
| GET | `/api/voice/help` | 获取语音指令帮助列表 |

### 4.6 AI 模块 `/api/ai`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ai/parse` | 自然语言 → 结构化日历指令 |
| POST | `/api/ai/detect-conflicts` | 检测指定时间段的事件冲突 |
| POST | `/api/ai/recommend-slot` | 推荐空闲时段 |
| GET | `/api/ai/daily-briefing` | 获取每日语音播报摘要 |

### 4.7 WebSocket `/ws/reminder`

- 连接时鉴权（JWT token 作为 query param）
- 服务端推送：`{"type": "reminder", "event_id": "...", "title": "...", "remind_at": "..."}`
- 客户端确认：`{"type": "ack", "reminder_id": "..."}`

### 4.8 通用约定

- 所有响应格式：`{"code": 0, "data": {...}, "message": "ok"}`
- 分页：`?page=1&size=20`，响应含 `total` 字段
- 错误码：400 参数错误 / 401 未认证 / 403 无权限 / 404 不存在 / 500 服务端错误
- JWT：access_token 有效期 30 分钟，refresh_token 7 天

---

## 5. 前端架构

### 5.1 路由设计

```
/                    → 重定向到 /calendar
/calendar            → 日历主页面（默认月视图）
/calendar/day        → 日视图
/calendar/week       → 周视图
/calendar/month      → 月视图
/calendar/agenda     → 议程视图
/login               → 登录页
/register            → 注册页
/settings            → 设置页（主题、账户、语音偏好）
/voice-history       → 语音指令历史
```

### 5.2 状态管理（Zustand）

```
stores/
├── useAuthStore       # 用户认证状态（token、用户信息、登录/登出）
├── useEventStore      # 事件数据（CRUD、当前视图的时间范围、选中事件）
├── useVoiceStore      # 语音状态（录音中、识别结果、对话上下文）
├── useReminderStore   # 提醒队列（待处理提醒、已关闭提醒）
├── useThemeStore      # 主题（light/dark，持久化到 localStorage）
└── useUIStore         # UI 状态（侧边栏展开、模态框、加载状态）
```

### 5.3 核心页面结构

```
App
├── AuthGuard              # 路由守卫，未登录跳转 /login
├── Layout
│   ├── Sidebar            # 导航侧边栏（日历、语音历史、设置）
│   ├── TopBar             # 顶部栏（搜索、语音按钮、用户头像）
│   ├── VoicePanel         # 语音交互浮动面板（可收起）
│   └── MainContent        # 路由出口
│       ├── CalendarView   # 日历页面（含 4 种视图切换）
│       ├── VoiceHistory   # 语音历史
│       ├── Settings       # 设置
│       └── AuthPages      # 登录/注册
├── ReminderToast          # 全局提醒弹窗（WebSocket 驱动）
└── EventModal             # 事件创建/编辑模态框
```

### 5.4 语音交互流程

```
用户按住语音按钮
    ↓
Web Speech API 开始录音 → 波形可视化
    ↓
实时转文字（interim results）→ 显示在输入框
    ↓
松开按钮 → 最终文本发送到 /api/voice/command
    ↓
后端 NLU 解析意图 + 实体
    ↓
返回结果：
  ├── 确认型 → "好的，已为你创建：周三下午3点开会"
  ├── 追问型 → "你想把这件事安排在什么时间？"
  └── 错误型 → "抱歉，我没有理解，你可以再说一次"
```

### 5.5 主题系统（CSS Variables）

```css
:root {
  /* 活力多彩配色 - 浅色主题 */
  --color-primary: #4285F4;       /* Google 蓝 */
  --color-secondary: #EA4335;     /* Google 红 */
  --color-accent: #34A853;        /* Google 绿 */
  --color-warning: #FBBC04;       /* Google 黄 */
  --color-bg: #FFFFFF;
  --color-surface: #F8F9FA;
  --color-text: #202124;
  --color-text-secondary: #5F6368;
  --color-border: #DADCE0;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.12);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.15);
}

[data-theme="dark"] {
  --color-bg: #1A1A2E;
  --color-surface: #16213E;
  --color-text: #E8E8E8;
  --color-text-secondary: #A0A0A0;
  --color-border: #2A2A4A;
}
```

---

## 6. 语音 & AI 模块

### 6.1 语音识别层（前端）

使用 Web Speech API 封装为 React Hook：

- `useSpeechRecognition`：start()/stop() 控制录音、interimResults 实时中间结果、onResult 回调最终文本、自动检测浏览器支持
- `useSpeechSynthesis`：speak(text) 语音播报、播报提醒内容、每日摘要播报

### 6.2 LLM 抽象层（后端）

```python
class BaseLLM(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> str:
        """通用对话接口"""

    @abstractmethod
    async def parse_calendar_command(self, text: str, context: dict) -> dict:
        """自然语言 → 结构化日历指令
        返回: {
            "intent": "create" | "delete" | "modify" | "query",
            "entities": {
                "title": "开会",
                "date": "2026-06-01",
                "time": "15:00",
                "duration": 60,
                "location": "会议室A",
                "priority": 3
            },
            "confidence": 0.92,
            "need_clarify": false,
            "clarify_question": null
        }
        """

def create_llm(provider: str = None) -> BaseLLM:
    """根据配置创建 LLM 实例
    provider: "qwen" | "openai" | "glm"，默认从 config 读取
    """
```

### 6.3 NLU 服务（自然语言理解）

```
用户语音文本 "后天下午三点和张伟开会"
    ↓
NLU Service 调用 LLM parse_calendar_command
    ↓
返回结构化结果
    ↓
confidence < 0.7 或 need_clarify=true → 追问用户
confidence >= 0.7 → 执行动作 → 语音确认
```

### 6.4 多轮对话上下文

- Redis 存储，key = `voice_session:{user_id}`
- 结构：`{ last_intent, last_entities, turn_count, expires_at }`
- 5 分钟无交互自动过期
- 支持追问补全（如用户说"创建一个会议"，系统追问时间）

### 6.5 AI 智能功能

- **冲突检测**：查询同时间段已有事件，返回冲突列表，LLM 生成解决建议
- **空闲时段推荐**：查询当天事件，找出空闲间隙，按优先级排序
- **每日摘要**：查询当天/次日事件，LLM 生成自然语言摘要，通过 WebSocket 推送 + 语音播报

---

## 7. 提醒与通知系统

### 7.1 三层提醒架构

```
APScheduler（后端每分钟扫描 reminders 表）
    ↓
WebSocket 推送（在线）/ 浏览器 Push（离线）
    ↓
前端展示：Toast 弹窗 / 浏览器通知 / 语音播报
```

### 7.2 多层级提前提醒

创建事件时可设置多个提醒点：
```json
{
    "reminders": [
        {"offset": -10, "unit": "minutes"},
        {"offset": -1, "unit": "hours"},
        {"offset": -1, "unit": "days"}
    ]
}
```

### 7.3 浏览器 Push Notification

1. 页面加载时请求通知权限
2. 注册 Service Worker
3. 从后端获取 VAPID 公钥
4. 订阅 Push，将 subscription 发送到后端保存
5. 后端通过 webpush 库发送离线通知

### 7.4 每日摘要定时任务

- 早间摘要：每天 7:30，查询当天事件，LLM 生成播报
- 晚间摘要：每天 21:00，查询次日事件，LLM 生成播报

---

## 8. 测试策略

### 8.1 TDD 循环

每个功能严格遵循 RED → GREEN → REFACTOR 循环。

### 8.2 覆盖率要求

| 任务复杂度 | 最低覆盖率 | 说明 |
|-----------|-----------|------|
| 简单 | 85% | CRUD、基础路由、简单组件 |
| 中等 | 91% | 语音交互、提醒系统、状态管理 |
| 复杂 | 94% | NLU 解析、LLM 适配层、多轮对话 |

### 8.3 测试结构

**后端**：
- `tests/unit/` — 业务逻辑单元测试
- `tests/integration/` — API 端点集成测试
- `tests/e2e/` — 端到端场景测试

**前端**：
- 组件测试（Vitest + React Testing Library）
- Hook 测试（Vitest + @testing-library/react-hooks）
- Store 测试（Vitest）

### 8.4 Mock 策略

- **LLM 调用** — 测试时 mock 所有 LLM 请求，返回固定结构数据
- **Web Speech API** — 前端测试时 mock SpeechRecognition
- **WebSocket** — 后端测试时 mock WebSocket 连接
- **时间相关** — freezegun（后端）+ vi.useFakeTimers（前端）

---

## 9. 错误处理与边界情况

### 9.1 全局错误处理

**后端**：统一异常拦截器，业务异常基类 `AppError(code, message)`。

**前端**：axios 拦截器统一处理：
- 401 → 自动 refresh token → 失败跳转登录
- 403 → 提示无权限
- 404 → 提示资源不存在
- 500 → 全局 Toast 错误提示
- 网络断开 → 提示离线状态

### 9.2 关键边界情况

| 场景 | 处理策略 |
|------|---------|
| 浏览器不支持 Web Speech API | 显示文字输入框替代，语音按钮灰化 + 提示 |
| LLM API 超时/不可用 | 降级为关键词匹配，提示用户 AI 功能暂不可用 |
| WebSocket 断连 | 自动重连（指数退避），离线期间轮询 API |
| 事件拖拽跨天/跨月 | FullCalendar 原生支持，后端校验时间合法性 |
| 重复事件修改单次 vs 全部 | 弹窗让用户选择"仅此一次"或"所有重复" |
| 并发编辑同一事件 | 乐观锁（updated_at 比对），冲突时提示刷新 |
| 时区问题 | 后端统一 UTC 存储，前端按用户本地时区显示 |
| 大量事件性能 | 事件列表分页加载，日历视图按需加载 |

### 9.3 数据校验

- 后端：Pydantic v2 严格校验所有请求参数
- 前端：react-hook-form + zod 校验
- 前后端双重校验，后端为权威

---

## 10. 开发阶段划分

### 阶段总览

| 阶段 | 名称 | 核心交付物 | 复杂度 |
|------|------|-----------|--------|
| 1 | 项目基础搭建 | 项目骨架、Docker 环境、数据库连接 | 小 |
| 2 | 用户认证系统 | 注册/登录/JWT/用户设置 | 中 |
| 3 | 日历核心视图 | FullCalendar 集成、四视图 | 中 |
| 4 | 事件 CRUD | 事件管理、拖拽、右键菜单、分类 | 中 |
| 5 | 语音交互基础 | Web Speech API、波形、实时转文字 | 中 |
| 6 | AI 自然语言理解 | LLM 抽象层、NLU、多轮对话 | 大 |
| 7 | 提醒与通知系统 | APScheduler、WebSocket、Push | 中 |
| 8 | AI 智能功能 | 冲突检测、空闲推荐、每日摘要 | 中 |
| 9 | 增值功能 | 天气、节假日、统计、分享、PDF | 中 |
| 10 | 部署与优化 | Docker Compose、Nginx、HTTPS、PWA | 小 |

### 各阶段详情

#### 阶段 1：项目基础搭建
- 初始化 monorepo（frontend + backend）
- Docker Compose 配置（PostgreSQL + Redis + 后端）
- FastAPI 项目骨架（main.py、config、database 连接）
- React + Vite 项目骨架（路由、全局样式、主题变量）
- Alembic 迁移配置 + 初始迁移
- 基础 health check API
- `.gitignore`、`README.md`

#### 阶段 2：用户认证系统
- User 模型 + 迁移
- 注册/登录 API（bcrypt + JWT）
- Token 刷新机制
- 前端登录/注册页面
- AuthGuard 路由守卫
- 用户设置页面（主题切换、基本信息修改）
- 前后端联调

#### 阶段 3：日历核心视图
- FullCalendar React 集成
- 月视图（默认视图）
- 周视图
- 日视图
- 议程视图
- 视图切换导航
- 事件数据与日历绑定
- 活力多彩风格适配

#### 阶段 4：事件 CRUD
- Event 模型 + Category 模型 + 迁移
- 事件 CRUD API（含分类、优先级、地点、备注）
- 事件创建/编辑模态框
- 点击空白格快速创建
- 拖拽调整事件时间
- 右键上下文菜单
- 分类管理（颜色、图标）
- 重复事件（RRULE 生成）
- 全文搜索

#### 阶段 5：语音交互基础
- `useSpeechRecognition` Hook 封装
- `useSpeechSynthesis` Hook 封装
- 语音按钮 UI（按住说话）
- 录音波形可视化（Canvas/Web Audio API）
- 实时转文字显示
- 浏览器兼容性检测 + 降级提示
- 语音状态管理（useVoiceStore）

#### 阶段 6：AI 自然语言理解
- LLM 抽象层（BaseLLM + Factory）
- 通义千问 Qwen 适配器
- OpenAI 适配器
- 智谱 GLM 适配器
- NLU Service（意图识别 + 实体抽取）
- 多轮对话上下文（Redis 存储 session）
- 语音指令执行流程
- 语音指令历史记录
- 语音帮助面板

#### 阶段 7：提醒与通知系统
- Reminder 模型 + 迁移
- APScheduler 集成 + 提醒扫描任务
- WebSocket 连接管理
- 前端提醒 Toast 组件
- 浏览器 Push Notification（Service Worker + VAPID）
- 语音播报提醒
- 多层级提醒设置

#### 阶段 8：AI 智能功能
- 冲突检测服务 + API
- 空闲时段推荐服务 + API
- 每日摘要生成（早间/晚间）
- 前端冲突提示 UI
- 前端摘要展示 + 语音播报
- 定时摘要推送

#### 阶段 9：增值功能
- 天气集成（和风天气 API 对接 + 日历天气标注）
- 节假日/调休数据接入（中国法定节假日 API）
- 时间花费统计图表（Recharts）
- 分享只读日程链接（生成带 token 的只读 URL，无需登录即可查看）
- 打印/导出 PDF
- iCal 格式导入/导出

#### 阶段 10：部署与优化
- Docker Compose 生产编排
- Nginx 反向代理配置
- HTTPS 证书（Let's Encrypt）
- PWA 支持（manifest.json + Service Worker）
- 性能优化（懒加载、代码分割）
- 阿里云 ECS 部署
- 最终联调与演示准备

---

## 附录 A：PR 提交规范

1. 基于 feature 分支添加新功能
2. 每个 PR 只做一件事，鼓励小粒度 PR
3. PR 标题：一句话说明新增/修改了什么
4. PR 描述包含：功能描述、实现思路、测试方式
5. 合并后主分支保持可运行状态

## 附录 B：Git 要求

- 开发周期内保持持续的 PR 记录和 commit 提交
- 使用 conventional commits 格式
