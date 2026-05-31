# Phase 3: 日历核心视图 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 集成 FullCalendar 实现日/周/月/议程四种视图，完成视图切换导航，将事件数据绑定到日历，适配活力多彩风格主题。

**Architecture:** 前端使用 @fullcalendar/react 作为日历核心组件，通过 Zustand store 管理事件数据和视图状态。日历组件封装在 features/calendar 模块中，支持四种视图切换。API 服务层对接后端事件接口（阶段 4 实现，此阶段用 mock 数据）。

**Tech Stack:** React 18, FullCalendar 6, TypeScript, Zustand, CSS Variables

---

## File Structure

| File | Responsibility |
|------|---------------|
| `frontend/src/features/calendar/CalendarPage.tsx` | 日历主页面（布局 + 视图切换） |
| `frontend/src/features/calendar/CalendarView.tsx` | FullCalendar 组件封装 |
| `frontend/src/features/calendar/ViewSwitcher.tsx` | 视图切换按钮组 |
| `frontend/src/features/calendar/CalendarHeader.tsx` | 日历头部（导航 + 标题） |
| `frontend/src/features/calendar/types.ts` | 日历相关类型定义 |
| `frontend/src/features/calendar/styles.css` | 日历自定义样式 |
| `frontend/src/features/calendar/__tests__/CalendarView.test.tsx` | 日历视图测试 |
| `frontend/src/stores/useEventStore.ts` | 事件数据 store |
| `frontend/src/services/eventApi.ts` | 事件 API 服务（mock 阶段） |
| `frontend/src/App.tsx` | 更新路由 |

---

## Task 1: 安装 FullCalendar 依赖

- [ ] **Step 1: 安装 FullCalendar**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npm install @fullcalendar/react @fullcalendar/daygrid @fullcalendar/timegrid @fullcalendar/list @fullcalendar/interaction
```

- [ ] **Step 2: 提交**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore: add FullCalendar dependencies"
```

---

## Task 2: 定义日历类型和事件 Store

**Files:**
- Create: `frontend/src/features/calendar/types.ts`
- Create: `frontend/src/stores/useEventStore.ts`
- Create: `frontend/src/services/eventApi.ts`

- [ ] **Step 1: 创建日历类型**

创建 `frontend/src/features/calendar/types.ts`：

```typescript
export interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  allDay: boolean;
  color?: string;
  location?: string;
  description?: string;
  categoryId?: string;
  priority?: number;
  recurrenceRule?: string;
}

export type CalendarViewType = 'dayGridMonth' | 'timeGridWeek' | 'timeGridDay' | 'listWeek';

export interface CalendarState {
  currentDate: Date;
  currentView: CalendarViewType;
  setCurrentDate: (date: Date) => void;
  setCurrentView: (view: CalendarViewType) => void;
}
```

- [ ] **Step 2: 创建 eventApi（mock 数据）**

创建 `frontend/src/services/eventApi.ts`：

```typescript
import api from './api';
import type { CalendarEvent } from '../features/calendar/types';

export const eventApi = {
  getEvents: (start: string, end: string) =>
    api.get<{ code: number; data: CalendarEvent[]; message: string }>(
      `/events?start=${start}&end=${end}`
    ),

  createEvent: (event: Omit<CalendarEvent, 'id'>) =>
    api.post<{ code: number; data: CalendarEvent; message: string }>('/events', event),

  updateEvent: (id: string, event: Partial<CalendarEvent>) =>
    api.put<{ code: number; data: CalendarEvent; message: string }>(`/events/${id}`, event),

  deleteEvent: (id: string) =>
    api.delete<{ code: number; data: null; message: string }>(`/events/${id}`),
};
```

- [ ] **Step 3: 创建 useEventStore**

创建 `frontend/src/stores/useEventStore.ts`：

