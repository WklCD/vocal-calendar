# Vocal Calendar 项目文档

## 一、项目简介

**Vocal Calendar（语音日历）** 是一个语音驱动的 Web 日历工具，支持通过语音交互管理日程、AI 智能辅助、多层级提醒。毕设项目，界面采用活力多彩风格（Google Calendar 风格）。

**核心能力：**
- 🎙️ 语音创建/删除/修改/查询日程
- 🤖 AI 自然语言理解（NLU）解析语音指令
- 🔔 多层级提醒（WebSocket 实时推送 + 浏览器通知）
- 📊 冲突检测、空闲时段推荐、每日语音摘要
- 🌤️ 天气标注、节假日标注、时间统计图表
- 🔗 分享只读日程链接、导出 iCal / PDF
- 🗣️ MiMo TTS 语音合成（9 种音色可选）

---

## 二、技术栈

| 层级 | 技术 |
|------|------|
| **前端** | React 18 + Vite 6 + TypeScript + Zustand + FullCalendar + React Router v6 + Recharts |
| **后端** | Python FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic v2 |
| **数据库** | PostgreSQL 16 + Redis |
| **AI/LLM** | 小米 MiMo（mimo-v2.5）/ 通义千问 / OpenAI / 智谱 GLM（Adapter 模式可切换） |
| **语音识别** | Web Speech API（浏览器原生，Safari/Edge 可用） |
| **语音合成** | MiMo-V2.5-TTS（9 种预置音色） |
| **定时任务** | APScheduler（提醒扫描 + 每日摘要） |
| **实时通信** | FastAPI WebSocket |
| **部署** | Docker + Docker Compose + Nginx |

---

## 三、项目结构

