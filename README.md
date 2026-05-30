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
npx vitest run
```

## 技术栈

- **前端**: React 18 + Vite 6 + TypeScript + Zustand + FullCalendar
- **后端**: Python FastAPI + SQLAlchemy 2.0 + Alembic
- **数据库**: PostgreSQL 16 + Redis
- **AI**: 通义千问 / OpenAI / 智谱（可切换）
- **语音**: Web Speech API