```typescript
import { create } from 'zustand';
import type { CalendarEvent, CalendarViewType } from '../features/calendar/types';

interface EventState {
  events: CalendarEvent[];
  currentView: CalendarViewType;
  currentDate: Date;
  selectedEvent: CalendarEvent | null;

  setEvents: (events: CalendarEvent[]) => void;
  addEvent: (event: CalendarEvent) => void;
  updateEvent: (id: string, updates: Partial<CalendarEvent>) => void;
  removeEvent: (id: string) => void;
  setCurrentView: (view: CalendarViewType) => void;
  setCurrentDate: (date: Date) => void;
  setSelectedEvent: (event: CalendarEvent | null) => void;

  // Mock data for development (remove when backend is ready)
  loadMockEvents: () => void;
}

export const useEventStore = create<EventState>((set) => ({
  events: [],
  currentView: 'dayGridMonth',
  currentDate: new Date(),
  selectedEvent: null,

  setEvents: (events) => set({ events }),
  addEvent: (event) => set((state) => ({ events: [...state.events, event] })),
  updateEvent: (id, updates) =>
    set((state) => ({
      events: state.events.map((e) => (e.id === id ? { ...e, ...updates } : e)),
    })),
  removeEvent: (id) =>
    set((state) => ({ events: state.events.filter((e) => e.id !== id) })),
  setCurrentView: (view) => set({ currentView: view }),
  setCurrentDate: (date) => set({ currentDate: date }),
  setSelectedEvent: (event) => set({ selectedEvent: event }),

  loadMockEvents: () => {
    const today = new Date();
    const y = today.getFullYear();
    const m = today.getMonth();
    const d = today.getDate();

    const mockEvents: CalendarEvent[] = [
      {
        id: '1',
        title: '项目评审会议',
        start: new Date(y, m, d, 10, 0).toISOString(),
        end: new Date(y, m, d, 11, 30).toISOString(),
        allDay: false,
        color: '#4285F4',
        location: '会议室A',
      },
      {
        id: '2',
        title: '午餐约会',
        start: new Date(y, m, d, 12, 0).toISOString(),
        end: new Date(y, m, d, 13, 0).toISOString(),
        allDay: false,
        color: '#34A853',
      },
      {
        id: '3',
        title: '产品需求讨论',
        start: new Date(y, m, d + 1, 14, 0).toISOString(),
        end: new Date(y, m, d + 1, 15, 30).toISOString(),
        allDay: false,
        color: '#FBBC04',
      },
      {
        id: '4',
        title: '周末团建',
        start: new Date(y, m, d + 3).toISOString(),
        end: new Date(y, m, d + 4).toISOString(),
        allDay: true,
        color: '#EA4335',
      },
      {
        id: '5',
        title: '代码审查',
        start: new Date(y, m, d, 15, 0).toISOString(),
        end: new Date(y, m, d, 16, 0).toISOString(),
        allDay: false,
        color: '#9334E6',
      },
    ];
    set({ events: mockEvents });
  },
}));
```

- [ ] **Step 4: 提交**

```bash
git add frontend/
git commit -m "feat: add calendar types, event API service, and event store with mock data"
```

---

## Task 3: 创建日历视图组件

**Files:**
- Create: `frontend/src/features/calendar/CalendarView.tsx`
- Create: `frontend/src/features/calendar/styles.css`

- [ ] **Step 1: 编写 CalendarView 测试 (RED)**

创建 `frontend/src/features/calendar/__tests__/CalendarView.test.tsx`：

```tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CalendarView from '../CalendarView';
import { useEventStore } from '../../../stores/useEventStore';

describe('CalendarView', () => {
  beforeEach(() => {
    useEventStore.getState().loadMockEvents();
  });

  it('renders the calendar component', () => {
    render(<CalendarView />);
    // FullCalendar 渲染后会有日历网格
    expect(document.querySelector('.fc')).toBeInTheDocument();
  });

  it('displays mock events', () => {
    render(<CalendarView />);
    expect(screen.getByText('项目评审会议')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行测试确认失败 (RED)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run src/features/calendar/__tests__/CalendarView.test.tsx
```

Expected: FAIL — `Cannot find module '../CalendarView'`

- [ ] **Step 3: 创建日历自定义样式**

创建 `frontend/src/features/calendar/styles.css`：