```
vocal-calendar/
├── backend/                          # FastAPI 后端
│   ├── app/
│   │   ├── main.py                   # 应用入口，注册所有路由
│   │   ├── api/                      # API 路由层
│   │   │   ├── auth.py               # 认证（注册/登录/获取用户信息）
│   │   │   ├── events.py             # 事件 CRUD
│   │   │   ├── categories.py         # 分类管理
│   │   │   ├── voice.py              # 语音指令处理
│   │   │   ├── ai.py                 # AI 功能（冲突检测/空闲推荐/摘要/TTS）
│   │   │   ├── reminders.py          # 提醒管理
│   │   │   ├── weather.py            # 天气查询
│   │   │   ├── holidays.py           # 节假日查询
│   │   │   ├── share.py              # 分享链接
│   │   │   ├── websocket.py          # WebSocket 端点
│   │   │   ├── health.py             # 健康检查
│   │   │   └── deps.py               # 公共依赖（get_current_user）
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── auth_service.py       # 认证服务
│   │   │   ├── event_service.py      # 事件服务
│   │   │   ├── voice_service.py      # 语音指令处理（NLU→执行→日志）
│   │   │   ├── nlu_service.py        # NLU 自然语言理解
│   │   │   ├── ai_service.py         # AI 服务（冲突/空闲/摘要）
│   │   │   ├── reminder_service.py   # 提醒服务
│   │   │   ├── weather_service.py    # 天气服务
│   │   │   ├── holiday_service.py    # 节假日服务
│   │   │   ├── share_service.py      # 分享服务
│   │   │   ├── voice_context.py      # 多轮对话上下文（Redis）
│   │   │   └── llm/                  # LLM 适配器层
│   │   │       ├── base.py           # BaseLLM 抽象接口
│   │   │       ├── mimo.py           # 小米 MiMo 适配器
│   │   │       ├── qwen.py           # 通义千问适配器
│   │   │       ├── openai.py         # OpenAI 适配器
│   │   │       ├── glm.py            # 智谱 GLM 适配器
│   │   │       ├── mock.py           # Mock 适配器（开发用，无需 API Key）
│   │   │       └── factory.py        # LLM 工厂（根据配置创建实例）
│   │   ├── models/                   # SQLAlchemy 数据模型
│   │   │   ├── user.py               # 用户
│   │   │   ├── event.py              # 事件
│   │   │   ├── category.py           # 分类
│   │   │   ├── reminder.py           # 提醒
│   │   │   └── voice_log.py          # 语音指令日志
│   │   ├── schemas/                  # Pydantic 请求/响应模型
│   │   ├── core/                     # 核心模块
│   │   │   ├── config.py             # 配置管理（Pydantic Settings）
│   │   │   ├── database.py           # 数据库连接
│   │   │   ├── security.py           # JWT + bcrypt
│   │   │   └── websocket_manager.py  # WebSocket 连接管理
│   │   └── tasks/                    # 定时任务
│   │       ├── reminder_task.py      # 提醒扫描（每分钟）
│   │       └── daily_briefing.py     # 每日摘要（7:30 早间 / 21:00 晚间）
│   ├── alembic/                      # 数据库迁移
│   ├── tests/                        # 测试文件
│   ├── requirements.txt
│   └── .env                          # 环境变量
│
├── frontend/                         # React 前端
│   ├── src/
│   │   ├── App.tsx                   # 路由配置
│   │   ├── features/                 # 功能模块
│   │   │   ├── auth/                 # 认证（登录/注册/AuthGuard）
│   │   │   ├── calendar/             # 日历（CalendarView/CalendarPage）
│   │   │   ├── events/               # 事件（EventForm/EventModal/ContextMenu）
│   │   │   ├── voice/                # 语音（VoicePanel/VoiceButton/VoiceHistory）
│   │   │   ├── ai/                   # AI（ConflictAlert/DailyBriefing/FreeSlotSuggest）
│   │   │   ├── reminders/            # 提醒（ReminderToast）
│   │   │   ├── settings/             # 设置（VoiceSelector 音色选择）
│   │   │   ├── weather/              # 天气（WeatherBadge）
│   │   │   ├── holidays/             # 节假日（HolidayBadge）
│   │   │   ├── stats/                # 统计（TimeStats 饼图）
│   │   │   ├── share/                # 分享（ShareLink/PublicCalendar）
│   │   │   └── export/               # 导出（ExportMenu）
│   │   ├── hooks/                    # 自定义 Hook
│   │   │   ├── useSpeechRecognition.ts  # 语音识别（Web Speech API）
│   │   │   ├── useSpeechSynthesis.ts    # 语音合成（MiMo TTS）
│   │   │   └── useAudioVisualizer.ts    # 音频波形可视化
│   │   ├── stores/                   # Zustand 状态管理
│   │   │   ├── useAuthStore.ts       # 认证状态
│   │   │   ├── useEventStore.ts      # 事件状态（对接后端 API）
│   │   │   ├── useVoiceStore.ts      # 语音识别状态
│   │   │   ├── useReminderStore.ts   # 提醒状态
│   │   │   └── useTtsStore.ts        # TTS 音色选择（持久化到 localStorage）
│   │   ├── services/                 # API 调用层
│   │   │   ├── api.ts                # Axios 实例（JWT 拦截器）
│   │   │   ├── authApi.ts / eventApi.ts / voiceApi.ts / aiApi.ts
│   │   │   ├── reminderApi.ts / weatherApi.ts / holidayApi.ts
│   │   │   ├── shareApi.ts / ttsApi.ts / wsService.ts / pushService.ts
│   │   │   └── ttsApi.ts             # MiMo TTS 服务（合成+播放+取消）
│   │   └── styles/                   # 样式（CSS 变量 + 全局样式）
│   ├── public/
│   │   ├── sw.js                     # Service Worker（Push 通知）
│   │   └── manifest.json             # PWA 配置
│   └── package.json
│
├── docker-compose.yml                # PostgreSQL + Redis
├── CLAUDE.md                         # Claude Code 指引
└── docs/superpowers/                 # 设计文档和开发计划
```

---

## 四、核心数据流

### 4.1 语音指令流程

```
用户说话
  → Web Speech API（浏览器）语音识别 → 文字
  → POST /api/voice/command { text }
  → VoiceService.process_command()
    → NLUService.parse_command()
      → LLM.parse_calendar_command()  // MiMo 解析为结构化 JSON
      → 返回 { intent, entities, confidence }
    → VoiceService._execute_action()  // 根据 intent 执行
      → create: 写入 events 表
      → delete: 按标题模糊匹配删除
      → modify: 按标题找到并更新
      → query: 查询数据库返回结果
    → 记录到 voice_logs 表
  → 返回 response_text
  → MiMo TTS 语音播报结果
  → 前端自动刷新日历
```

### 4.2 事件数据流

```
前端 CalendarPage
  → useEventStore.fetchEvents(start, end)
  → eventApi.getEvents() → GET /api/events?start=&end=
  → EventService.get_events_by_date_range()
  → 返回事件列表 → FullCalendar 渲染
```

### 4.3 提醒流程

```
APScheduler 每分钟扫描
  → ReminderService.get_pending_reminders()
  → WebSocket 推送到在线用户
  → 前端 ReminderToast 弹窗 + MiMo TTS 语音播报
  → 离线用户降级为浏览器 Push Notification
```

---

## 五、功能清单

### 5.1 已完成功能（Phase 1-9）

