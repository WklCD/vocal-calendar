# Phase 7: 提醒与通知系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现完整的提醒与通知系统，包含 Reminder 模型、APScheduler 定时扫描、WebSocket 实时推送、浏览器 Push Notification、语音播报提醒、多层级提醒设置。

**Architecture:** 后端 APScheduler 每分钟扫描 reminders 表，对到时提醒通过 WebSocket 推送给在线用户，离线用户降级为浏览器 Push Notification。前端 ReminderToast 组件展示提醒弹窗，支持语音播报。Service Worker 处理后台 Push。

**Tech Stack:** APScheduler, FastAPI WebSocket, webpush (pywebpush), Service Worker, VAPID, React 18, Zustand

---

## File Structure

### Backend

| File | Responsibility |
|------|---------------|
| `backend/app/models/reminder.py` | Reminder SQLAlchemy 模型 |
| `backend/app/schemas/reminder.py` | Reminder Pydantic Schema |
| `backend/app/services/reminder_service.py` | Reminder 业务逻辑 |
| `backend/app/tasks/reminder_task.py` | APScheduler 定时任务 |
| `backend/app/api/reminders.py` | Reminder API 路由 |
| `backend/app/api/websocket.py` | WebSocket 管理 |
| `backend/app/core/websocket_manager.py` | WebSocket 连接管理器 |

### Frontend

| File | Responsibility |
|------|---------------|
| `frontend/src/features/reminders/ReminderToast.tsx` | 提醒弹窗组件 |
| `frontend/src/features/reminders/ReminderSettings.tsx` | 提醒设置组件 |
| `frontend/src/services/reminderApi.ts` | 提醒 API 服务 |
| `frontend/src/services/pushService.ts` | Push Notification 服务 |
| `frontend/src/services/wsService.ts` | WebSocket 服务 |
| `frontend/src/stores/useReminderStore.ts` | 提醒状态管理 |
| `frontend/public/sw.js` | Service Worker |
| `frontend/public/manifest.json` | PWA manifest（基础） |

---

## Task 1: 创建 Reminder 模型和 Schema

**Files:**
- Create: `backend/app/models/reminder.py`
- Create: `backend/app/schemas/reminder.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 创建 Reminder 模型**

创建 `backend/app/models/reminder.py`：

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    remind_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(20), default="push")  # push / voice / both
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending / sent / dismissed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    event = relationship("Event", backref="reminders")
```

- [ ] **Step 2: 创建 Reminder Schema**

创建 `backend/app/schemas/reminder.py`：

```python
from pydantic import BaseModel
from datetime import datetime


class ReminderCreateRequest(BaseModel):
    event_id: str
    remind_at: datetime
    type: str = "push"


class ReminderResponse(BaseModel):
    id: str
    event_id: str
    user_id: str
    remind_at: datetime
    type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReminderDismissRequest(BaseModel):
    reminder_id: str
```

- [ ] **Step 3: 更新 models/__init__.py**

修改 `backend/app/models/__init__.py`：

```python
from app.models.user import User
from app.models.event import Event
from app.models.category import Category
from app.models.voice_log import VoiceLog
from app.models.reminder import Reminder

__all__ = ["User", "Event", "Category", "VoiceLog", "Reminder"]
```

- [ ] **Step 4: 生成迁移**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
alembic revision --autogenerate -m "create reminders table"
alembic upgrade head
```

- [ ] **Step 5: 提交**

```bash
git add backend/
git commit -m "feat: add Reminder model, schema, and migration"
```

---

## Task 2: 实现 WebSocket 管理器

**Files:**
- Create: `backend/app/core/websocket_manager.py`
- Create: `backend/app/api/websocket.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建 WebSocket 管理器**

创建 `backend/app/core/websocket_manager.py`：

```python
import json
from fastapi import WebSocket
from typing import Dict, Set


class WebSocketManager:
    """管理 WebSocket 连接，支持按用户推送消息。"""

    def __init__(self):
        # user_id -> set of WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]

    def is_connected(self, user_id: str) -> bool:
        return user_id in self._connections and len(self._connections[user_id]) > 0

    async def send_to_user(self, user_id: str, message: dict) -> bool:
        """向指定用户发送消息。返回是否成功。"""
        if not self.is_connected(user_id):
            return False

        connections = self._connections.get(user_id, set()).copy()
        disconnected = set()

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)

        # Clean up disconnected
        for ws in disconnected:
            self.disconnect(user_id, ws)

        return len(disconnected) < len(connections)

    async def broadcast(self, message: dict):
        """向所有连接广播消息。"""
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, message)


# Global instance
ws_manager = WebSocketManager()
```

