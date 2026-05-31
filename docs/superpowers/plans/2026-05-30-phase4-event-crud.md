# Phase 4: 事件 CRUD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现完整的事件 CRUD 功能，包含 Event/Category 模型、后端 API、前端事件模态框、拖拽调整时间、右键菜单、分类管理、重复事件、全文搜索。

**Architecture:** 后端 SQLAlchemy 模型 + Pydantic Schema + FastAPI 路由，前端 Zustand store 管理事件状态，FullCalendar 交互插件支持拖拽和点击创建。RRULE 格式存储重复规则。

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic v2, React 18, FullCalendar, Zustand, react-hook-form, zod

---

## File Structure

### Backend

| File | Responsibility |
|------|---------------|
| `backend/app/models/event.py` | Event SQLAlchemy 模型 |
| `backend/app/models/category.py` | Category SQLAlchemy 模型 |
| `backend/app/schemas/event.py` | Event Pydantic Schema |
| `backend/app/schemas/category.py` | Category Pydantic Schema |
| `backend/app/services/event_service.py` | Event 业务逻辑 |
| `backend/app/services/category_service.py` | Category 业务逻辑 |
| `backend/app/api/events.py` | Event API 路由 |
| `backend/app/api/categories.py` | Category API 路由 |
| `backend/tests/test_event_service.py` | Event 服务测试 |
| `backend/tests/test_event_api.py` | Event API 测试 |

### Frontend

| File | Responsibility |
|------|---------------|
| `frontend/src/features/events/EventModal.tsx` | 事件创建/编辑模态框 |
| `frontend/src/features/events/EventContextMenu.tsx` | 右键上下文菜单 |
| `frontend/src/features/events/EventForm.tsx` | 事件表单 |
| `frontend/src/features/categories/CategoryManager.tsx` | 分类管理 |
| `frontend/src/services/categoryApi.ts` | 分类 API 服务 |
| `frontend/src/stores/useCategoryStore.ts` | 分类状态管理 |

---

## Task 1: 创建 Event 和 Category 模型

**Files:**
- Create: `backend/app/models/event.py`
- Create: `backend/app/models/category.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 创建 Category 模型**

创建 `backend/app/models/category.py`：

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(7), default="#4285F4")
    icon: Mapped[str] = mapped_column(String(50), default="calendar")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    events = relationship("Event", back_populates="category")
```

- [ ] **Step 2: 创建 Event 模型**

创建 `backend/app/models/event.py`：

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, SmallInteger, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=False)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    category_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    priority: Mapped[int] = mapped_column(SmallInteger, default=3)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    recurrence_rule: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category = relationship("Category", back_populates="events")
```

- [ ] **Step 3: 更新 models/__init__.py**

替换 `backend/app/models/__init__.py`：

```python
from app.models.user import User
from app.models.event import Event
from app.models.category import Category

__all__ = ["User", "Event", "Category"]
```

- [ ] **Step 4: 更新 alembic/env.py 导入**

在 `backend/alembic/env.py` 中更新导入：

```python
from app.models import user, event, category  # noqa: F401
```

- [ ] **Step 5: 生成并执行迁移**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
alembic revision --autogenerate -m "create events and categories tables"
alembic upgrade head
```

- [ ] **Step 6: 验证表创建**

```bash
docker exec -it vocal-calendar-db psql -U vocal_user -d vocal_calendar -c "\dt"
```

Expected: 输出包含 `events` 和 `categories` 表

- [ ] **Step 7: 提交**

```bash
git add backend/
git commit -m "feat: add Event and Category models with migration"
```

---

## Task 2: 创建 Event 和 Category Schema

**Files:**
- Create: `backend/app/schemas/event.py`
- Create: `backend/app/schemas/category.py`

- [ ] **Step 1: 创建 Event Schema**

创建 `backend/app/schemas/event.py`：

```python
from pydantic import BaseModel
from datetime import datetime


class EventCreateRequest(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    is_all_day: bool = False
    location: str | None = None
    category_id: str | None = None
    priority: int = 3
    color: str | None = None
    recurrence_rule: str | None = None


class EventUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    is_all_day: bool | None = None
    location: str | None = None
    category_id: str | None = None
    priority: int | None = None
    color: str | None = None
    recurrence_rule: str | None = None


class EventResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str | None
    start_time: datetime
    end_time: datetime
    is_all_day: bool
    location: str | None
    category_id: str | None
    priority: int
    color: str | None
    recurrence_rule: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventSearchParams(BaseModel):
    q: str
    start: datetime | None = None
    end: datetime | None = None
```

