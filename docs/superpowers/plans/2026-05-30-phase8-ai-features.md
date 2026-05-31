# Phase 8: AI 智能功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 AI 智能功能，包含事件冲突检测、空闲时段推荐、每日语音播报摘要（早间/晚间），前端冲突提示 UI 和摘要展示。

**Architecture:** 后端通过查询用户事件数据库实现冲突检测和空闲推荐，调用 LLM 生成自然语言摘要和解决建议。APScheduler 定时触发每日摘要（7:30 早间、21:00 晚间），通过 WebSocket 推送到前端。

**Tech Stack:** FastAPI, SQLAlchemy, APScheduler, LLM (Qwen/OpenAI/GLM), WebSocket, React 18

---

## File Structure

### Backend

| File | Responsibility |
|------|---------------|
| `backend/app/services/ai_service.py` | AI 智能服务（冲突检测、空闲推荐、摘要） |
| `backend/app/tasks/daily_briefing.py` | 每日摘要定时任务 |
| `backend/tests/test_ai_service.py` | AI 服务测试 |

### Frontend

| File | Responsibility |
|------|---------------|
| `frontend/src/features/ai/ConflictAlert.tsx` | 冲突提示组件 |
| `frontend/src/features/ai/DailyBriefing.tsx` | 每日摘要组件 |
| `frontend/src/features/ai/FreeSlotSuggest.tsx` | 空闲时段推荐组件 |
| `frontend/src/services/aiApi.ts` | AI API 服务 |

---

## Task 1: 实现 AI Service

**Files:**
- Create: `backend/app/services/ai_service.py`
- Create: `backend/tests/test_ai_service.py`

- [ ] **Step 1: 编写 AI 服务测试 (RED)**

创建 `backend/tests/test_ai_service.py`：

```python
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.services.ai_service import AIService
from app.models.event import Event


@pytest.fixture
def db():
    return MagicMock(spec=Session)


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.chat = AsyncMock(return_value="你今天有3个会议，最早的是上午10点的项目评审。")
    return llm


@pytest.fixture
def service(db, mock_llm):
    return AIService(db=db, llm=mock_llm)


class TestConflictDetection:
    def test_detect_no_conflicts(self, service, db):
        now = datetime.now(timezone.utc)
        # Mock: no existing events
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        db.query.return_value = mock_query

        conflicts = service.detect_conflicts(
            user_id="user-1",
            start_time=now,
            end_time=now + timedelta(hours=1),
        )
        assert conflicts == []

    def test_detect_conflict(self, service, db):
        now = datetime.now(timezone.utc)
        existing = Event(
            id="event-1",
            user_id="user-1",
            title="已有会议",
            start_time=now,
            end_time=now + timedelta(hours=2),
        )
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [existing]
        db.query.return_value = mock_query

        conflicts = service.detect_conflicts(
            user_id="user-1",
            start_time=now + timedelta(minutes=30),
            end_time=now + timedelta(hours=1),
        )
        assert len(conflicts) == 1
        assert conflicts[0].id == "event-1"


class TestFreeSlotRecommendation:
    def test_recommend_empty_day(self, service, db):
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
        day_end = now.replace(hour=18, minute=0, second=0, microsecond=0)

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value = mock_query

        slots = service.recommend_free_slots(
            user_id="user-1",
            date=now.date(),
            duration_minutes=60,
        )
        assert len(slots) > 0

    def test_recommend_with_gaps(self, service, db):
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=9, minute=0, second=0, microsecond=0)

        events = [
            Event(
                start_time=day_start,
                end_time=day_start + timedelta(hours=1),
            ),
            Event(
                start_time=day_start + timedelta(hours=3),
                end_time=day_start + timedelta(hours=4),
            ),
        ]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = events
        db.query.return_value = mock_query

        slots = service.recommend_free_slots(
            user_id="user-1",
            date=now.date(),
            duration_minutes=60,
        )
        assert len(slots) >= 1


class TestDailyBriefing:
    @pytest.mark.asyncio
    async def test_generate_briefing(self, service, db):
        now = datetime.now(timezone.utc)
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [
            Event(
                title="项目评审",
                start_time=now.replace(hour=10, minute=0),
                end_time=now.replace(hour=11, minute=0),
                location="会议室A",
            ),
        ]
        db.query.return_value = mock_query

        briefing = await service.generate_daily_briefing("user-1", "morning")
        assert isinstance(briefing, str)
        assert len(briefing) > 0
```

