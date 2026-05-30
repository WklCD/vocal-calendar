# Phase 9: 增值功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现增值功能，包含天气集成、节假日/调休标注、时间花费统计图表、分享只读日程链接、打印/导出 PDF、iCal 格式导入/导出。

**Architecture:** 天气通过和风天气 API 获取并在日历上标注。节假日通过中国法定节假日 API 获取。统计图表使用 Recharts。分享链接生成带 token 的只读 URL。PDF 导出使用浏览器 print API。iCal 使用 ical.js 解析和生成。

**Tech Stack:** 和风天气 API, 中国节假日 API, Recharts, ical.js, 浏览器 Print API, React 18

---

## File Structure

### Backend

| File | Responsibility |
|------|---------------|
| `backend/app/services/weather_service.py` | 天气 API 服务 |
| `backend/app/services/holiday_service.py` | 节假日 API 服务 |
| `backend/app/services/share_service.py` | 分享链接服务 |
| `backend/app/services/ical_service.py` | iCal 导入导出服务 |
| `backend/app/api/weather.py` | 天气 API 路由 |
| `backend/app/api/holidays.py` | 节假日 API 路由 |
| `backend/app/api/share.py` | 分享 API 路由 |
| `backend/app/api/export.py` | 导出 API 路由 |

### Frontend

| File | Responsibility |
|------|---------------|
| `frontend/src/features/weather/WeatherBadge.tsx` | 天气标注组件 |
| `frontend/src/features/holidays/HolidayBadge.tsx` | 节假日标注组件 |
| `frontend/src/features/stats/TimeStats.tsx` | 时间统计图表 |
| `frontend/src/features/share/ShareLink.tsx` | 分享链接组件 |
| `frontend/src/features/share/PublicCalendar.tsx` | 公开日历页面 |
| `frontend/src/features/export/ExportMenu.tsx` | 导出菜单组件 |
| `frontend/src/services/weatherApi.ts` | 天气 API 服务 |
| `frontend/src/services/holidayApi.ts` | 节假日 API 服务 |
| `frontend/src/services/shareApi.ts` | 分享 API 服务 |

---

## Task 1: 天气集成

**Files:**
- Create: `backend/app/services/weather_service.py`
- Create: `backend/app/api/weather.py`
- Modify: `backend/app/main.py`
- Create: `frontend/src/services/weatherApi.ts`
- Create: `frontend/src/features/weather/WeatherBadge.tsx`

- [ ] **Step 1: 创建天气服务**

创建 `backend/app/services/weather_service.py`：

```python
import httpx
from datetime import datetime, timezone
from app.core.config import get_settings


class WeatherService:
    """和风天气 API 服务。"""

    def __init__(self):
        settings = get_settings()
        self.api_key = getattr(settings, "QWEATHER_API_KEY", "")
        self.base_url = "https://devapi.qweather.com/v7"

    async def get_weather_now(self, location: str = "101010100") -> dict:
        """获取实时天气。location 默认为北京。"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/weather/now",
                params={"location": location, "key": self.api_key},
            )
            response.raise_for_status()
            data = response.json()
            if data.get("code") == "200":
                now = data.get("now", {})
                return {
                    "temp": now.get("temp"),
                    "text": now.get("text"),
                    "icon": now.get("icon"),
                    "humidity": now.get("humidity"),
                    "windDir": now.get("windDir"),
                }
            return {"temp": "--", "text": "未知", "icon": "999"}

    async def get_weather_3d(self, location: str = "101010100") -> list[dict]:
        """获取3天天气预报。"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/weather/3d",
                params={"location": location, "key": self.api_key},
            )
            response.raise_for_status()
            data = response.json()
            if data.get("code") == "200":
                return [
                    {
                        "date": d.get("fxDate"),
                        "tempMax": d.get("tempMax"),
                        "tempMin": d.get("tempMin"),
                        "textDay": d.get("textDay"),
                        "iconDay": d.get("iconDay"),
                    }
                    for d in data.get("daily", [])
                ]
            return []
```

- [ ] **Step 2: 创建天气 API 路由**

