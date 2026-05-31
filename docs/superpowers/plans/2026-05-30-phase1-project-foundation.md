# Phase 1: 项目基础搭建 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从零搭建 vocal-calendar monorepo 项目骨架，包含前后端初始化、Docker 开发环境、数据库连接、Alembic 迁移、health check API。

**Architecture:** Monorepo 结构，frontend（React + Vite）和 backend（FastAPI）作为独立子目录。Docker Compose 编排 PostgreSQL + Redis + 后端服务。前端通过 Vite dev server 运行，后端通过 uvicorn 运行。

**Tech Stack:** React 18, Vite 6, TypeScript, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 16, Redis, Docker, Docker Compose

---

## File Structure

### Backend Files

| File | Responsibility |
|------|---------------|
| `backend/Dockerfile` | 后端容器镜像定义 |
| `backend/requirements.txt` | Python 依赖 |
| `backend/app/__init__.py` | 包初始化 |
| `backend/app/main.py` | FastAPI 入口，挂载路由 |
| `backend/app/core/__init__.py` | 包初始化 |
| `backend/app/core/config.py` | 应用配置（Pydantic Settings） |
| `backend/app/core/database.py` | SQLAlchemy engine + session |
| `backend/app/api/__init__.py` | 包初始化 |
| `backend/app/api/health.py` | Health check 路由 |
| `backend/alembic.ini` | Alembic 配置 |
| `backend/alembic/env.py` | Alembic 迁移环境 |
| `backend/alembic/versions/` | 迁移文件目录 |
| `backend/tests/__init__.py` | 测试包 |
| `backend/tests/conftest.py` | 测试 fixtures |
| `backend/tests/test_health.py` | Health check 测试 |

### Frontend Files

| File | Responsibility |
|------|---------------|
| `frontend/package.json` | Node 依赖 |
| `frontend/vite.config.ts` | Vite 构建配置 |
| `frontend/tsconfig.json` | TypeScript 配置 |
| `frontend/tsconfig.node.json` | Node 端 TS 配置 |
| `frontend/index.html` | HTML 入口 |
| `frontend/src/main.tsx` | React 入口 |
| `frontend/src/App.tsx` | 根组件 + 路由 |
| `frontend/src/vite-env.d.ts` | Vite 类型声明 |
| `frontend/src/styles/variables.css` | CSS 变量（主题 token） |
| `frontend/src/styles/global.css` | 全局样式 reset |

### Root Files

| File | Responsibility |
|------|---------------|
| `docker-compose.yml` | 服务编排 |
| `.gitignore` | Git 忽略规则 |
| `README.md` | 项目说明 |

---

## Task 1: 初始化 Git 仓库与项目根目录

**Files:**
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1: 创建 .gitignore**

```gitignore
# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
.venv/
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Build
dist/
build/
*.egg-info/

# Environment
.env
.env.local
.env.*.local

# Docker
docker-compose.override.yml

# Database
*.db
*.sqlite3

# Logs
*.log

# Superpowers brainstorm sessions
.superpowers/

# Coverage
htmlcov/
.coverage
coverage/
```

- [ ] **Step 2: 创建 README.md**

```markdown
# Vocal Calendar

语音驱动的日历工具，支持语音交互管理日程、AI 智能辅助、多层级提醒。

## 快速开始

### 环境要求
- Docker & Docker Compose
- Node.js 20+
- Python 3.12+

### 启动开发环境

```bash
# 启动数据库和 Redis
docker compose up -d postgres redis

# 启动后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 启动前端
cd frontend
npm install
npm run dev
```

### 运行测试

```bash
# 后端测试
cd backend
pytest -v

# 前端测试
cd frontend
npm test
```

## 技术栈

- **前端**: React 18 + Vite 6 + TypeScript + Zustand + FullCalendar
- **后端**: Python FastAPI + SQLAlchemy 2.0 + Alembic
- **数据库**: PostgreSQL 16 + Redis
- **AI**: 通义千问 / OpenAI / 智谱（可切换）
- **语音**: Web Speech API
```

- [ ] **Step 3: 初始化 Git 仓库并提交**

```bash
cd /Users/linchengda/Desktop/vocal-calendar
git init
git add .gitignore README.md
git commit -m "chore: initialize project with gitignore and readme"
```

---

## Task 2: 配置 Docker Compose 开发环境