- [ ] **Step 2: 创建 Category Schema**

创建 `backend/app/schemas/category.py`：

```python
from pydantic import BaseModel
from datetime import datetime


class CategoryCreateRequest(BaseModel):
    name: str
    color: str = "#4285F4"
    icon: str = "calendar"


class CategoryUpdateRequest(BaseModel):
    name: str | None = None
    color: str | None = None
    icon: str | None = None


class CategoryResponse(BaseModel):
    id: str
    user_id: str
    name: str
    color: str
    icon: str
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 提交**

```bash
git add backend/
git commit -m "feat: add Event and Category Pydantic schemas"
```

---

## Task 3: 实现 Event 和 Category Service

**Files:**
- Create: `backend/app/services/event_service.py`
- Create: `backend/app/services/category_service.py`
- Create: `backend/tests/test_event_service.py`

- [ ] **Step 1: 编写 EventService 测试 (RED)**

创建 `backend/tests/test_event_service.py`：

```python
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.services.event_service import EventService
from app.models.event import Event


@pytest.fixture
def db():
    return MagicMock(spec=Session)


@pytest.fixture
def service(db):
    return EventService(db)


class TestCreateEvent:
    def test_create_event(self, service, db):
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        now = datetime.now(timezone.utc)
        event = service.create_event(
            user_id="user-1",
            title="测试会议",
            start_time=now,
            end_time=now + timedelta(hours=1),
        )
        assert db.add.called
        assert db.commit.called


class TestGetEvents:
    def test_get_events_by_date_range(self, service, db):
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value = mock_query

        now = datetime.now(timezone.utc)
        events = service.get_events("user-1", now, now + timedelta(days=7))
        assert isinstance(events, list)


class TestUpdateEvent:
    def test_update_event_title(self, service, db):
        mock_event = Event(
            id="event-1",
            user_id="user-1",
            title="旧标题",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_event
        db.query.return_value = mock_query
        db.commit = MagicMock()
        db.refresh = MagicMock()

        result = service.update_event("event-1", "user-1", title="新标题")
        assert mock_event.title == "新标题"


class TestDeleteEvent:
    def test_delete_event(self, service, db):
        mock_event = Event(id="event-1", user_id="user-1")
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_event
        db.query.return_value = mock_query
        db.delete = MagicMock()
        db.commit = MagicMock()

        result = service.delete_event("event-1", "user-1")
        assert db.delete.called


class TestSearchEvents:
    def test_search_events(self, service, db):
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value = mock_query

        events = service.search_events("user-1", "会议")
        assert isinstance(events, list)
```

- [ ] **Step 2: 运行测试确认失败 (RED)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_event_service.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现 EventService**

创建 `backend/app/services/event_service.py`：

```python
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.event import Event


class EventService:
    def __init__(self, db: Session):
        self.db = db

    def create_event(self, user_id: str, **kwargs) -> Event:
        event = Event(user_id=user_id, **kwargs)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_events(
        self, user_id: str, start: datetime, end: datetime
    ) -> list[Event]:
        return (
            self.db.query(Event)
            .filter(
                Event.user_id == user_id,
                Event.start_time >= start,
                Event.start_time <= end,
            )
            .order_by(Event.start_time)
            .all()
        )

    def get_event_by_id(self, event_id: str, user_id: str) -> Event | None:
        return (
            self.db.query(Event)
            .filter(Event.id == event_id, Event.user_id == user_id)
            .first()
        )

    def update_event(self, event_id: str, user_id: str, **kwargs) -> Event:
        event = self.get_event_by_id(event_id, user_id)
        if not event:
            raise ValueError("事件不存在")

        for key, value in kwargs.items():
            if value is not None and hasattr(event, key):
                setattr(event, key, value)

        self.db.commit()
        self.db.refresh(event)
        return event

    def delete_event(self, event_id: str, user_id: str) -> bool:
        event = self.get_event_by_id(event_id, user_id)
        if not event:
            raise ValueError("事件不存在")

        self.db.delete(event)
        self.db.commit()
        return True

    def search_events(self, user_id: str, query: str) -> list[Event]:
        return (
            self.db.query(Event)
            .filter(
                Event.user_id == user_id,
                or_(
                    Event.title.ilike(f"%{query}%"),
                    Event.description.ilike(f"%{query}%"),
                    Event.location.ilike(f"%{query}%"),
                ),
            )
            .order_by(Event.start_time.desc())
            .all()
        )
```

- [ ] **Step 4: 实现 CategoryService**

创建 `backend/app/services/category_service.py`：

```python
from sqlalchemy.orm import Session
from app.models.category import Category


class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_category(self, user_id: str, name: str, color: str = "#4285F4", icon: str = "calendar") -> Category:
        category = Category(user_id=user_id, name=name, color=color, icon=icon)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def get_categories(self, user_id: str) -> list[Category]:
        return (
            self.db.query(Category)
            .filter(Category.user_id == user_id)
            .order_by(Category.name)
            .all()
        )

    def update_category(self, category_id: str, user_id: str, **kwargs) -> Category:
        category = (
            self.db.query(Category)
            .filter(Category.id == category_id, Category.user_id == user_id)
            .first()
        )
        if not category:
            raise ValueError("分类不存在")

        for key, value in kwargs.items():
            if value is not None and hasattr(category, key):
                setattr(category, key, value)

        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, category_id: str, user_id: str) -> bool:
        category = (
            self.db.query(Category)
            .filter(Category.id == category_id, Category.user_id == user_id)
            .first()
        )
        if not category:
            raise ValueError("分类不存在")

        self.db.delete(category)
        self.db.commit()
        return True