| 阶段 | 功能 | 状态 |
|------|------|------|
| Phase 1 | 项目骨架（Docker、FastAPI、React、Alembic、健康检查） | ✅ |
| Phase 2 | 用户认证（JWT + bcrypt、登录/注册页面、AuthGuard） | ✅ |
| Phase 3 | 日历视图（FullCalendar 4 种视图、月份/周/日/列表） | ✅ |
| Phase 4 | 事件 CRUD（EventForm、EventModal、右键菜单） | ✅ |
| Phase 5 | 语音基础（SpeechRecognition、SpeechSynthesis、波形可视化） | ✅ |
| Phase 6 | AI NLU（LLM 适配器层、NLU 服务、语音指令执行、语音历史） | ✅ |
| Phase 7 | 提醒通知（Reminder 模型、WebSocket、APScheduler、Service Worker） | ✅ |
| Phase 8 | AI 智能（冲突检测、空闲推荐、每日语音摘要） | ✅ |
| Phase 9 | 增值功能（天气、节假日、统计图表、分享链接、导出 iCal） | ✅ |

### 5.2 Phase 10（待实现）

- Docker 生产部署
- Nginx 反向代理
- PWA 完整支持
- 设置页面完善
- 性能优化

---

## 六、API 接口一览

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/register | 用户注册 |
| POST | /api/auth/login | 用户登录 |
| GET | /api/auth/me | 获取当前用户信息 |

### 事件

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/events?start=&end= | 获取日期范围内的事件 |
| POST | /api/events | 创建事件 |
| GET | /api/events/{id} | 获取单个事件 |
| PUT | /api/events/{id} | 更新事件 |
| DELETE | /api/events/{id} | 删除事件 |
| GET | /api/events/search?q= | 搜索事件 |

### 语音

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/voice/command | 语音指令处理（NLU + 执行） |
| GET | /api/voice/logs | 语音指令历史 |
| GET | /api/voice/help | 语音指令帮助 |

### AI

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/ai/detect-conflicts?start_time=&end_time= | 时间冲突检测 |
| POST | /api/ai/recommend-slot?target_date=&duration_minutes= | 空闲时段推荐 |
| GET | /api/ai/daily-briefing?period=morning | 每日摘要 |
| POST | /api/ai/tts | MiMo TTS 语音合成 |

### 提醒

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/reminders?status= | 提醒列表 |
| PUT | /api/reminders/{id}/dismiss | 关闭提醒 |

### 其他

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/weather/now | 实时天气 |
| GET | /api/weather/forecast | 天气预报 |
| GET | /api/holidays?year=&month= | 节假日信息 |
| POST | /api/share/create | 生成分享链接 |
| GET | /api/share/{token} | 获取分享日程 |
| WS | /ws/reminder?token= | WebSocket 提醒推送 |

---

## 七、数据库模型

### User
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| email | String | 邮箱（唯一） |
| username | String | 用户名 |
| password_hash | String | bcrypt 密码哈希 |
| avatar_url | String? | 头像 |
| theme | String | 主题偏好 |

### Event
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID FK | 所属用户 |
| title | String | 标题 |
| description | Text? | 描述 |
| start_time | DateTime(tz) | 开始时间（UTC） |
| end_time | DateTime(tz) | 结束时间（UTC） |
| is_all_day | Boolean | 全天事件 |
| location | String? | 地点 |
| category_id | UUID FK? | 分类 |
| priority | SmallInteger | 优先级 1-5 |
| color | String? | 颜色 |

### Reminder
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| event_id | UUID FK | 关联事件 |
| user_id | UUID FK | 所属用户 |
| remind_at | DateTime(tz) | 提醒时间 |
| type | String | push / voice / both |
| status | String | pending / sent / dismissed |

### VoiceLog
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID FK | 所属用户 |
| raw_text | Text | 原始语音文本 |
| parsed_intent | String? | 解析意图 |
| parsed_entities | JSON? | 解析实体 |
| response_text | Text? | 响应文本 |

---

## 八、LLM 适配器架构

采用 **Adapter 模式**，所有 LLM 实现统一接口：

```python
class BaseLLM(ABC):
    async def chat(self, messages: list[dict], **kwargs) -> str: ...
    async def parse_calendar_command(self, text: str, context: dict | None = None) -> dict: ...
```

| 适配器 | 模型 | 说明 |
|--------|------|------|
| MiMoLLM | mimo-v2.5 | 小米 MiMo（默认，国内可用） |
| QwenLLM | qwen-turbo | 通义千问 |
| OpenAILLM | gpt-4o-mini | OpenAI |
| GLMLLM | glm-4-flash | 智谱 GLM |
| MockLLM | - | 正则匹配（开发测试用，无需 API Key） |