- [ ] **Step 2: 创建 WebSocket 路由**

创建 `backend/app/api/websocket.py`：

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.websocket_manager import ws_manager
from app.core.security import decode_token

router = APIRouter()


@router.websocket("/ws/reminder")
async def reminder_websocket(
    websocket: WebSocket,
    token: str = Query(...),
):
    # Authenticate
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001, reason="Unauthorized")
        return

    user_id = payload["sub"]
    await ws_manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            # Handle client messages (e.g., ack)
            if data.get("type") == "ack":
                reminder_id = data.get("reminder_id")
                # Could mark reminder as acknowledged here
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
```

- [ ] **Step 3: 注册 WebSocket 路由**

修改 `backend/app/main.py`，添加：

```python
from app.api.websocket import router as ws_router

app.include_router(ws_router)
```

- [ ] **Step 4: 提交**

```bash
git add backend/
git commit -m "feat: add WebSocket manager and reminder websocket endpoint"
```

---

## Task 3: 实现 Reminder Service 和定时任务

**Files:**
- Create: `backend/app/services/reminder_service.py`
- Create: `backend/app/tasks/reminder_task.py`
- Create: `backend/app/api/reminders.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建 ReminderService**

创建 `backend/app/services/reminder_service.py`：

```python
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.reminder import Reminder
from app.models.event import Event
from app.core.websocket_manager import ws_manager


class ReminderService:
    def __init__(self, db: Session):
        self.db = db

    def create_reminder(
        self, event_id: str, user_id: str, remind_at: datetime, reminder_type: str = "push"
    ) -> Reminder:
        reminder = Reminder(
            event_id=event_id,
            user_id=user_id,
            remind_at=remind_at,
            type=reminder_type,
        )
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)
        return reminder

    def create_reminders_for_event(
        self, event: Event, offsets: list[dict]
    ) -> list[Reminder]:
        """为事件创建多个提醒。

        Args:
            event: Event 对象
            offsets: 提醒偏移量列表，例如 [{"offset": -10, "unit": "minutes"}, ...]
        """
        reminders = []
        for offset_config in offsets:
            offset = offset_config.get("offset", 0)
            unit = offset_config.get("unit", "minutes")

            if unit == "minutes":
                delta = timedelta(minutes=offset)
            elif unit == "hours":
                delta = timedelta(hours=offset)
            elif unit == "days":
                delta = timedelta(days=offset)
            else:
                delta = timedelta(minutes=offset)

            remind_at = event.start_time + delta
            if remind_at > datetime.now(timezone.utc):
                reminder = self.create_reminder(
                    event_id=event.id,
                    user_id=event.user_id,
                    remind_at=remind_at,
                )
                reminders.append(reminder)

        return reminders

    def get_pending_reminders(self) -> list[Reminder]:
        """获取所有待处理且已到时间的提醒。"""
        now = datetime.now(timezone.utc)
        return (
            self.db.query(Reminder)
            .filter(
                Reminder.status == "pending",
                Reminder.remind_at <= now,
            )
            .all()
        )

    def get_user_reminders(self, user_id: str, status: str | None = None) -> list[Reminder]:
        """获取用户的提醒列表。"""
        query = self.db.query(Reminder).filter(Reminder.user_id == user_id)
        if status:
            query = query.filter(Reminder.status == status)
        return query.order_by(Reminder.remind_at.desc()).all()

    def dismiss_reminder(self, reminder_id: str, user_id: str) -> Reminder:
        """关闭提醒。"""
        reminder = (
            self.db.query(Reminder)
            .filter(Reminder.id == reminder_id, Reminder.user_id == user_id)
            .first()
        )
        if not reminder:
            raise ValueError("提醒不存在")

        reminder.status = "dismissed"
        self.db.commit()
        return reminder

    async def process_pending_reminders(self):
        """处理所有待发送的提醒。"""
        pending = self.get_pending_reminders()

        for reminder in pending:
            # Try WebSocket push
            sent = await ws_manager.send_to_user(reminder.user_id, {
                "type": "reminder",
                "reminder_id": reminder.id,
                "event_id": reminder.event_id,
                "title": reminder.event.title if reminder.event else "",
                "remind_at": reminder.remind_at.isoformat(),
            })

            # Update status
            reminder.status = "sent"
            self.db.commit()
```