**Files:**
- Create: `docker-compose.yml`
- Create: `backend/Dockerfile`

- [ ] **Step 1: 创建 docker-compose.yml**

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    container_name: vocal-calendar-db
    environment:
      POSTGRES_USER: vocal_user
      POSTGRES_PASSWORD: vocal_pass
      POSTGRES_DB: vocal_calendar
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U vocal_user -d vocal_calendar"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: vocal-calendar-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

- [ ] **Step 2: 创建 backend/Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 3: 启动数据库和 Redis 验证**

```bash
cd /Users/linchengda/Desktop/vocal-calendar
docker compose up -d postgres redis
docker compose ps
```

Expected: postgres 和 redis 状态为 `running`，healthcheck 通过。

- [ ] **Step 4: 提交**

```bash
git add docker-compose.yml backend/Dockerfile
git commit -m "chore: add Docker Compose with PostgreSQL and Redis"
```

---

## Task 3: 创建后端项目骨架

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/database.py`

- [ ] **Step 1: 创建 requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
alembic==1.13.2
psycopg2-binary==2.9.9
pydantic==2.9.2
pydantic-settings==2.5.2
python-dotenv==1.0.1
redis==5.1.1
```

- [ ] **Step 2: 创建 backend/app/__init__.py**

```python
```

- [ ] **Step 3: 创建 backend/app/core/__init__.py**

```python
```

- [ ] **Step 4: 创建 backend/app/core/config.py**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Vocal Calendar"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://vocal_user:vocal_pass@localhost:5432/vocal_calendar"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 5: 创建 backend/app/core/database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 6: 安装依赖并验证导入**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pip install -r requirements.txt
python -c "from app.core.config import get_settings; print(get_settings().APP_NAME)"
python -c "from app.core.database import Base, engine; print('DB OK')"
```

Expected: 输出 `Vocal Calendar` 和 `DB OK`

- [ ] **Step 7: 提交**

```bash
git add backend/
git commit -m "feat: add backend project skeleton with config and database"
```

---

## Task 4: 创建 Health Check API

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/health.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: 创建 backend/app/api/__init__.py**

```python
```

- [ ] **Step 2: 编写 health check 测试 (RED)**

创建 `backend/tests/__init__.py`：

```python
```

创建 `backend/tests/conftest.py`：

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)
```

创建 `backend/tests/test_health.py`：

```python
def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
```

- [ ] **Step 3: 运行测试确认失败 (RED)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_health.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 4: 创建 backend/app/api/health.py**

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
    }
```

- [ ] **Step 5: 创建 backend/app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api.health import router as health_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
```

- [ ] **Step 6: 运行测试确认通过 (GREEN)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_health.py -v
```

Expected: `1 passed`

- [ ] **Step 7: 手动启动服务验证**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
uvicorn app.main:app --reload --port 8000 &
sleep 2
curl http://localhost:8000/api/health
kill %1
```

Expected: `{"status":"healthy","version":"0.1.0"}`

- [ ] **Step 8: 提交**

```bash
git add backend/
git commit -m "feat: add health check API endpoint with tests"
```

---

## Task 5: 配置 Alembic 数据库迁移

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/.gitkeep`

- [ ] **Step 1: 初始化 Alembic**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
alembic init alembic
```

- [ ] **Step 2: 修改 alembic.ini 数据库连接**

编辑 `backend/alembic.ini`，找到 `sqlalchemy.url` 行，修改为：

```ini
sqlalchemy.url = postgresql://vocal_user:vocal_pass@localhost:5432/vocal_calendar
```

- [ ] **Step 3: 修改 alembic/env.py 使用应用配置**

替换 `backend/alembic/env.py` 内容为：

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# 将 backend 目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import get_settings
from app.core.database import Base

# 导入所有模型以便 Alembic 能检测到
# from app.models import user, event, reminder, voice_log  # 后续阶段添加

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: 验证 Alembic 连接数据库**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
alembic current
```

Expected: 输出当前迁移版本（应为空，因为还没有迁移文件）

- [ ] **Step 5: 创建初始迁移验证流程**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
alembic revision --autogenerate -m "initial empty migration"
alembic upgrade head
```

Expected: 迁移成功执行

- [ ] **Step 6: 提交**

```bash
git add backend/alembic.ini backend/alembic/
git commit -m "chore: configure Alembic database migrations"
```