- [ ] **Step 2: 运行测试确认失败 (RED)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_ai_service.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现 AIService**

创建 `backend/app/services/ai_service.py`：

```python
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.event import Event
from app.services.llm.base import BaseLLM


class AIService:
    def __init__(self, db: Session, llm: BaseLLM):
        self.db = db
        self.llm = llm

    def detect_conflicts(
        self, user_id: str, start_time: datetime, end_time: datetime
    ) -> list[Event]:
        """检测与指定时间段冲突的事件。"""
        return (
            self.db.query(Event)
            .filter(
                Event.user_id == user_id,
                Event.start_time < end_time,
                Event.end_time > start_time,
            )
            .all()
        )

    def recommend_free_slots(
        self, user_id: str, date: date, duration_minutes: int = 60
    ) -> list[dict]:
        """推荐指定日期的空闲时段。"""
        day_start = datetime.combine(date, datetime.min.time()).replace(
            tzinfo=timezone.utc
        ) + timedelta(hours=9)  # 9:00 AM
        day_end = datetime.combine(date, datetime.min.time()).replace(
            tzinfo=timezone.utc
        ) + timedelta(hours=18)  # 6:00 PM

        events = (
            self.db.query(Event)
            .filter(
                Event.user_id == user_id,
                Event.start_time >= day_start,
                Event.start_time <= day_end,
            )
            .order_by(Event.start_time)
            .all()
        )

        slots = []
        current = day_start
        delta = timedelta(minutes=duration_minutes)

        for event in events:
            gap = event.start_time - current
            if gap >= delta:
                slots.append({
                    "start": current.isoformat(),
                    "end": event.start_time.isoformat(),
                    "duration_minutes": int(gap.total_seconds() / 60),
                })
            current = max(current, event.end_time)

        # Check remaining time until day end
        if day_end - current >= delta:
            slots.append({
                "start": current.isoformat(),
                "end": day_end.isoformat(),
                "duration_minutes": int((day_end - current).total_seconds() / 60),
            })

        return slots

    async def generate_daily_briefing(
        self, user_id: str, period: str = "morning"
    ) -> str:
        """生成每日语音播报摘要。"""
        today = datetime.now(timezone.utc).date()

        if period == "morning":
            target_date = today
            label = "今天"
        else:
            target_date = today + timedelta(days=1)
            label = "明天"

        day_start = datetime.combine(target_date, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        day_end = day_start + timedelta(days=1)

        events = (
            self.db.query(Event)
            .filter(
                Event.user_id == user_id,
                Event.start_time >= day_start,
                Event.start_time < day_end,
            )
            .order_by(Event.start_time)
            .all()
        )

        if not events:
            return f"{label}没有安排任何事件，可以好好休息一下。"

        event_list = []
        for e in events:
            time_str = e.start_time.strftime("%H:%M")
            location = f"，地点：{e.location}" if e.location else ""
            event_list.append(f"- {time_str} {e.title}{location}")

        events_text = "\n".join(event_list)

        prompt = f"""请根据以下{label}的日程安排，生成一段简洁友好的语音播报摘要（适合语音朗读，不超过100字）：

{label}的日程：
{events_text}

请用自然、温馨的语气生成摘要，像一个贴心的助手在提醒主人。"""

        messages = [{"role": "user", "content": prompt}]
        return await self.llm.chat(messages)
```

- [ ] **Step 4: 运行测试确认通过 (GREEN)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_ai_service.py -v
```

Expected: `4 passed`

- [ ] **Step 5: 提交**

```bash
git add backend/
git commit -m "feat: add AIService with conflict detection, free slot recommendation, and daily briefing"
```

---

## Task 2: 更新 AI API 路由和定时任务

**Files:**
- Modify: `backend/app/api/ai.py`
- Create: `backend/app/tasks/daily_briefing.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 更新 AI API 路由**