- [ ] **Step 2: 创建定时任务**

创建 `backend/app/tasks/reminder_task.py`：

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.database import SessionLocal
from app.services.reminder_service import ReminderService

scheduler = AsyncIOScheduler()


async def check_reminders():
    """每分钟检查并发送到期提醒。"""
    db = SessionLocal()
    try:
        service = ReminderService(db)
        await service.process_pending_reminders()
    except Exception as e:
        print(f"Reminder task error: {e}")
    finally:
        db.close()


def start_scheduler():
    """启动定时任务调度器。"""
    scheduler.add_job(
        check_reminders,
        "interval",
        minutes=1,
        id="check_reminders",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler():
    """停止调度器。"""
    if scheduler.running:
        scheduler.shutdown()
```

- [ ] **Step 3: 创建 Reminder API 路由**

创建 `backend/app/api/reminders.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.reminder import ReminderResponse
from app.services.reminder_service import ReminderService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.get("")
def get_reminders(
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ReminderService(db)
    reminders = service.get_user_reminders(current_user.id, status)
    return {
        "code": 0,
        "data": [ReminderResponse.from_orm(r) for r in reminders],
        "message": "ok",
    }


@router.put("/{reminder_id}/dismiss")
def dismiss_reminder(
    reminder_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ReminderService(db)
    try:
        reminder = service.dismiss_reminder(reminder_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"code": 0, "data": ReminderResponse.from_orm(reminder), "message": "已关闭"}
```

- [ ] **Step 4: 注册路由并启动调度器**

修改 `backend/app/main.py`，添加：

```python
from app.api.reminders import router as reminders_router
from app.tasks.reminder_task import start_scheduler, stop_scheduler

app.include_router(reminders_router)

@app.on_event("startup")
async def startup_event():
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()
```

- [ ] **Step 5: 安装 APScheduler**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pip install apscheduler
echo "apscheduler==3.10.4" >> requirements.txt
```

- [ ] **Step 6: 提交**

```bash
git add backend/
git commit -m "feat: add ReminderService, APScheduler task, and reminder API"
```

---

## Task 4: 创建前端 WebSocket 和提醒服务

**Files:**
- Create: `frontend/src/services/wsService.ts`
- Create: `frontend/src/services/pushService.ts`
- Create: `frontend/src/services/reminderApi.ts`
- Create: `frontend/src/stores/useReminderStore.ts`

- [ ] **Step 1: 创建 WebSocket 服务**

创建 `frontend/src/services/wsService.ts`：

```typescript
type MessageHandler = (data: any) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000;

  connect(token: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    this.ws = new WebSocket(`${protocol}//${host}/ws/reminder?token=${token}`);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const type = data.type;
        const handlers = this.handlers.get(type);
        if (handlers) {
          handlers.forEach((handler) => handler(data));
        }
      } catch (e) {
        console.error('WebSocket message parse error:', e);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.tryReconnect(token);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private tryReconnect(token: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    setTimeout(() => this.connect(token), delay);
  }

  on(type: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);

    return () => {
      this.handlers.get(type)?.delete(handler);
    };
  }

  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const wsService = new WebSocketService();
```

- [ ] **Step 2: 创建 Push Notification 服务**

创建 `frontend/src/services/pushService.ts`：

```typescript
const VAPID_PUBLIC_KEY = 'YOUR_VAPID_PUBLIC_KEY'; // 从后端获取

export const pushService = {
  async requestPermission(): Promise<boolean> {
    if (!('Notification' in window)) {
      console.warn('Browser does not support notifications');
      return false;
    }

    const permission = await Notification.requestPermission();
    return permission === 'granted';
  },

  async registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
    if (!('serviceWorker' in navigator)) {
      console.warn('Browser does not support service workers');
      return null;
    }

    try {
      const registration = await navigator.serviceWorker.register('/sw.js');
      return registration;
    } catch (error) {
      console.error('Service Worker registration failed:', error);
      return null;
    }
  },

  async subscribe(registration: ServiceWorkerRegistration): Promise<PushSubscription | null> {
    try {
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: VAPID_PUBLIC_KEY,
      });
      return subscription;
    } catch (error) {
      console.error('Push subscription failed:', error);
      return null;
    }
  },

  showNotification(title: string, body: string, options?: NotificationOptions): void {
    if (Notification.permission === 'granted') {
      new Notification(title, {
        body,
        icon: '/calendar-icon.png',
        badge: '/calendar-icon.png',
        ...options,
      });
    }
  },
};
```

- [ ] **Step 3: 创建 reminderApi**

创建 `frontend/src/services/reminderApi.ts`：

```typescript
import api from './api';