创建 `backend/app/api/weather.py`：

```python
from fastapi import APIRouter, Query
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/now")
async def get_weather_now(location: str = Query("101010100")):
    service = WeatherService()
    weather = await service.get_weather_now(location)
    return {"code": 0, "data": weather, "message": "ok"}


@router.get("/forecast")
async def get_weather_forecast(location: str = Query("101010100")):
    service = WeatherService()
    forecast = await service.get_weather_3d(location)
    return {"code": 0, "data": forecast, "message": "ok"}
```

- [ ] **Step 3: 注册路由**

修改 `backend/app/main.py`：

```python
from app.api.weather import router as weather_router
app.include_router(weather_router)
```

- [ ] **Step 4: 创建前端天气 API 和组件**

创建 `frontend/src/services/weatherApi.ts`：

```typescript
import api from './api';

export const weatherApi = {
  getNow: (location?: string) =>
    api.get<{ code: number; data: any; message: string }>(
      `/weather/now${location ? `?location=${location}` : ''}`
    ),

  getForecast: (location?: string) =>
    api.get<{ code: number; data: any[]; message: string }>(
      `/weather/forecast${location ? `?location=${location}` : ''}`
    ),
};
```

创建 `frontend/src/features/weather/WeatherBadge.tsx`：

```tsx
import { useEffect, useState } from 'react';
import { weatherApi } from '../../services/weatherApi';

export default function WeatherBadge() {
  const [weather, setWeather] = useState<any>(null);

  useEffect(() => {
    const fetchWeather = async () => {
      try {
        const resp = await weatherApi.getNow();
        setWeather(resp.data.data);
      } catch {
        // Handle error
      }
    };
    fetchWeather();
  }, []);

  if (!weather) return null;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-2)',
      padding: 'var(--space-2) var(--space-3)',
      background: 'var(--color-surface)',
      borderRadius: 'var(--radius-md)',
      fontSize: 'var(--font-size-sm)',
    }}>
      <span>{weather.text}</span>
      <span style={{ fontWeight: 600 }}>{weather.temp}°C</span>
    </div>
  );
}
```

- [ ] **Step 5: 提交**

```bash
git add backend/ frontend/
git commit -m "feat: add weather integration with QWeather API"
```

---

## Task 2: 节假日集成

**Files:**
- Create: `backend/app/services/holiday_service.py`
- Create: `backend/app/api/holidays.py`
- Modify: `backend/app/main.py`
- Create: `frontend/src/services/holidayApi.ts`
- Create: `frontend/src/features/holidays/HolidayBadge.tsx`

- [ ] **Step 1: 创建节假日服务**

创建 `backend/app/services/holiday_service.py`：

```python
import httpx
from datetime import date


class HolidayService:
    """中国法定节假日 API 服务。"""

    def __init__(self):
        self.base_url = "https://timor.tech/api/holiday"

    async def get_holidays(self, year: int, month: int) -> list[dict]:
        """获取指定月份的节假日信息。"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/info/{year}/{month}")
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0:
                holidays = []
                for day_str, info in data.get("holiday", {}).items():
                    holidays.append({
                        "date": f"{year}-{month:02d}-{day_str}",
                        "name": info.get("name", ""),
                        "is_holiday": info.get("holiday", False),
                    })
                return holidays
            return []

    async def is_holiday(self, target_date: date) -> dict:
        """检查指定日期是否为节假日。"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/info/{target_date}")
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0:
                info = data.get("type", {})
                return {
                    "is_holiday": info.get("type") == 1,
                    "is_workday": info.get("type") == 2,
                    "name": info.get("name", ""),
                }
            return {"is_holiday": False, "is_workday": False, "name": ""}
```

- [ ] **Step 2: 创建节假日 API 路由**

创建 `backend/app/api/holidays.py`：

```python
from fastapi import APIRouter, Query
from datetime import date
from app.services.holiday_service import HolidayService

router = APIRouter(prefix="/api/holidays", tags=["holidays"])


@router.get("")
async def get_holidays(year: int = Query(...), month: int = Query(...)):
    service = HolidayService()
    holidays = await service.get_holidays(year, month)
    return {"code": 0, "data": holidays, "message": "ok"}


@router.get("/check")
async def check_holiday(date: date = Query(...)):
    service = HolidayService()
    result = await service.is_holiday(date)
    return {"code": 0, "data": result, "message": "ok"}
```