---

## Task 6: 创建前端项目骨架

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/vite-env.d.ts`
- Create: `frontend/src/styles/variables.css`
- Create: `frontend/src/styles/global.css`

- [ ] **Step 1: 初始化 Vite 项目**

```bash
cd /Users/linchengda/Desktop/vocal-calendar
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

- [ ] **Step 2: 创建主题变量 CSS**

创建 `frontend/src/styles/variables.css`：

```css
:root {
  /* === Color Palette (Google-inspired) === */
  --color-primary: #4285F4;
  --color-primary-light: #669DF6;
  --color-primary-dark: #1A73E8;
  --color-secondary: #EA4335;
  --color-accent: #34A853;
  --color-warning: #FBBC04;

  /* Category Colors */
  --color-category-work: #4285F4;
  --color-category-personal: #34A853;
  --color-category-health: #EA4335;
  --color-category-social: #FBBC04;
  --color-category-other: #9334E6;

  /* Background */
  --color-bg: #FFFFFF;
  --color-bg-secondary: #F8F9FA;
  --color-surface: #FFFFFF;
  --color-surface-hover: #F1F3F4;

  /* Text */
  --color-text: #202124;
  --color-text-secondary: #5F6368;
  --color-text-disabled: #9AA0A6;
  --color-text-inverse: #FFFFFF;

  /* Border */
  --color-border: #DADCE0;
  --color-border-light: #E8EAED;

  /* Status */
  --color-success: #34A853;
  --color-error: #EA4335;
  --color-info: #4285F4;

  /* === Typography === */
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'Fira Code', 'Consolas', monospace;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-size-3xl: 1.875rem;

  /* === Spacing === */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;

  /* === Border Radius === */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;

  /* === Shadows === */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);

  /* === Transitions === */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
  --transition-slow: 350ms ease;

  /* === Layout === */
  --sidebar-width: 260px;
  --topbar-height: 56px;
}

[data-theme="dark"] {
  --color-bg: #1A1A2E;
  --color-bg-secondary: #16213E;
  --color-surface: #0F3460;
  --color-surface-hover: #1A4B8C;
  --color-text: #E8E8E8;
  --color-text-secondary: #A0A0A0;
  --color-text-disabled: #666666;
  --color-text-inverse: #1A1A2E;
  --color-border: #2A2A4A;
  --color-border-light: #3A3A5A;
}
```

- [ ] **Step 3: 创建全局样式**

创建 `frontend/src/styles/global.css`：

```css
@import './variables.css';

*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  color: var(--color-text);
  background-color: var(--color-bg);
  line-height: 1.6;
  min-height: 100vh;
}

a {
  color: var(--color-primary);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

button {
  cursor: pointer;
  border: none;
  outline: none;
  font-family: inherit;
}

input, textarea, select {
  font-family: inherit;
  font-size: inherit;
}

img {
  max-width: 100%;
  display: block;
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--color-bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: var(--radius-full);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-secondary);
}
```

- [ ] **Step 4: 修改 App.tsx 占位**

替换 `frontend/src/App.tsx`：

```tsx
function App() {
  return (
    <div className="app">
      <h1>Vocal Calendar</h1>
      <p>语音日历工具 — 项目已启动</p>
    </div>
  );
}

export default App;
```

- [ ] **Step 5: 修改 main.tsx 引入全局样式**

替换 `frontend/src/main.tsx`：

```tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles/global.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

- [ ] **Step 6: 删除 Vite 默认样式文件**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
rm -f src/App.css src/index.css src/assets/react.svg
```

- [ ] **Step 7: 验证前端启动**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npm run dev -- --host &
sleep 3
curl -s http://localhost:5173 | head -20
kill %1
```

Expected: HTML 内容包含 `Vocal Calendar`

- [ ] **Step 8: 提交**

```bash
git add frontend/
git commit -m "feat: add frontend skeleton with Vite, theme variables, and global styles"
```

---

## Task 7: 配置 Vite 代理到后端

**Files:**
- Modify: `frontend/vite.config.ts`

- [ ] **Step 1: 修改 vite.config.ts 添加代理**

替换 `frontend/vite.config.ts`：

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
});
```

- [ ] **Step 2: 验证代理工作**

启动后端和前端：