interface Reminder {
  id: string;
  event_id: string;
  user_id: string;
  remind_at: string;
  type: string;
  status: string;
  created_at: string;
}

export const reminderApi = {
  getReminders: (status?: string) => {
    const params = status ? `?status=${status}` : '';
    return api.get<{ code: number; data: Reminder[]; message: string }>(
      `/reminders${params}`
    );
  },

  dismissReminder: (reminderId: string) =>
    api.put<{ code: number; data: Reminder; message: string }>(
      `/reminders/${reminderId}/dismiss`
    ),
};
```

- [ ] **Step 4: 创建 useReminderStore**

创建 `frontend/src/stores/useReminderStore.ts`：

```typescript
import { create } from 'zustand';
import { reminderApi } from '../services/reminderApi';

interface Reminder {
  id: string;
  event_id: string;
  title?: string;
  remind_at: string;
  type: string;
  status: string;
}

interface ReminderState {
  reminders: Reminder[];
  activeReminder: Reminder | null;
  isToastVisible: boolean;

  fetchReminders: () => Promise<void>;
  dismissReminder: (id: string) => Promise<void>;
  showToast: (reminder: Reminder) => void;
  hideToast: () => void;
}

export const useReminderStore = create<ReminderState>((set, get) => ({
  reminders: [],
  activeReminder: null,
  isToastVisible: false,

  fetchReminders: async () => {
    try {
      const resp = await reminderApi.getReminders('pending');
      set({ reminders: resp.data.data });
    } catch {
      // Handle error
    }
  },

  dismissReminder: async (id: string) => {
    try {
      await reminderApi.dismissReminder(id);
      set((state) => ({
        reminders: state.reminders.filter((r) => r.id !== id),
        activeReminder: state.activeReminder?.id === id ? null : state.activeReminder,
        isToastVisible: state.activeReminder?.id === id ? false : state.isToastVisible,
      }));
    } catch {
      // Handle error
    }
  },

  showToast: (reminder) => {
    set({ activeReminder: reminder, isToastVisible: true });
  },

  hideToast: () => {
    set({ isToastVisible: false });
  },
}));
```

- [ ] **Step 5: 提交**

```bash
git add frontend/
git commit -m "feat: add WebSocket, Push, and reminder services with store"
```

---

## Task 5: 创建前端提醒组件

**Files:**
- Create: `frontend/src/features/reminders/ReminderToast.tsx`
- Create: `frontend/public/sw.js`
- Create: `frontend/public/manifest.json`

- [ ] **Step 1: 创建 ReminderToast**

创建 `frontend/src/features/reminders/ReminderToast.tsx`：

```tsx
import { useEffect } from 'react';
import { useReminderStore } from '../../stores/useReminderStore';
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis';