替换 `backend/app/api/ai.py`：

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, date, timezone
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.ai_service import AIService
from app.services.llm.factory import create_llm

router = APIRouter(prefix="/api/ai", tags=["ai"])


def get_ai_service(db: Session = Depends(get_db)) -> AIService:
    llm = create_llm()
    return AIService(db=db, llm=llm)


@router.post("/detect-conflicts")
async def detect_conflicts(
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
):
    conflicts = ai_service.detect_conflicts(current_user.id, start_time, end_time)
    return {
        "code": 0,
        "data": {
            "has_conflicts": len(conflicts) > 0,
            "conflicts": [
                {
                    "id": e.id,
                    "title": e.title,
                    "start_time": e.start_time.isoformat(),
                    "end_time": e.end_time.isoformat(),
                }
                for e in conflicts
            ],
        },
        "message": "ok",
    }


@router.post("/recommend-slot")
async def recommend_slot(
    target_date: date = Query(...),
    duration_minutes: int = Query(60),
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
):
    slots = ai_service.recommend_free_slots(current_user.id, target_date, duration_minutes)
    return {
        "code": 0,
        "data": {"slots": slots},
        "message": "ok",
    }


@router.get("/daily-briefing")
async def daily_briefing(
    period: str = Query("morning"),
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
):
    briefing = await ai_service.generate_daily_briefing(current_user.id, period)
    return {
        "code": 0,
        "data": {"briefing": briefing, "period": period},
        "message": "ok",
    }
```

- [ ] **Step 2: 创建每日摘要定时任务**

创建 `backend/app/tasks/daily_briefing.py`：

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.database import SessionLocal
from app.core.websocket_manager import ws_manager
from app.services.ai_service import AIService
from app.services.llm.factory import create_llm
from app.models.user import User


async def send_morning_briefing():
    """每天 7:30 发送早间摘要。"""
    db = SessionLocal()
    try:
        llm = create_llm()
        ai_service = AIService(db=db, llm=llm)
        users = db.query(User).all()

        for user in users:
            try:
                briefing = await ai_service.generate_daily_briefing(user.id, "morning")
                await ws_manager.send_to_user(user.id, {
                    "type": "briefing",
                    "period": "morning",
                    "text": briefing,
                })
            except Exception as e:
                print(f"Morning briefing error for user {user.id}: {e}")
    finally:
        db.close()


async def send_evening_briefing():
    """每天 21:00 发送晚间摘要。"""
    db = SessionLocal()
    try:
        llm = create_llm()
        ai_service = AIService(db=db, llm=llm)
        users = db.query(User).all()

        for user in users:
            try:
                briefing = await ai_service.generate_daily_briefing(user.id, "evening")
                await ws_manager.send_to_user(user.id, {
                    "type": "briefing",
                    "period": "evening",
                    "text": briefing,
                })
            except Exception as e:
                print(f"Evening briefing error for user {user.id}: {e}")
    finally:
        db.close()


def register_briefing_jobs(scheduler: AsyncIOScheduler):
    """注册每日摘要定时任务。"""
    scheduler.add_job(
        send_morning_briefing,
        "cron",
        hour=7,
        minute=30,
        id="morning_briefing",
        replace_existing=True,
    )
    scheduler.add_job(
        send_evening_briefing,
        "cron",
        hour=21,
        minute=0,
        id="evening_briefing",
        replace_existing=True,
    )
```

- [ ] **Step 3: 更新 main.py 注册摘要任务**

修改 `backend/app/main.py`，更新 startup 事件：

```python
from app.tasks.daily_briefing import register_briefing_jobs

@app.on_event("startup")
async def startup_event():
    start_scheduler()
    from app.tasks.reminder_task import scheduler
    register_briefing_jobs(scheduler)
```

- [ ] **Step 4: 提交**

```bash
git add backend/
git commit -m "feat: update AI API routes and add daily briefing scheduler"
```

---

## Task 3: 创建前端 AI 组件