```

- [ ] **Step 5: 运行测试确认通过 (GREEN)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_event_service.py -v
```

Expected: `5 passed`

- [ ] **Step 6: 提交**

```bash
git add backend/
git commit -m "feat: add EventService and CategoryService with tests"
```

---

## Task 4: 创建 Event 和 Category API 路由

**Files:**
- Create: `backend/app/api/events.py`
- Create: `backend/app/api/categories.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_event_api.py`

- [ ] **Step 1: 创建 Event 路由**

创建 `backend/app/api/events.py`：

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.schemas.event import (
    EventCreateRequest,
    EventUpdateRequest,
    EventResponse,
)
from app.services.event_service import EventService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("")
def get_events(
    start: datetime = Query(...),
    end: datetime = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    events = service.get_events(current_user.id, start, end)
    return {
        "code": 0,
        "data": [EventResponse.from_orm(e) for e in events],
        "message": "ok",
    }


@router.post("")
def create_event(
    req: EventCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    event = service.create_event(
        user_id=current_user.id,
        title=req.title,
        description=req.description,
        start_time=req.start_time,
        end_time=req.end_time,
        is_all_day=req.is_all_day,
        location=req.location,
        category_id=req.category_id,
        priority=req.priority,
        color=req.color,
        recurrence_rule=req.recurrence_rule,
    )
    return {"code": 0, "data": EventResponse.from_orm(event), "message": "创建成功"}


@router.get("/search")
def search_events(
    q: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    events = service.search_events(current_user.id, q)
    return {
        "code": 0,
        "data": [EventResponse.from_orm(e) for e in events],
        "message": "ok",
    }


@router.get("/{event_id}")
def get_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    event = service.get_event_by_id(event_id, current_user.id)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    return {"code": 0, "data": EventResponse.from_orm(event), "message": "ok"}


@router.put("/{event_id}")
def update_event(
    event_id: str,
    req: EventUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    try:
        event = service.update_event(
            event_id,
            current_user.id,
            title=req.title,
            description=req.description,
            start_time=req.start_time,
            end_time=req.end_time,
            is_all_day=req.is_all_day,
            location=req.location,
            category_id=req.category_id,
            priority=req.priority,
            color=req.color,
            recurrence_rule=req.recurrence_rule,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"code": 0, "data": EventResponse.from_orm(event), "message": "更新成功"}


@router.delete("/{event_id}")
def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    try:
        service.delete_event(event_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"code": 0, "data": None, "message": "删除成功"}
```

- [ ] **Step 2: 创建 Category 路由**

创建 `backend/app/api/categories.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.category import (
    CategoryCreateRequest,
    CategoryUpdateRequest,
    CategoryResponse,
)
from app.services.category_service import CategoryService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("")
def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    categories = service.get_categories(current_user.id)
    return {
        "code": 0,
        "data": [CategoryResponse.from_orm(c) for c in categories],
        "message": "ok",
    }


@router.post("")
def create_category(
    req: CategoryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    category = service.create_category(current_user.id, req.name, req.color, req.icon)
    return {"code": 0, "data": CategoryResponse.from_orm(category), "message": "创建成功"}


@router.put("/{category_id}")
def update_category(
    category_id: str,
    req: CategoryUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    try:
        category = service.update_category(
            category_id, current_user.id,
            name=req.name, color=req.color, icon=req.icon,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"code": 0, "data": CategoryResponse.from_orm(category), "message": "更新成功"}


@router.delete("/{category_id}")
def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    try:
        service.delete_category(category_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"code": 0, "data": None, "message": "删除成功"}
```

- [ ] **Step 3: 注册路由到 main.py**

修改 `backend/app/main.py`，添加：

```python
from app.api.events import router as events_router
from app.api.categories import router as categories_router

app.include_router(events_router)
app.include_router(categories_router)
```

- [ ] **Step 4: 编写 Event API 集成测试 (RED)**

创建 `backend/tests/test_event_api.py`：

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "postgresql://vocal_user:vocal_pass@localhost:5432/vocal_calendar_test"
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    client.post("/api/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123",
    })
    resp = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestEventCRUD:
    def test_create_event(self, client, auth_headers):
        response = client.post("/api/events", json={
            "title": "测试会议",
            "start_time": "2026-06-01T10:00:00Z",
            "end_time": "2026-06-01T11:00:00Z",
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["title"] == "测试会议"

    def test_get_events(self, client, auth_headers):
        client.post("/api/events", json={
            "title": "会议A",
            "start_time": "2026-06-01T10:00:00Z",
            "end_time": "2026-06-01T11:00:00Z",
        }, headers=auth_headers)

        response = client.get(
            "/api/events?start=2026-06-01T00:00:00Z&end=2026-06-02T00:00:00Z",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1

    def test_update_event(self, client, auth_headers):
        create_resp = client.post("/api/events", json={
            "title": "旧标题",
            "start_time": "2026-06-01T10:00:00Z",
            "end_time": "2026-06-01T11:00:00Z",
        }, headers=auth_headers)
        event_id = create_resp.json()["data"]["id"]

        response = client.put(f"/api/events/{event_id}", json={
            "title": "新标题",
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["title"] == "新标题"

    def test_delete_event(self, client, auth_headers):
        create_resp = client.post("/api/events", json={
            "title": "要删除的事件",
            "start_time": "2026-06-01T10:00:00Z",
            "end_time": "2026-06-01T11:00:00Z",
        }, headers=auth_headers)
        event_id = create_resp.json()["data"]["id"]

        response = client.delete(f"/api/events/{event_id}", headers=auth_headers)
        assert response.status_code == 200

    def test_search_events(self, client, auth_headers):
        client.post("/api/events", json={
            "title": "项目评审会议",
            "start_time": "2026-06-01T10:00:00Z",
            "end_time": "2026-06-01T11:00:00Z",
        }, headers=auth_headers)

        response = client.get("/api/events/search?q=评审", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1
```

- [ ] **Step 5: 运行测试确认通过 (GREEN)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_event_api.py -v
```

Expected: `5 passed`

- [ ] **Step 6: 提交**

```bash
git add backend/
git commit -m "feat: add Event and Category API routes with integration tests"
```

---

## Task 5: 创建前端事件模态框和表单

**Files:**
- Create: `frontend/src/features/events/EventForm.tsx`
- Create: `frontend/src/features/events/EventModal.tsx`
- Create: `frontend/src/features/events/EventContextMenu.tsx`

- [ ] **Step 1: 创建 EventForm**

创建 `frontend/src/features/events/EventForm.tsx`：

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { CalendarEvent } from '../calendar/types';

const eventSchema = z.object({
  title: z.string().min(1, '请输入标题'),
  start_time: z.string().min(1, '请选择开始时间'),
  end_time: z.string().min(1, '请选择结束时间'),
  is_all_day: z.boolean().default(false),
  location: z.string().optional(),
  description: z.string().optional(),
  priority: z.number().min(1).max(5).default(3),
  color: z.string().optional(),
});

type EventFormData = z.infer<typeof eventSchema>;

interface EventFormProps {
  initialData?: Partial<CalendarEvent>;
  onSubmit: (data: EventFormData) => void;
  onCancel: () => void;
}

export default function EventForm({ initialData, onSubmit, onCancel }: EventFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<EventFormData>({
    resolver: zodResolver(eventSchema),
    defaultValues: {
      title: initialData?.title || '',
      start_time: initialData?.start ? initialData.start.slice(0, 16) : '',
      end_time: initialData?.end ? initialData.end.slice(0, 16) : '',
      is_all_day: initialData?.allDay || false,
      location: initialData?.location || '',
      description: initialData?.description || '',
      priority: initialData?.priority || 3,
      color: initialData?.color || '#4285F4',
    },
  });

  const colorOptions = [
    { value: '#4285F4', label: '蓝' },
    { value: '#EA4335', label: '红' },
    { value: '#34A853', label: '绿' },
    { value: '#FBBC04', label: '黄' },
    { value: '#9334E6', label: '紫' },
  ];

  return (
    <form onSubmit={handleSubmit(onSubmit)} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      <div>
        <label htmlFor="title" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
          标题
        </label>
        <input
          id="title"
          {...register('title')}
          placeholder="事件标题"
          style={{
            width: '100%',
            padding: 'var(--space-3)',
            border: `1px solid ${errors.title ? 'var(--color-error)' : 'var(--color-border)'}`,
            borderRadius: 'var(--radius-md)',
          }}
        />
        {errors.title && <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>{errors.title.message}</span>}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
        <div>
          <label htmlFor="start_time" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
            开始时间
          </label>
          <input
            id="start_time"
            type="datetime-local"
            {...register('start_time')}
            style={{
              width: '100%',
              padding: 'var(--space-3)',
              border: `1px solid ${errors.start_time ? 'var(--color-error)' : 'var(--color-border)'}`,
              borderRadius: 'var(--radius-md)',
            }}
          />
        </div>
        <div>
          <label htmlFor="end_time" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
            结束时间
          </label>
          <input
            id="end_time"
            type="datetime-local"
            {...register('end_time')}
            style={{
              width: '100%',
              padding: 'var(--space-3)',
              border: `1px solid ${errors.end_time ? 'var(--color-error)' : 'var(--color-border)'}`,
              borderRadius: 'var(--radius-md)',
            }}
          />
        </div>
      </div>

      <div>
        <label htmlFor="location" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
          地点
        </label>
        <input
          id="location"
          {...register('location')}
          placeholder="可选"
          style={{
            width: '100%',
            padding: 'var(--space-3)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
          }}
        />
      </div>

      <div>
        <label htmlFor="description" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
          备注
        </label>
        <textarea
          id="description"
          {...register('description')}
          rows={3}
          placeholder="可选"
          style={{
            width: '100%',
            padding: 'var(--space-3)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            resize: 'vertical',
          }}
        />
      </div>

      <div>
        <label style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
          颜色
        </label>
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          {colorOptions.map((opt) => (
            <label
              key={opt.value}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-1)',
                cursor: 'pointer',
              }}
            >
              <input type="radio" value={opt.value} {...register('color')} />
              <span
                style={{
                  width: 20,
                  height: 20,
                  borderRadius: 'var(--radius-full)',
                  background: opt.value,
                }}
              />
            </label>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end', marginTop: 'var(--space-2)' }}>
        <button
          type="button"
          onClick={onCancel}
          style={{
            padding: 'var(--space-2) var(--space-6)',
            background: 'transparent',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-text-secondary)',
          }}
        >
          取消
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          style={{
            padding: 'var(--space-2) var(--space-6)',
            background: 'var(--color-primary)',
            color: 'var(--color-text-inverse)',
            borderRadius: 'var(--radius-md)',
            fontWeight: 600,
          }}
        >
          {initialData?.id ? '保存' : '创建'}
        </button>
      </div>
    </form>
  );
}
```

- [ ] **Step 2: 创建 EventModal**

创建 `frontend/src/features/events/EventModal.tsx`：

```tsx
import EventForm from './EventForm';
import type { CalendarEvent } from '../calendar/types';

interface EventModalProps {
  isOpen: boolean;
  event?: CalendarEvent | null;
  onSubmit: (data: any) => void;
  onClose: () => void;
}

export default function EventModal({ isOpen, event, onSubmit, onClose }: EventModalProps) {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1000,
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          background: 'var(--color-surface)',
          borderRadius: 'var(--radius-xl)',
          padding: 'var(--space-8)',
          width: '100%',
          maxWidth: '500px',
          maxHeight: '90vh',
          overflow: 'auto',
          boxShadow: 'var(--shadow-xl)',
        }}
      >
        <h2 style={{ marginBottom: 'var(--space-6)', fontSize: 'var(--font-size-xl)' }}>
          {event?.id ? '编辑事件' : '创建事件'}
        </h2>
        <EventForm
          initialData={event || undefined}
          onSubmit={onSubmit}
          onCancel={onClose}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 创建 EventContextMenu**

创建 `frontend/src/features/events/EventContextMenu.tsx`：

```tsx
interface ContextMenuPosition {
  x: number;
  y: number;
}

interface EventContextMenuProps {
  isOpen: boolean;
  position: ContextMenuPosition;
  onEdit: () => void;
  onDelete: () => void;
  onClose: () => void;
}

export default function EventContextMenu({
  isOpen,
  position,
  onEdit,
  onDelete,
  onClose,
}: EventContextMenuProps) {
  if (!isOpen) return null;

  return (
    <>
      <div
        style={{ position: 'fixed', inset: 0, zIndex: 999 }}
        onClick={onClose}
      />
      <div
        style={{
          position: 'fixed',
          left: position.x,
          top: position.y,
          background: 'var(--color-surface)',
          borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid var(--color-border)',
          padding: 'var(--space-1)',
          zIndex: 1000,
          minWidth: '160px',
        }}
      >
        <button
          onClick={onEdit}
          style={{
            display: 'block',
            width: '100%',
            padding: 'var(--space-2) var(--space-4)',
            background: 'transparent',
            textAlign: 'left',
            borderRadius: 'var(--radius-sm)',
            fontSize: 'var(--font-size-sm)',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-surface-hover)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          ✏️ 编辑事件
        </button>
        <button
          onClick={onDelete}
          style={{
            display: 'block',
            width: '100%',
            padding: 'var(--space-2) var(--space-4)',
            background: 'transparent',
            textAlign: 'left',
            borderRadius: 'var(--radius-sm)',
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-error)',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-surface-hover)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          🗑️ 删除事件
        </button>
      </div>
    </>
  );
}
```

- [ ] **Step 4: 提交**

```bash
git add frontend/
git commit -m "feat: add EventForm, EventModal, and EventContextMenu components"
```

---

## Task 6: 集成事件操作到日历页面

**Files:**
- Modify: `frontend/src/features/calendar/CalendarPage.tsx`
- Modify: `frontend/src/features/calendar/CalendarView.tsx`

- [ ] **Step 1: 更新 CalendarPage 集成事件模态框**

替换 `frontend/src/features/calendar/CalendarPage.tsx`：

```tsx
import { useState } from 'react';
import CalendarView from './CalendarView';
import EventModal from '../events/EventModal';
import EventContextMenu from '../events/EventContextMenu';
import { useAuthStore } from '../../stores/useAuthStore';
import { useEventStore } from '../../stores/useEventStore';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import type { CalendarEvent } from './types';

export default function CalendarPage() {
  const { user, logout } = useAuthStore();
  const { loadMockEvents, addEvent, updateEvent, removeEvent } = useEventStore();
  const navigate = useNavigate();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null);
  const [contextMenu, setContextMenu] = useState<{
    isOpen: boolean;
    position: { x: number; y: number };
    event: CalendarEvent | null;
  }>({ isOpen: false, position: { x: 0, y: 0 }, event: null });

  useEffect(() => {
    loadMockEvents();
  }, [loadMockEvents]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleCreateEvent = () => {
    setEditingEvent(null);
    setIsModalOpen(true);
  };

  const handleSubmitEvent = (data: any) => {
    if (editingEvent?.id) {
      updateEvent(editingEvent.id, {
        title: data.title,
        start: data.start_time,
        end: data.end_time,
        allDay: data.is_all_day,
        location: data.location,
        description: data.description,
        priority: data.priority,
        color: data.color,
      });
    } else {
      addEvent({
        id: Date.now().toString(),
        title: data.title,
        start: data.start_time,
        end: data.end_time,
        allDay: data.is_all_day,
        location: data.location,
        description: data.description,
        priority: data.priority,
        color: data.color,
      });
    }
    setIsModalOpen(false);
    setEditingEvent(null);
  };

  const handleDeleteEvent = () => {
    if (contextMenu.event?.id) {
      removeEvent(contextMenu.event.id);
    }
    setContextMenu({ isOpen: false, position: { x: 0, y: 0 }, event: null });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
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
          <button
            onClick={handleCreateEvent}
            style={{
              padding: 'var(--space-2) var(--space-4)',
              background: 'var(--color-primary)',
              color: 'var(--color-text-inverse)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-sm)',
              fontWeight: 600,
            }}
          >
            + 新建事件
          </button>
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
            }}
          >
            退出
          </button>
        </div>
      </header>

      <main style={{ flex: 1, padding: 'var(--space-4)', overflow: 'hidden' }}>
        <CalendarView
          onEventClick={(event) => {
            setEditingEvent(event);
            setIsModalOpen(true);
          }}
          onEventContextMenu={(event, position) => {
            setContextMenu({ isOpen: true, position, event });
          }}
        />
      </main>

      <EventModal
        isOpen={isModalOpen}
        event={editingEvent}
        onSubmit={handleSubmitEvent}
        onClose={() => {
          setIsModalOpen(false);
          setEditingEvent(null);
        }}
      />

      <EventContextMenu
        isOpen={contextMenu.isOpen}
        position={contextMenu.position}
        onEdit={() => {
          setEditingEvent(contextMenu.event);
          setIsModalOpen(true);
          setContextMenu({ isOpen: false, position: { x: 0, y: 0 }, event: null });
        }}
        onDelete={handleDeleteEvent}
        onClose={() => setContextMenu({ isOpen: false, position: { x: 0, y: 0 }, event: null })}
      />
    </div>
  );
}
```

- [ ] **Step 2: 更新 CalendarView 支持事件回调**

替换 `frontend/src/features/calendar/CalendarView.tsx`：

```tsx
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
import interactionPlugin from '@fullcalendar/interaction';
import { useEventStore } from '../../stores/useEventStore';
import type { CalendarEvent, CalendarViewType } from './types';
import './styles.css';

interface CalendarViewProps {
  onEventClick?: (event: CalendarEvent) => void;
  onEventContextMenu?: (event: CalendarEvent, position: { x: number; y: number }) => void;
}

export default function CalendarView({ onEventClick, onEventContextMenu }: CalendarViewProps) {
  const { events, currentView, currentDate, setCurrentView, setCurrentDate } =
    useEventStore();

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
      originalEvent: event,
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
          setCurrentView(info.view.type as CalendarViewType);
        }}
        datesSet={(info) => {
          setCurrentDate(info.view.currentStart);
        }}
        eventClick={(info) => {
          const originalEvent = info.event.extendedProps.originalEvent;
          if (originalEvent && onEventClick) {
            onEventClick(originalEvent);
          }
        }}
        eventContextMenu={(info) => {
          info.jsEvent.preventDefault();
          const originalEvent = info.event.extendedProps.originalEvent;
          if (originalEvent && onEventContextMenu) {
            onEventContextMenu(originalEvent, {
              x: info.jsEvent.clientX,
              y: info.jsEvent.clientY,
            });
          }
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

- [ ] **Step 3: 运行全部前端测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run
```

Expected: 所有测试通过

- [ ] **Step 4: 提交**

```bash
git add frontend/
git commit -m "feat: integrate event CRUD operations into calendar page"
```

---

## Task 7: 完整验证

- [ ] **Step 1: 后端全量测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest -v --tb=short
```

Expected: 所有测试通过

- [ ] **Step 2: 前端全量测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run
```

Expected: 所有测试通过

- [ ] **Step 3: 手动 E2E 验证**

1. 登录 → 日历页面显示 mock 事件
2. 点击"+ 新建事件" → 填写表单 → 创建成功
3. 点击已有事件 → 弹出编辑模态框 → 修改保存
4. 右键点击事件 → 上下文菜单 → 删除
5. 拖拽事件 → 时间更新
6. 点击空白格 → 快速创建
7. 搜索功能验证

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "chore: phase 4 complete — event CRUD with modal, drag, context menu"
```

---

## 阶段交付物清单

| 交付物 | 状态 |
|--------|------|
| Event + Category SQLAlchemy 模型 | ☐ |
| 数据库迁移 | ☐ |
| Event + Category Pydantic Schema | ☐ |
| EventService + CategoryService | ☐ |
| Event + Category API 路由 | ☐ |
| Event API 集成测试 | ☐ |
| EventForm 组件 | ☐ |
| EventModal 组件 | ☐ |
| EventContextMenu 组件 | ☐ |
| 日历页面事件操作集成 | ☐ |