export default function ReminderToast() {
  const { activeReminder, isToastVisible, hideToast, dismissReminder } =
    useReminderStore();
  const { speak } = useSpeechSynthesis();

  useEffect(() => {
    if (isToastVisible && activeReminder) {
      // Auto-speak if voice type
      if (activeReminder.type === 'voice' || activeReminder.type === 'both') {
        speak(`提醒：${activeReminder.title || '你有一个事件'}`);
      }
    }
  }, [isToastVisible, activeReminder, speak]);

  if (!isToastVisible || !activeReminder) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 'var(--space-4)',
        right: 'var(--space-4)',
        zIndex: 2000,
        background: 'var(--color-surface)',
        borderRadius: 'var(--radius-xl)',
        boxShadow: 'var(--shadow-xl)',
        border: '1px solid var(--color-border)',
        padding: 'var(--space-5)',
        width: '320px',
        animation: 'slideIn 0.3s ease',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-3)' }}>
        <span style={{ fontSize: '1.5rem' }}>🔔</span>
        <div style={{ flex: 1 }}>
          <h4 style={{ marginBottom: 'var(--space-1)', fontSize: 'var(--font-size-base)' }}>
            提醒
          </h4>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
            {activeReminder.title || '你有一个即将到来的事件'}
          </p>
          <p style={{ color: 'var(--color-text-disabled)', fontSize: 'var(--font-size-xs)', marginTop: 'var(--space-1)' }}>
            {new Date(activeReminder.remind_at).toLocaleString('zh-CN')}
          </p>
        </div>
        <button
          onClick={hideToast}
          style={{
            background: 'transparent',
            padding: 'var(--space-1)',
            fontSize: 'var(--font-size-lg)',
          }}
        >
          ✕
        </button>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-4)' }}>
        <button
          onClick={() => {
            dismissReminder(activeReminder.id);
          }}
          style={{
            flex: 1,
            padding: 'var(--space-2)',
            background: 'transparent',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          关闭
        </button>
        <button
          onClick={() => {
            hideToast();
          }}
          style={{
            flex: 1,
            padding: 'var(--space-2)',
            background: 'var(--color-primary)',
            color: 'var(--color-text-inverse)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-size-sm)',
            fontWeight: 600,
          }}
        >
          知道了
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 创建 Service Worker**

创建 `frontend/public/sw.js`：

```javascript
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};

  const options = {
    body: data.body || '你有一个提醒',
    icon: '/calendar-icon.png',
    badge: '/calendar-icon.png',
    vibrate: [200, 100, 200],
    data: data,
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'Vocal Calendar', options)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      if (clientList.length > 0) {
        return clientList[0].focus();
      }
      return clients.openWindow('/');
    })
  );
});
```

- [ ] **Step 3: 创建 PWA manifest**

创建 `frontend/public/manifest.json`：

```json
{
  "name": "Vocal Calendar",
  "short_name": "VocalCal",
  "description": "语音驱动的日历工具",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#FFFFFF",
  "theme_color": "#4285F4",
  "icons": [
    {
      "src": "/calendar-icon.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/calendar-icon.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

- [ ] **Step 4: 集成 ReminderToast 到 CalendarPage**

修改 `frontend/src/features/calendar/CalendarPage.tsx`，添加：

```tsx
import ReminderToast from '../reminders/ReminderToast';
```

在 `<VoicePanel />` 前添加：

```tsx
<ReminderToast />
```

- [ ] **Step 5: 添加滑入动画到全局样式**

在 `frontend/src/styles/global.css` 末尾添加：

```css
@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
```

- [ ] **Step 6: 提交**

```bash
git add frontend/
git commit -m "feat: add ReminderToast, Service Worker, and PWA manifest"
```

---

## Task 6: 完整验证

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

1. 创建事件并设置提醒（提前 1 分钟）
2. 等待提醒触发 → Toast 弹窗显示
3. 浏览器通知权限请求 → 允许
4. 关闭提醒 → 提醒状态更新

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "chore: phase 7 complete — reminder and notification system"
```

---

## 阶段交付物清单

| 交付物 | 状态 |
|--------|------|
| Reminder 模型 + 迁移 | ☐ |
| Reminder Schema | ☐ |
| WebSocket 管理器 | ☐ |
| WebSocket 路由 | ☐ |
| ReminderService | ☐ |
| APScheduler 定时任务 | ☐ |
| Reminder API 路由 | ☐ |
| 前端 WebSocket 服务 | ☐ |
| Push Notification 服务 | ☐ |
| reminderApi | ☐ |
| useReminderStore | ☐ |
| ReminderToast 组件 | ☐ |
| Service Worker | ☐ |
| PWA manifest | ☐ |