**Files:**
- Create: `frontend/src/services/aiApi.ts`
- Create: `frontend/src/features/ai/ConflictAlert.tsx`
- Create: `frontend/src/features/ai/DailyBriefing.tsx`
- Create: `frontend/src/features/ai/FreeSlotSuggest.tsx`

- [ ] **Step 1: 创建 aiApi**

创建 `frontend/src/services/aiApi.ts`：

```typescript
import api from './api';

export const aiApi = {
  detectConflicts: (startTime: string, endTime: string) =>
    api.post<{ code: number; data: { has_conflicts: boolean; conflicts: any[] }; message: string }>(
      `/ai/detect-conflicts?start_time=${startTime}&end_time=${endTime}`
    ),

  recommendSlot: (targetDate: string, durationMinutes: number = 60) =>
    api.post<{ code: number; data: { slots: any[] }; message: string }>(
      `/ai/recommend-slot?target_date=${targetDate}&duration_minutes=${durationMinutes}`
    ),

  getDailyBriefing: (period: string = 'morning') =>
    api.get<{ code: number; data: { briefing: string; period: string }; message: string }>(
      `/ai/daily-briefing?period=${period}`
    ),
};
```

- [ ] **Step 2: 创建 ConflictAlert**

创建 `frontend/src/features/ai/ConflictAlert.tsx`：

```tsx
interface Conflict {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
}

interface ConflictAlertProps {
  conflicts: Conflict[];
  onDismiss: () => void;
}

export default function ConflictAlert({ conflicts, onDismiss }: ConflictAlertProps) {
  if (conflicts.length === 0) return null;

  return (
    <div
      style={{
        padding: 'var(--space-4)',
        background: 'rgba(234, 67, 53, 0.1)',
        border: '1px solid var(--color-error)',
        borderRadius: 'var(--radius-lg)',
        marginBottom: 'var(--space-4)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
        <span>⚠️</span>
        <span style={{ fontWeight: 600, color: 'var(--color-error)' }}>
          时间冲突
        </span>
        <button
          onClick={onDismiss}
          style={{
            marginLeft: 'auto',
            background: 'transparent',
            padding: 'var(--space-1)',
          }}
        >
          ✕
        </button>
      </div>
      <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
        <p style={{ marginBottom: 'var(--space-2)' }}>以下事件与新事件时间重叠：</p>
        {conflicts.map((c) => (
          <div
            key={c.id}
            style={{
              padding: 'var(--space-2)',
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-md)',
              marginBottom: 'var(--space-1)',
            }}
          >
            <span style={{ fontWeight: 500 }}>{c.title}</span>
            <span style={{ marginLeft: 'var(--space-2)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-disabled)' }}>
              {new Date(c.start_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })} -
              {new Date(c.end_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 创建 DailyBriefing**

创建 `frontend/src/features/ai/DailyBriefing.tsx`：

```tsx
import { useEffect, useState } from 'react';
import { aiApi } from '../../services/aiApi';
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis';