**切换方式：** 在 `.env` 中设置 `LLM_PROVIDER=mimo`（或 qwen/openai/glm/mock）

**自动降级：** 如果配置的 LLM 没有 API Key，自动降级为 MockLLM

---

## 九、MiMo TTS 语音合成

### API 调用

```
POST https://token-plan-cn.xiaomimimo.com/v1/chat/completions
Header: api-key: $MIMO_API_KEY
Body: {
  "model": "mimo-v2.5-tts",
  "messages": [{"role": "assistant", "content": "要合成的文本"}],
  "audio": {"format": "wav", "voice": "音色ID"}
}
Response: choices[0].message.audio.data (base64 wav)
```

### 可用音色

| 音色 | Voice ID | 语言 | 性别 |
|------|----------|------|------|
| MiMo默认 | mimo_default | 中文 | 女 |
| 冰糖 | 冰糖 | 中文 | 女 |
| 茉莉 | 茉莉 | 中文 | 女 |
| 苏打 | 苏打 | 中文 | 男 |
| 白桦 | 白桦 | 中文 | 男 |
| Mia | Mia | 英文 | 女 |
| Chloe | Chloe | 英文 | 女 |
| Milo | Milo | 英文 | 男 |
| Dean | Dean | 英文 | 男 |

### 使用位置

- 语音指令回复播报（VoicePanel）
- 提醒弹窗播报（ReminderToast）
- 每日摘要播报（DailyBriefing）
- 音色试听（VoiceSelector）

---

## 十、前端状态管理

| Store | 用途 | 持久化 |
|-------|------|--------|
| useAuthStore | 用户认证（token、用户信息） | localStorage |
| useEventStore | 日历事件（从后端 API 加载） | 否 |
| useVoiceStore | 语音识别状态（录音中、转文字） | 否 |
| useReminderStore | 提醒状态（弹窗、列表） | 否 |
| useTtsStore | TTS 音色选择 | localStorage |

---

## 十一、启动指南

### 环境要求

- Node.js 18+
- Python 3.11+
- Docker + Docker Compose

### 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/WklCD/vocal-calendar.git
cd vocal-calendar

# 2. 启动数据库
docker compose up -d postgres redis

# 3. 配置后端
cd backend
cp .env.example .env
# 编辑 .env，填入 MIMO_API_KEY

# 4. 安装后端依赖 + 运行迁移
pip install -r requirements.txt
alembic upgrade head

# 5. 启动后端
python3 -m uvicorn app.main:app --reload --port 8000

# 6. 安装前端依赖 + 启动
cd ../frontend
npm install
npm run dev
```

### 环境变量（backend/.env）

```bash
DATABASE_URL=postgresql://vocal_user:vocal_pass@localhost:5432/vocal_calendar
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key
LLM_PROVIDER=mimo
MIMO_API_KEY=your-mimo-api-key
```

---

## 十二、测试

```bash
# 后端测试（77 个）
cd backend && pytest -v

# 前端测试（37 个）
cd frontend && npx vitest run
```

---

## 十三、浏览器兼容性

| 功能 | Safari | Edge | Chrome | Firefox |
|------|--------|------|--------|---------|
| 语音识别 | ✅ | ✅ | ❌（国内不可用） | ❌ |
| 语音合成（MiMo TTS） | ✅ | ✅ | ✅ | ✅ |
| 日历/其他功能 | ✅ | ✅ | ✅ | ✅ |

**注意：** 语音识别使用 Web Speech API，Chrome 在国内使用 Google 服务器被屏蔽，推荐使用 Safari 或 Edge。

---

## 十四、已知限制和优化方向

### 已知限制

1. **天气服务使用 Mock 数据** — 需要配置和风天气 API Key 才能获取真实天气
2. **分享链接使用内存存储** — 重启后失效，生产环境应存入数据库
3. **LLM 日期理解偏差** — MiMo 可能返回错误年份（如 2024），需要后处理修正
4. **无离线支持** — Service Worker 仅用于 Push 通知，未实现完整离线缓存

### 优化方向

1. **Phase 10 部署** — Docker 生产镜像、Nginx 反向代理、HTTPS
2. **PWA 完整支持** — 离线缓存、安装提示
3. **日历事件持久化** — UI 创建的事件应同步到后端（当前仅语音创建的事件写数据库）
4. **多语言支持** — 目前仅中文界面
5. **移动端适配** — 响应式布局优化
6. **RAG 增强** — 结合用户历史事件进行更智能的 NLU 解析