```css
/* === FullCalendar Theme Overrides === */
.fc {
  --fc-border-color: var(--color-border);
  --fc-page-bg-color: var(--color-bg);
  --fc-neutral-bg-color: var(--color-bg-secondary);
  --fc-list-event-hover-bg-color: var(--color-surface-hover);

  font-family: var(--font-family);
}

/* Header toolbar */
.fc .fc-toolbar-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--color-text);
}

.fc .fc-button {
  background: var(--color-primary);
  border-color: var(--color-primary);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: 500;
  padding: var(--space-2) var(--space-4);
  transition: all var(--transition-fast);
}

.fc .fc-button:hover {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
}

.fc .fc-button-active {
  background: var(--color-primary-dark) !important;
  border-color: var(--color-primary-dark) !important;
}

.fc .fc-today-button {
  background: var(--color-surface);
  border-color: var(--color-border);
  color: var(--color-text);
}

.fc .fc-today-button:disabled {
  opacity: 0.5;
}

/* Day headers */
.fc .fc-col-header-cell {
  background: var(--color-bg-secondary);
  font-weight: 600;
  color: var(--color-text-secondary);
  padding: var(--space-2) 0;
}

/* Today highlight */
.fc .fc-day-today {
  background: rgba(66, 133, 244, 0.05) !important;
}

/* Events */
.fc .fc-event {
  border-radius: var(--radius-sm);
  border: none;
  padding: 2px 6px;
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: transform var(--transition-fast);
}

.fc .fc-event:hover {
  transform: scale(1.02);
  box-shadow: var(--shadow-md);
}

.fc .fc-event-title {
  font-weight: 500;
}

.fc .fc-event-time {
  font-size: var(--font-size-xs);
  opacity: 0.8;
}

/* All day events */
.fc .fc-daygrid-event {
  border-radius: var(--radius-sm);
}

/* Month day numbers */
.fc .fc-daygrid-day-number {
  color: var(--color-text);
  font-weight: 500;
  padding: var(--space-2);
}

.fc .fc-day-other .fc-daygrid-day-number {
  color: var(--color-text-disabled);
}

/* Week/day time axis */
.fc .fc-timegrid-slot-label-cushion {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.fc .fc-timegrid-axis {
  color: var(--color-text-secondary);
}

/* List view */
.fc .fc-list-event-title a {
  color: var(--color-text);
  font-weight: 500;
}

.fc .fc-list-event-time {
  color: var(--color-text-secondary);
}

/* Responsive */
@media (max-width: 768px) {
  .fc .fc-toolbar {
    flex-direction: column;
    gap: var(--space-2);
  }

  .fc .fc-toolbar-title {
    font-size: var(--font-size-lg);
  }
}
```

- [ ] **Step 4: 创建 CalendarView 组件**

创建 `frontend/src/features/calendar/CalendarView.tsx`：

```tsx
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
import interactionPlugin from '@fullcalendar/interaction';
import { useEventStore } from '../../stores/useEventStore';
import type { CalendarViewType } from './types';
import './styles.css';

export default function CalendarView() {
  const { events, currentView, currentDate, setCurrentView, setCurrentDate } =
    useEventStore();

  const handleViewChange = (view: CalendarViewType) => {
    setCurrentView(view);
  };

  const handleDateChange = (date: Date) => {
    setCurrentDate(date);
  };

  const calendarEvents = events.map((event) => ({
    id: event.id,
    title: event.title,
    start: event.start,
    end: event.end,
    allDay: event.allDay,
    backgroundColor: event.color,
    borderColor: event.color,
    extendedProps: {
      location: event.location,
      description: event.description,
      priority: event.priority,
    },
  }));

  return (
    <div className="calendar-view">
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, listPlugin, interactionPlugin]}
        initialView={currentView}
        initialDate={currentDate}
        headerToolbar={{
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek',
        }}
        buttonText={{
          today: '今天',
          month: '月',
          week: '周',
          day: '日',
          list: '列表',
        }}
        locale="zh-cn"
        events={calendarEvents}
        editable={true}
        selectable={true}
        selectMirror={true}
        dayMaxEvents={3}
        weekends={true}
        height="calc(100vh - var(--topbar-height) - var(--space-8))"
        viewDidMount={(info) => {
          handleViewChange(info.view.type as CalendarViewType);
        }}
        datesSet={(info) => {
          handleDateChange(info.view.currentStart);
        }}
        eventClick={(info) => {
          console.log('Event clicked:', info.event.title);
        }}
        select={(info) => {
          console.log('Date selected:', info.startStr, info.endStr);
        }}
        eventDrop={(info) => {
          console.log('Event dropped:', info.event.title, info.event.startStr);
        }}
      />
    </div>
  );
}
```