export default function DailyBriefing() {
  const [briefing, setBriefing] = useState('');
  const [period, setPeriod] = useState<'morning' | 'evening'>('morning');
  const [loading, setLoading] = useState(true);
  const { speak, isSpeaking } = useSpeechSynthesis();

  useEffect(() => {
    const hour = new Date().getHours();
    setPeriod(hour < 12 ? 'morning' : 'evening');
  }, []);

  useEffect(() => {
    const fetchBriefing = async () => {
      try {
        setLoading(true);
        const resp = await aiApi.getDailyBriefing(period);
        setBriefing(resp.data.data.briefing);
      } catch {
        setBriefing('暂时无法获取摘要');
      } finally {
        setLoading(false);
      }
    };
    fetchBriefing();
  }, [period]);

  return (
    <div
      style={{
        padding: 'var(--space-4)',
        background: 'linear-gradient(135deg, var(--color-primary), var(--color-accent))',
        borderRadius: 'var(--radius-xl)',
        color: 'var(--color-text-inverse)',
        marginBottom: 'var(--space-4)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
        <span style={{ fontSize: 'var(--font-size-sm)', opacity: 0.9 }}>
          {period === 'morning' ? '☀️ 早间摘要' : '🌙 晚间摘要'}
        </span>
        <button
          onClick={() => speak(briefing)}
          disabled={isSpeaking || loading}
          style={{
            background: 'rgba(255,255,255,0.2)',
            borderRadius: 'var(--radius-full)',
            padding: 'var(--space-2)',
            color: 'var(--color-text-inverse)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          {isSpeaking ? '🔊 播放中...' : '🔊 播放'}
        </button>
      </div>
      {loading ? (
        <p style={{ opacity: 0.7 }}>正在生成摘要...</p>
      ) : (
        <p style={{ fontSize: 'var(--font-size-base)', lineHeight: 1.6 }}>{briefing}</p>
      )}
    </div>
  );
}
```

- [ ] **Step 4: 创建 FreeSlotSuggest**

创建 `frontend/src/features/ai/FreeSlotSuggest.tsx`：

```tsx
import { useEffect, useState } from 'react';
import { aiApi } from '../../services/aiApi';

interface Slot {
  start: string;
  end: string;
  duration_minutes: number;
}

export default function FreeSlotSuggest() {
  const [slots, setSlots] = useState<Slot[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSlots = async () => {
      try {
        const today = new Date().toISOString().split('T')[0];
        const resp = await aiApi.recommendSlot(today, 60);
        setSlots(resp.data.data.slots);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    };
    fetchSlots();
  }, []);

  if (loading) return null;
  if (slots.length === 0) return null;

  return (
    <div
      style={{
        padding: 'var(--space-4)',
        background: 'var(--color-surface)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--color-border)',
        marginBottom: 'var(--space-4)',
      }}
    >
      <h3 style={{ fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-3)', color: 'var(--color-accent)' }}>
        💡 推荐空闲时段
      </h3>
      <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
        {slots.slice(0, 4).map((slot, index) => (
          <button
            key={index}
            style={{
              padding: 'var(--space-2) var(--space-3)',
              background: 'rgba(52, 168, 83, 0.1)',
              border: '1px solid var(--color-accent)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-accent)',
              cursor: 'pointer',
            }}
          >
            {new Date(slot.start).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })} -
            {new Date(slot.end).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
            <span style={{ marginLeft: 'var(--space-1)', opacity: 0.7 }}>
              ({slot.duration_minutes}分钟)
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 5: 提交**

```bash
git add frontend/
git commit -m "feat: add ConflictAlert, DailyBriefing, and FreeSlotSuggest AI components"
```

---

## Task 4: 集成 AI 组件到日历页面

**Files:**
- Modify: `frontend/src/features/calendar/CalendarPage.tsx`

- [ ] **Step 1: 导入 AI 组件**

修改 `frontend/src/features/calendar/CalendarPage.tsx`，添加导入：

```tsx
import DailyBriefing from '../ai/DailyBriefing';
import FreeSlotSuggest from '../ai/FreeSlotSuggest';
```

在 `<main>` 标签内的 `<CalendarView />` 前添加：

```tsx
<DailyBriefing />
<FreeSlotSuggest />
```

- [ ] **Step 2: 运行全部前端测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run
```

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add frontend/
git commit -m "feat: integrate AI components into calendar page"
```

---

## Task 5: 完整验证

- [ ] **Step 1: 后端测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest -v --tb=short
```

Expected: 所有测试通过

- [ ] **Step 2: 前端测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run
```

Expected: 所有测试通过

- [ ] **Step 3: 手动验证**

1. 登录 → 日历页面显示早间/晚间摘要卡片
2. 点击播放按钮 → 语音播报摘要
3. 创建事件时检测冲突 → 冲突提示显示
4. 空闲时段推荐显示

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "chore: phase 8 complete — AI smart features (conflicts, briefing, slots)"
```

---

## 阶段交付物清单

| 交付物 | 状态 |
|--------|------|
| AIService（冲突检测、空闲推荐、摘要） | ☐ |
| AI API 路由更新 | ☐ |
| 每日摘要定时任务 | ☐ |
| 前端 aiApi | ☐ |
| ConflictAlert 组件 | ☐ |
| DailyBriefing 组件 | ☐ |
| FreeSlotSuggest 组件 | ☐ |
| 日历页面集成 | ☐ |
