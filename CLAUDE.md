# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vocal Calendar（语音日历）— 一个语音驱动的 Web 日历工具，支持语音交互管理日程、AI 智能辅助、多层级提醒。毕设项目，界面采用活力多彩风格（Google Calendar 风格）。

## Tech Stack

- **Frontend**: React 18 + Vite 6 + TypeScript + Zustand + FullCalendar + React Router v6
- **Backend**: Python FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic v2
- **Database**: PostgreSQL 16 + Redis
- **AI**: 通义千问 / OpenAI / 智谱 GLM（可切换，Adapter 模式）
- **Voice**: Web Speech API（浏览器原生）
- **Deploy**: Docker + Docker Compose + Nginx

## Commands

### Backend

```bash
# Install dependencies
cd backend && pip install -r requirements.txt

# Run dev server
uvicorn app.main:app --reload --port 8000

# Run all tests
pytest -v

# Run single test file
pytest tests/test_auth_service.py -v

# Run single test
pytest tests/test_auth_service.py::TestLogin::test_login_success -v

# Database migrations
alembic upgrade head                    # Apply migrations
alembic revision --autogenerate -m "msg"  # Generate migration
alembic history                         # View migration history
```

### Frontend

```bash
# Install dependencies
cd frontend && npm install

# Run dev server
npm run dev

# Run all tests
npx vitest run

# Run single test file
npx vitest run src/features/auth/__tests__/LoginPage.test.tsx

# Run tests in watch mode
npx vitest

# Production build
npm run build
```

### Docker

```bash
# Start database and Redis (development)
docker compose up -d postgres redis

# Production deployment
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

## Architecture

```
frontend/                   # React SPA
  src/
    features/               # Feature modules (auth, calendar, voice, events, reminders, ai, settings)
    hooks/                  # Custom hooks (useSpeechRecognition, useSpeechSynthesis, useAudioVisualizer)
    stores/                 # Zustand stores (useAuthStore, useEventStore, useVoiceStore, useReminderStore)
    services/               # API call layer (api.ts, authApi.ts, eventApi.ts, voiceApi.ts, aiApi.ts)
    styles/                 # CSS variables, global styles, theme system
    components/             # Shared UI components

backend/                    # FastAPI API server
  app/
    api/                    # Route handlers (auth, events, categories, reminders, voice, ai, websocket)
    services/               # Business logic layer
      llm/                  # LLM abstraction: base.py → qwen.py / openai.py / glm.py + factory.py
    models/                 # SQLAlchemy models (User, Event, Category, Reminder, VoiceLog)
    schemas/                # Pydantic request/response models
    core/                   # Config, security (JWT+bcrypt), database, websocket_manager
    tasks/                  # APScheduler jobs (reminder_task, daily_briefing)
  alembic/                  # Database migrations
  tests/                    # pytest tests (unit/, integration/, e2e/)
```

**Data flow**: Frontend → REST API (or WebSocket) → Router → Service → SQLAlchemy Model → PostgreSQL. LLM calls go through the Adapter pattern (`services/llm/`), switchable via config.

**Key patterns**:
- Frontend organized by **feature modules**, each with its own components, hooks, and store slice
- Backend follows **routers → services → models** three-layer separation
- LLM layer uses **Adapter pattern** — new LLM = new adapter file + config entry
- Voice commands: Web Speech API → text → `/api/voice/command` → NLU (LLM) → execute action → response

## PR 提交规范

1. **基于 feature 分支**添加新功能，不要直接在 main 上开发
2. **每个 PR 只做一件事**：每个 PR 只实现或修改单一功能；鼓励尽可能小、粒度尽可能细的 PR；大功能应拆分为多个独立 PR 分步提交
3. **PR 标题与描述需清晰完整**：
   - **标题**：一句话说明本 PR 新增/修改了什么
   - **功能描述**：说明该功能的作用与使用方式
   - **实现思路**：简要说明技术选型或核心实现逻辑
   - **测试方式**：如何验证该功能正常运行
4. **PR 合并后**，主分支代码需保持可运行状态，评委在任意时间查看应能复现演示效果

## Git 要求

- 开发周期内保持**持续的 PR 记录和 commit 提交**
- **commit message 使用中文**，格式：`类型: 中文描述`
- 使用 **conventional commits** 格式：
  - `feat:` 新功能（例：`feat: 添加用户注册接口`）
  - `fix:` 修复 bug（例：`fix: 修复登录token过期问题`）
  - `test:` 测试相关（例：`test: 添加认证服务单元测试`）
  - `chore:` 构建/工具/配置（例：`chore: 初始化项目结构`）
  - `docs:` 文档（例：`docs: 更新API文档`）
  - `refactor:` 重构（例：`refactor: 优化数据库查询逻辑`）
- 每个 commit 对应一个完整的、可运行的变更

## Testing Requirements

- **TDD**: 严格遵循 RED → GREEN → REFACTOR 循环
- **Coverage**: 简单任务 ≥85%, 中等任务 ≥91%, 复杂任务 ≥94%
- **Mock strategy**: LLM calls mocked in all tests; Web Speech API mocked in frontend tests; time frozen with freezegun (backend) / vi.useFakeTimers (frontend)

## Design Documents

- System design: `docs/superpowers/specs/2026-05-30-vocal-calendar-design.md`
- Development plans: `docs/superpowers/plans/2026-05-30-phase{1-10}-*.md` (10 phases)
- Original requirements: `语音日历开发.md`

## Key Decisions

- Multi-user system with JWT authentication (access_token 30min, refresh_token 7d)
- Web Speech API only (no iFlytek fallback), Chrome/Edge required for voice features
- LLM switchable via Adapter pattern (Qwen primary, OpenAI/GLM alternatives)
- PostgreSQL + Redis (not SQLite), deployed via Docker
- Local development first, deploy to Alibaba Cloud ECS at the end
- All times stored in UTC, displayed in user's local timezone