```bash
# Terminal 1
cd /Users/linchengda/Desktop/vocal-calendar/backend
uvicorn app.main:app --reload --port 8000 &

# Terminal 2
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npm run dev &

sleep 3

# 通过前端代理访问后端 API
curl http://localhost:5173/api/health

# Cleanup
kill %1 %2
```

Expected: `{"status":"healthy","version":"0.1.0"}`

- [ ] **Step 3: 提交**

```bash
git add frontend/vite.config.ts
git commit -m "feat: configure Vite proxy for backend API"
```

---

## Task 8: 配置前端测试环境

**Files:**
- Modify: `frontend/package.json`（添加测试依赖和脚本）
- Create: `frontend/src/__tests__/App.test.tsx`
- Create: `frontend/vitest.config.ts`

- [ ] **Step 1: 安装测试依赖**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

- [ ] **Step 2: 创建 vitest.config.ts**

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/__tests__/setup.ts',
    css: true,
  },
});
```

- [ ] **Step 3: 创建测试 setup 文件**

创建 `frontend/src/__tests__/setup.ts`：

```typescript
import '@testing-library/jest-dom';
```

- [ ] **Step 4: 编写 App 组件测试 (RED)**

创建 `frontend/src/__tests__/App.test.tsx`：

```tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from '../App';

describe('App', () => {
  it('renders the app title', () => {
    render(<App />);
    expect(screen.getByText('Vocal Calendar')).toBeInTheDocument();
  });

  it('renders the subtitle', () => {
    render(<App />);
    expect(screen.getByText(/语音日历工具/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 5: 运行测试确认通过 (GREEN)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run
```

Expected: `2 passed`

- [ ] **Step 6: 添加测试脚本到 package.json**

在 `frontend/package.json` 的 `scripts` 中添加：

```json
{
  "scripts": {
    "test": "vitest",
    "test:run": "vitest run",
    "test:coverage": "vitest run --coverage"
  }
}
```

- [ ] **Step 7: 提交**

```bash
git add frontend/
git commit -m "test: configure Vitest and add App component tests"
```

---

## Task 9: 完整验证与最终提交

- [ ] **Step 1: 验证后端所有测试通过**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest -v
```

Expected: 所有测试通过

- [ ] **Step 2: 验证前端所有测试通过**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run
```

Expected: 所有测试通过

- [ ] **Step 3: 验证 Docker 服务正常**

```bash
cd /Users/linchengda/Desktop/vocal-calendar
docker compose ps
```

Expected: postgres 和 redis 运行中

- [ ] **Step 4: 完整启动验证**

```bash
# 启动后端
cd /Users/linchengda/Desktop/vocal-calendar/backend
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# 启动前端
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npm run dev &
FRONTEND_PID=$!

sleep 5

# 验证
echo "=== Backend Health ==="
curl -s http://localhost:8000/api/health

echo ""
echo "=== Frontend via Proxy ==="
curl -s http://localhost:5173/api/health

# Cleanup
kill $BACKEND_PID $FRONTEND_PID
```

Expected: 两个 health check 都返回 `{"status":"healthy","version":"0.1.0"}`

- [ ] **Step 5: 最终提交**

```bash
git add -A
git commit -m "chore: phase 1 complete — project foundation ready"
```

---

## 阶段交付物清单

| 交付物 | 状态 |
|--------|------|
| Git 仓库初始化 | ☐ |
| Docker Compose（PostgreSQL + Redis） | ☐ |
| FastAPI 项目骨架 | ☐ |
| 应用配置（Pydantic Settings） | ☐ |
| 数据库连接（SQLAlchemy） | ☐ |
| Alembic 迁移配置 | ☐ |
| Health Check API + 测试 | ☐ |
| React + Vite 项目骨架 | ☐ |
| CSS 主题变量系统 | ☐ |
| 全局样式 Reset | ☐ |
| Vite 代理配置 | ☐ |
| Vitest 测试环境 | ☐ |
| App 组件测试 | ☐ |

## PR 提交规范提醒

每个 Task 完成后都应提交一次 commit。如果某个 Task 涉及多个独立变更，可以拆分为多个 commit。commit message 格式：
- `feat:` 新功能
- `fix:` 修复
- `test:` 测试
- `chore:` 构建/工具
- `docs:` 文档

## Git 要求提醒

- 开发周期内保持持续的 commit 记录
- 每个 commit 对应一个完整的、可运行的变更
- 使用 conventional commits 格式