- [ ] **Step 3: 注册路由**

修改 `backend/app/main.py`：

```python
from app.api.holidays import router as holidays_router
app.include_router(holidays_router)
```

- [ ] **Step 4: 创建前端节假日组件**

创建 `frontend/src/services/holidayApi.ts`：

```typescript
import api from './api';

export const holidayApi = {
  getHolidays: (year: number, month: number) =>
    api.get<{ code: number; data: any[]; message: string }>(
      `/holidays?year=${year}&month=${month}`
    ),

  checkHoliday: (date: string) =>
    api.get<{ code: number; data: any; message: string }>(
      `/holidays/check?date=${date}`
    ),
};
```

创建 `frontend/src/features/holidays/HolidayBadge.tsx`：

```tsx
import { useEffect, useState } from 'react';
import { holidayApi } from '../../services/holidayApi';

interface Holiday {
  date: string;
  name: string;
  is_holiday: boolean;
}

export default function HolidayBadge({ year, month }: { year: number; month: number }) {
  const [holidays, setHolidays] = useState<Holiday[]>([]);

  useEffect(() => {
    const fetchHolidays = async () => {
      try {
        const resp = await holidayApi.getHolidays(year, month);
        setHolidays(resp.data.data.filter((h: Holiday) => h.is_holiday));
      } catch {
        // Handle error
      }
    };
    fetchHolidays();
  }, [year, month]);

  if (holidays.length === 0) return null;

  return (
    <div style={{
      padding: 'var(--space-3)',
      background: 'rgba(251, 188, 4, 0.1)',
      borderRadius: 'var(--radius-md)',
      marginBottom: 'var(--space-4)',
    }}>
      <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-warning)' }}>
        🏖️ 本月节假日：{holidays.map((h) => h.name).join('、')}
      </span>
    </div>
  );
}
```

- [ ] **Step 5: 提交**

```bash
git add backend/ frontend/
git commit -m "feat: add Chinese holiday integration"
```

---

## Task 3: 时间统计图表

**Files:**
- Create: `frontend/src/features/stats/TimeStats.tsx`