- [ ] **Step 5: 运行测试确认通过 (GREEN)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run src/features/calendar/__tests__/CalendarView.test.tsx
```

Expected: `2 passed`

- [ ] **Step 6: 提交**

```bash
git add frontend/
git commit -m "feat: add CalendarView component with FullCalendar integration"
```

---

## Task 4: 创建日历主页面和布局

**Files:**
- Create: `frontend/src/features/calendar/CalendarPage.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建 CalendarPage**

创建 `frontend/src/features/calendar/CalendarPage.tsx`：

```tsx
import CalendarView from './CalendarView';
import { useAuthStore } from '../../stores/useAuthStore';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useEventStore } from '../../stores/useEventStore';

export default function CalendarPage() {
  const { user, logout } = useAuthStore();
  const { loadMockEvents } = useEventStore();
  const navigate = useNavigate();

  useEffect(() => {
    loadMockEvents();
  }, [loadMockEvents]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Top Bar */}
      <header
        style={{
          height: 'var(--topbar-height)',
          background: 'var(--color-surface)',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 var(--space-6)',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-primary)' }}>
            📅 Vocal Calendar
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
          <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
            {user?.username}
          </span>
          <button
            onClick={handleLogout}
            style={{
              padding: 'var(--space-2) var(--space-4)',
              background: 'transparent',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-text-secondary)',
              fontSize: 'var(--font-size-sm)',
              cursor: 'pointer',
            }}
          >
            退出
          </button>
        </div>
      </header>

      {/* Calendar Content */}
      <main style={{ flex: 1, padding: 'var(--space-4)', overflow: 'hidden' }}>
        <CalendarView />
      </main>
    </div>
  );
}
```

- [ ] **Step 2: 更新 App.tsx 路由**

替换 `frontend/src/App.tsx`：

```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './features/auth/LoginPage';
import RegisterPage from './features/auth/RegisterPage';
import AuthGuard from './features/auth/AuthGuard';
import CalendarPage from './features/calendar/CalendarPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/calendar"
          element={
            <AuthGuard>
              <CalendarPage />
            </AuthGuard>
          }
        />
        <Route path="/" element={<Navigate to="/calendar" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

- [ ] **Step 3: 运行全部前端测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run
```

Expected: 所有测试通过

- [ ] **Step 4: 提交**

```bash
git add frontend/
git commit -m "feat: add CalendarPage with top bar and routing integration"
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

启动前后端，浏览器访问 http://localhost:5173：
1. 登录后进入日历页面
2. 默认月视图显示 mock 事件
3. 点击"周"切换到周视图
4. 点击"日"切换到日视图
5. 点击"列表"切换到议程视图
6. 点击"今天"回到今天
7. 左右箭头切换月份/周/日
8. 事件显示正确的颜色和标题

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "chore: phase 3 complete — calendar views with FullCalendar integration"
```

---

## 阶段交付物清单

| 交付物 | 状态 |
|--------|------|
| FullCalendar 依赖安装 | ☐ |
| 日历类型定义 | ☐ |
| eventApi 服务层 | ☐ |
| useEventStore（含 mock 数据） | ☐ |
| CalendarView 组件（四视图） | ☐ |
| 日历自定义样式（活力多彩） | ☐ |
| CalendarPage 页面布局 | ☐ |
| 路由集成 | ☐ |