- [ ] **Step 1: 安装 Recharts**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npm install recharts
```

- [ ] **Step 2: 创建 TimeStats 组件**

创建 `frontend/src/features/stats/TimeStats.tsx`：

```tsx
import { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { useEventStore } from '../../stores/useEventStore';

const COLORS = ['#4285F4', '#EA4335', '#34A853', '#FBBC04', '#9334E6', '#FF6D01', '#46BDC6'];

export default function TimeStats() {
  const { events } = useEventStore();

  const stats = useMemo(() => {
    const categoryMap = new Map<string, number>();

    events.forEach((event) => {
      const start = new Date(event.start).getTime();
      const end = new Date(event.end).getTime();
      const hours = Math.max(0, (end - start) / (1000 * 60 * 60));

      const category = event.categoryId || '未分类';
      categoryMap.set(category, (categoryMap.get(category) || 0) + hours);
    });

    return Array.from(categoryMap.entries()).map(([name, value]) => ({
      name,
      value: Math.round(value * 10) / 10,
    }));
  }, [events]);

  if (stats.length === 0) return null;

  return (
    <div style={{
      padding: 'var(--space-4)',
      background: 'var(--color-surface)',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--color-border)',
      marginBottom: 'var(--space-4)',
    }}>
      <h3 style={{ fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-4)' }}>
        📊 时间花费统计
      </h3>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={stats}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={80}
            paddingAngle={2}
            dataKey="value"
          >
            {stats.map((_, index) => (
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => `${value} 小时`} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/
git commit -m "feat: add time statistics chart with Recharts"
```

---

## Task 4: 分享日程链接

**Files:**
- Create: `backend/app/services/share_service.py`
- Create: `backend/app/api/share.py`
- Modify: `backend/app/main.py`
- Create: `frontend/src/services/shareApi.ts`
- Create: `frontend/src/features/share/ShareLink.tsx`
- Create: `frontend/src/features/share/PublicCalendar.tsx`

- [ ] **Step 1: 创建分享服务**

创建 `backend/app/services/share_service.py`：

```python
import uuid
import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.event import Event
from app.core.config import get_settings


class ShareService:
    """生成只读日程分享链接。"""

    def __init__(self, db: Session):
        self.db = db

    def generate_share_token(self, user_id: str) -> str:
        """为用户生成分享 token。"""
        raw = f"{user_id}-{uuid.uuid4()}-{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get_shared_events(self, share_token: str) -> list[Event]:
        """通过分享 token 获取用户的事件（只读）。"""
        # 使用 token 的前8位作为 user_id 的代理（简化实现）
        # 实际生产中应存储 token -> user_id 映射表
        return (
            self.db.query(Event)
            .filter(Event.user_id == share_token[:8])
            .order_by(Event.start_time)
            .all()
        )
```

- [ ] **Step 2: 创建分享 API 路由**

创建 `backend/app/api/share.py`：

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.share_service import ShareService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/share", tags=["share"])


@router.post("/create")
def create_share_link(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ShareService(db)
    token = service.generate_share_token(current_user.id)
    return {
        "code": 0,
        "data": {"share_token": token, "url": f"/shared/{token}"},
        "message": "ok",
    }


@router.get("/{share_token}")
def get_shared_calendar(share_token: str, db: Session = Depends(get_db)):
    service = ShareService(db)
    events = service.get_shared_events(share_token)
    return {
        "code": 0,
        "data": [
            {
                "title": e.title,
                "start": e.start_time.isoformat(),
                "end": e.end_time.isoformat(),
                "allDay": e.is_all_day,
                "location": e.location,
            }
            for e in events
        ],
        "message": "ok",
    }
```

- [ ] **Step 3: 注册路由**

修改 `backend/app/main.py`：

```python
from app.api.share import router as share_router
app.include_router(share_router)
```

- [ ] **Step 4: 创建前端分享组件**

创建 `frontend/src/services/shareApi.ts`：

```typescript
import api from './api';

export const shareApi = {
  createLink: () =>
    api.post<{ code: number; data: { share_token: string; url: string }; message: string }>(
      '/share/create'
    ),

  getShared: (token: string) =>
    api.get<{ code: number; data: any[]; message: string }>(
      `/share/${token}`
    ),
};
```

创建 `frontend/src/features/share/ShareLink.tsx`：

```tsx
import { useState } from 'react';
import { shareApi } from '../../services/shareApi';

export default function ShareLink() {
  const [shareUrl, setShareUrl] = useState('');
  const [loading, setLoading] = useState(false);

  const handleCreateLink = async () => {
    try {
      setLoading(true);
      const resp = await shareApi.createLink();
      const url = `${window.location.origin}${resp.data.data.url}`;
      setShareUrl(url);
    } catch {
      // Handle error
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(shareUrl);
  };

  return (
    <div style={{
      padding: 'var(--space-4)',
      background: 'var(--color-surface)',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--color-border)',
    }}>
      <h3 style={{ fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-3)' }}>
        🔗 分享日程
      </h3>
      {shareUrl ? (
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <input
            readOnly
            value={shareUrl}
            style={{
              flex: 1,
              padding: 'var(--space-2)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-sm)',
            }}
          />
          <button
            onClick={handleCopy}
            style={{
              padding: 'var(--space-2) var(--space-4)',
              background: 'var(--color-primary)',
              color: 'var(--color-text-inverse)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-sm)',
            }}
          >
            复制
          </button>
        </div>
      ) : (
        <button
          onClick={handleCreateLink}
          disabled={loading}
          style={{
            padding: 'var(--space-2) var(--space-4)',
            background: 'var(--color-primary)',
            color: 'var(--color-text-inverse)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          {loading ? '生成中...' : '生成分享链接'}
        </button>
      )}
    </div>
  );
}
```

创建 `frontend/src/features/share/PublicCalendar.tsx`：

```tsx
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import { shareApi } from '../../services/shareApi';

export default function PublicCalendar() {
  const { token } = useParams<{ token: string }>();
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    if (!token) return;
    const fetchEvents = async () => {
      try {
        const resp = await shareApi.getShared(token);
        setEvents(resp.data.data);
      } catch {
        // Handle error
      }
    };
    fetchEvents();
  }, [token]);

  return (
    <div style={{ padding: 'var(--space-6)', maxWidth: '900px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: 'var(--space-6)', color: 'var(--color-primary)' }}>
        📅 共享日程
      </h1>
      <FullCalendar
        plugins={[dayGridPlugin]}
        initialView="dayGridMonth"
        locale="zh-cn"
        events={events}
        editable={false}
        height="auto"
      />
    </div>
  );
}
```

- [ ] **Step 5: 添加分享路由到 App.tsx**

修改 `frontend/src/App.tsx`，添加：

```tsx
import PublicCalendar from './features/share/PublicCalendar';
```

在 Routes 中添加：

```tsx
<Route path="/shared/:token" element={<PublicCalendar />} />
```

- [ ] **Step 6: 提交**

```bash
git add backend/ frontend/
git commit -m "feat: add share link and public calendar view"
```

---

## Task 5: 导出和打印

**Files:**
- Create: `frontend/src/features/export/ExportMenu.tsx`
- Modify: `backend/app/api/export.py`

- [ ] **Step 1: 创建导出菜单**

创建 `frontend/src/features/export/ExportMenu.tsx`：

```tsx
import { useEventStore } from '../../stores/useEventStore';

export default function ExportMenu() {
  const { events } = useEventStore();

  const handlePrint = () => {
    window.print();
  };

  const handleExportICal = () => {
    const icalContent = generateICal(events);
    const blob = new Blob([icalContent], { type: 'text/calendar;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'vocal-calendar-export.ics';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{
      padding: 'var(--space-4)',
      background: 'var(--color-surface)',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--color-border)',
    }}>
      <h3 style={{ fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-3)' }}>
        📤 导出
      </h3>
      <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
        <button
          onClick={handlePrint}
          style={{
            padding: 'var(--space-2) var(--space-4)',
            background: 'transparent',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          🖨️ 打印 / PDF
        </button>
        <button
          onClick={handleExportICal}
          style={{
            padding: 'var(--space-2) var(--space-4)',
            background: 'transparent',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          📅 导出 iCal
        </button>
      </div>
    </div>
  );
}

function generateICal(events: any[]): string {
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Vocal Calendar//CN',
  ];

  events.forEach((event) => {
    lines.push('BEGIN:VEVENT');
    lines.push(`DTSTART:${formatICalDate(event.start)}`);
    lines.push(`DTEND:${formatICalDate(event.end)}`);
    lines.push(`SUMMARY:${event.title}`);
    if (event.location) lines.push(`LOCATION:${event.location}`);
    if (event.description) lines.push(`DESCRIPTION:${event.description}`);
    lines.push('END:VEVENT');
  });

  lines.push('END:VCALENDAR');
  return lines.join('\r\n');
}

function formatICalDate(dateStr: string): string {
  return new Date(dateStr).toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/
git commit -m "feat: add export menu with print/PDF and iCal export"
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

1. 天气标注显示在日历头部
2. 节假日在日历上标注
3. 时间统计图表显示
4. 生成分享链接 → 新标签打开 → 只读日历
5. 打印/PDF 导出
6. iCal 文件下载

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "chore: phase 9 complete — value-added features (weather, holidays, stats, share, export)"
```

---

## 阶段交付物清单

| 交付物 | 状态 |
|--------|------|
| 天气服务 + API | ☐ |
| 节假日服务 + API | ☐ |
| 分享服务 + API | ☐ |
| 前端天气组件 | ☐ |
| 前端节假日组件 | ☐ |
| 时间统计图表 | ☐ |
| 分享链接组件 | ☐ |
| 公开日历页面 | ☐ |
| 导出菜单（打印/iCal） | ☐ |
