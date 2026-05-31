# Phase 2: 用户认证系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现完整的用户认证系统，包含注册、登录、JWT Token 刷新、用户信息管理、前端登录/注册页面、AuthGuard 路由守卫。

**Architecture:** 后端使用 bcrypt 加密密码、PyJWT 生成/验证 Token，access_token 30 分钟 + refresh_token 7 天。前端使用 Zustand 管理认证状态，axios 拦截器自动附加 Token 和处理 401。

**Tech Stack:** FastAPI, SQLAlchemy 2.0, PyJWT, bcrypt, React 18, Zustand, React Router v6, axios, react-hook-form, zod, Vitest

---

## File Structure

### Backend Files

| File | Responsibility |
|------|---------------|
| `backend/app/models/__init__.py` | 模型包初始化 |
| `backend/app/models/user.py` | User SQLAlchemy 模型 |
| `backend/app/schemas/__init__.py` | Schema 包初始化 |
| `backend/app/schemas/auth.py` | 认证相关 Pydantic 模型 |
| `backend/app/schemas/user.py` | 用户相关 Pydantic 模型 |
| `backend/app/core/security.py` | JWT + bcrypt 工具函数 |
| `backend/app/services/__init__.py` | 服务包初始化 |
| `backend/app/services/auth_service.py` | 认证业务逻辑 |
| `backend/app/api/auth.py` | 认证路由 |
| `backend/app/api/deps.py` | 依赖注入（get_current_user） |
| `backend/alembic/versions/xxx_create_users.py` | Users 表迁移 |
| `backend/tests/test_auth_service.py` | 认证服务单元测试 |
| `backend/tests/test_auth_api.py` | 认证 API 集成测试 |

### Frontend Files

| File | Responsibility |
|------|---------------|
| `frontend/src/services/api.ts` | axios 实例 + 拦截器 |
| `frontend/src/services/authApi.ts` | 认证 API 调用 |
| `frontend/src/stores/useAuthStore.ts` | 认证状态管理 |
| `frontend/src/features/auth/LoginPage.tsx` | 登录页面 |
| `frontend/src/features/auth/RegisterPage.tsx` | 注册页面 |
| `frontend/src/features/auth/AuthGuard.tsx` | 路由守卫 |
| `frontend/src/features/auth/__tests__/LoginPage.test.tsx` | 登录页测试 |
| `frontend/src/features/auth/__tests__/RegisterPage.test.tsx` | 注册页测试 |

---

## Task 1: 创建 User 模型

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/alembic/versions/001_create_users.py`

- [ ] **Step 1: 创建 models 包**

创建 `backend/app/models/__init__.py`：

```python
from app.models.user import User

__all__ = ["User"]
```

- [ ] **Step 2: 创建 User 模型**

创建 `backend/app/models/user.py`：

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    theme: Mapped[str] = mapped_column(String(20), default="light")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

- [ ] **Step 3: 更新 alembic/env.py 导入模型**

在 `backend/alembic/env.py` 中取消模型导入注释：

```python
from app.models import user  # noqa: F401
```

- [ ] **Step 4: 生成迁移文件**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
alembic revision --autogenerate -m "create users table"
```

- [ ] **Step 5: 执行迁移**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
alembic upgrade head
```

- [ ] **Step 6: 验证表创建**

```bash
docker exec -it vocal-calendar-db psql -U vocal_user -d vocal_calendar -c "\dt"
```

Expected: 输出包含 `users` 表

- [ ] **Step 7: 提交**

```bash
git add backend/
git commit -m "feat: add User model and create users table migration"
```

---

## Task 2: 实现安全工具（JWT + bcrypt）

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/tests/test_security.py`

- [ ] **Step 1: 编写安全工具测试 (RED)**

创建 `backend/tests/test_security.py`：

```python
import pytest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        result = hash_password("mypassword123")
        assert isinstance(result, str)
        assert result != "mypassword123"

    def test_verify_password_correct(self):
        hashed = hash_password("mypassword123")
        assert verify_password("mypassword123", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("mypassword123")
        assert verify_password("wrongpassword", hashed) is False


class TestJWTToken:
    def test_create_access_token(self):
        token = create_access_token({"sub": "user-123"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_create_refresh_token(self):
        token = create_refresh_token({"sub": "user-123"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decode_access_token(self):
        token = create_access_token({"sub": "user-123"})
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_decode_refresh_token(self):
        token = create_refresh_token({"sub": "user-123"})
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        payload = decode_token("invalid.token.here")
        assert payload is None
```

- [ ] **Step 2: 运行测试确认失败 (RED)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_security.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.core.security'`

- [ ] **Step 3: 实现安全工具**

创建 `backend/app/core/security.py`：

```python
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        return None
```

- [ ] **Step 4: 安装 passlib 依赖**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pip install passlib[bcrypt]
echo "passlib[bcrypt]==1.7.4" >> requirements.txt
```

- [ ] **Step 5: 运行测试确认通过 (GREEN)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_security.py -v
```

Expected: `9 passed`

- [ ] **Step 6: 提交**

```bash
git add backend/
git commit -m "feat: implement JWT and bcrypt security utilities with tests"
```

---

## Task 3: 创建认证 Schema 和 Service

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/auth_service.py`
- Create: `backend/tests/test_auth_service.py`

- [ ] **Step 1: 创建 schemas 包**

创建 `backend/app/schemas/__init__.py`：

```python
```

创建 `backend/app/schemas/auth.py`：

```python
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
```

创建 `backend/app/schemas/user.py`：

```python
from pydantic import BaseModel
from datetime import datetime


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    avatar_url: str | None
    theme: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    username: str | None = None
    avatar_url: str | None = None
    theme: str | None = None
```

- [ ] **Step 2: 创建 services 包**

创建 `backend/app/services/__init__.py`：

```python
```

- [ ] **Step 3: 编写 AuthService 测试 (RED)**

创建 `backend/tests/test_auth_service.py`：

```python
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.services.auth_service import AuthService
from app.models.user import User


@pytest.fixture
def db():
    return MagicMock(spec=Session)


@pytest.fixture
def service(db):
    return AuthService(db)


class TestRegister:
    def test_register_new_user(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        result = service.register("test@example.com", "testuser", "password123")

        assert db.add.called
        assert db.commit.called

    def test_register_duplicate_email(self, service, db):
        existing = User(email="test@example.com", username="existing", password_hash="hash")
        db.query.return_value.filter.return_value.first.return_value = existing

        with pytest.raises(ValueError, match="邮箱已被注册"):
            service.register("test@example.com", "newuser", "password123")


class TestLogin:
    def test_login_success(self, service, db):
        from app.core.security import hash_password
        user = User(
            id="user-1",
            email="test@example.com",
            username="testuser",
            password_hash=hash_password("password123"),
        )
        db.query.return_value.filter.return_value.first.return_value = user

        result = service.login("test@example.com", "password123")

        assert "access_token" in result
        assert "refresh_token" in result

    def test_login_wrong_password(self, service, db):
        from app.core.security import hash_password
        user = User(
            id="user-1",
            email="test@example.com",
            username="testuser",
            password_hash=hash_password("password123"),
        )
        db.query.return_value.filter.return_value.first.return_value = user

        with pytest.raises(ValueError, match="邮箱或密码错误"):
            service.login("test@example.com", "wrongpassword")

    def test_login_nonexistent_user(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="邮箱或密码错误"):
            service.login("noone@example.com", "password123")
```

- [ ] **Step 4: 运行测试确认失败 (RED)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_auth_service.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.auth_service'`

- [ ] **Step 5: 实现 AuthService**

创建 `backend/app/services/auth_service.py`：

```python
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, email: str, username: str, password: str) -> User:
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError("邮箱已被注册")

        user = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, email: str, password: str) -> dict:
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("邮箱或密码错误")

        access_token = create_access_token({"sub": user.id})
        refresh_token = create_refresh_token({"sub": user.id})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def refresh(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("无效的刷新令牌")

        user_id = payload["sub"]
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        new_access = create_access_token({"sub": user.id})
        new_refresh = create_refresh_token({"sub": user.id})

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
        }

    def get_user_by_id(self, user_id: str) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def update_user(self, user_id: str, **kwargs) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user
```

- [ ] **Step 6: 运行测试确认通过 (GREEN)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_auth_service.py -v
```

Expected: `5 passed`

- [ ] **Step 7: 提交**

```bash
git add backend/
git commit -m "feat: add auth schemas and AuthService with tests"
```

---

## Task 4: 创建认证 API 路由

**Files:**
- Create: `backend/app/api/deps.py`
- Modify: `backend/app/api/auth.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_auth_api.py`

- [ ] **Step 1: 创建依赖注入**

创建 `backend/app/api/deps.py`：

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.services.auth_service import AuthService
from app.models.user import User

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌",
        )

    user_id = payload["sub"]
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    return user
```

- [ ] **Step 2: 编写认证 API 集成测试 (RED)**

创建 `backend/tests/test_auth_api.py`：

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, Base, engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# 使用测试数据库
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


class TestRegisterAPI:
    def test_register_success(self, client):
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["email"] == "test@example.com"

    def test_register_duplicate_email(self, client):
        client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "another",
            "password": "password123",
        })
        assert response.status_code == 400


class TestLoginAPI:
    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401


class TestMeAPI:
    def test_get_me(self, client):
        client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })
        login_resp = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password123",
        })
        token = login_resp.json()["data"]["access_token"]

        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["email"] == "test@example.com"

    def test_get_me_no_token(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 403
```

- [ ] **Step 3: 运行测试确认失败 (RED)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
# 创建测试数据库
docker exec -it vocal-calendar-db psql -U vocal_user -c "CREATE DATABASE vocal_calendar_test;" 2>/dev/null || true
pytest tests/test_auth_api.py -v
```

Expected: FAIL — `ModuleNotFoundError` 或路由不存在

- [ ] **Step 4: 实现认证路由**

创建 `backend/app/api/auth.py`：

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.auth_service import AuthService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        user = auth_service.register(req.email, req.username, req.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"code": 0, "data": UserResponse.from_orm(user), "message": "注册成功"}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        tokens = auth_service.login(req.email, req.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return {"code": 0, "data": tokens, "message": "登录成功"}


@router.post("/refresh")
def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        tokens = auth_service.refresh(req.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return {"code": 0, "data": tokens, "message": "刷新成功"}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"code": 0, "data": UserResponse.from_orm(current_user), "message": "ok"}


@router.put("/me")
def update_me(
    req: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    auth_service = AuthService(db)
    try:
        user = auth_service.update_user(
            current_user.id,
            username=req.username,
            avatar_url=req.avatar_url,
            theme=req.theme,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"code": 0, "data": UserResponse.from_orm(user), "message": "更新成功"}
```

- [ ] **Step 5: 注册路由到 main.py**

修改 `backend/app/main.py`，在 `app.include_router(health_router)` 后添加：

```python
from app.api.auth import router as auth_router

app.include_router(auth_router)
```

- [ ] **Step 6: 运行测试确认通过 (GREEN)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_auth_api.py -v
```

Expected: `6 passed`

- [ ] **Step 7: 提交**

```bash
git add backend/
git commit -m "feat: add auth API endpoints (register, login, refresh, me) with tests"
```

---

## Task 5: 创建前端 API 服务层

**Files:**
- Create: `frontend/src/services/api.ts`
- Create: `frontend/src/services/authApi.ts`
- Create: `frontend/src/stores/useAuthStore.ts`

- [ ] **Step 1: 安装依赖**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npm install axios zustand
```

- [ ] **Step 2: 创建 axios 实例**

创建 `frontend/src/services/api.ts`：

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach access token
api.interceptors.request.use((config) => {
  const stored = localStorage.getItem('auth-storage');
  if (stored) {
    const { state } = JSON.parse(stored);
    if (state?.accessToken) {
      config.headers.Authorization = `Bearer ${state.accessToken}`;
    }
  }
  return config;
});

// Response interceptor: handle 401 and refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const stored = localStorage.getItem('auth-storage');
      if (stored) {
        const { state } = JSON.parse(stored);
        if (state?.refreshToken) {
          try {
            const resp = await axios.post('/api/auth/refresh', {
              refresh_token: state.refreshToken,
            });
            const { access_token, refresh_token } = resp.data.data;

            // Update stored tokens
            const newState = {
              ...state,
              accessToken: access_token,
              refreshToken: refresh_token,
            };
            localStorage.setItem(
              'auth-storage',
              JSON.stringify({ state: newState })
            );

            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return api(originalRequest);
          } catch {
            localStorage.removeItem('auth-storage');
            window.location.href = '/login';
          }
        }
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

- [ ] **Step 3: 创建 authApi**

创建 `frontend/src/services/authApi.ts`：

```typescript
import api from './api';

interface RegisterParams {
  email: string;
  username: string;
  password: string;
}

interface LoginParams {
  email: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface UserResponse {
  id: string;
  email: string;
  username: string;
  avatar_url: string | null;
  theme: string;
  created_at: string;
}

export const authApi = {
  register: (params: RegisterParams) =>
    api.post<{ code: number; data: UserResponse; message: string }>(
      '/auth/register',
      params
    ),

  login: (params: LoginParams) =>
    api.post<{ code: number; data: TokenResponse; message: string }>(
      '/auth/login',
      params
    ),

  refresh: (refreshToken: string) =>
    api.post<{ code: number; data: TokenResponse; message: string }>(
      '/auth/refresh',
      { refresh_token: refreshToken }
    ),

  getMe: () =>
    api.get<{ code: number; data: UserResponse; message: string }>('/auth/me'),

  updateMe: (data: { username?: string; theme?: string; avatar_url?: string }) =>
    api.put<{ code: number; data: UserResponse; message: string }>(
      '/auth/me',
      data
    ),
};
```

- [ ] **Step 4: 创建 useAuthStore**

创建 `frontend/src/stores/useAuthStore.ts`：

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi } from '../services/authApi';

interface User {
  id: string;
  email: string;
  username: string;
  avatar_url: string | null;
  theme: string;
  created_at: string;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  updateTheme: (theme: string) => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const resp = await authApi.login({ email, password });
        const { access_token, refresh_token } = resp.data.data;
        set({
          accessToken: access_token,
          refreshToken: refresh_token,
          isAuthenticated: true,
        });
        await get().fetchUser();
      },

      register: async (email, username, password) => {
        await authApi.register({ email, username, password });
      },

      logout: () => {
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        });
      },

      fetchUser: async () => {
        try {
          const resp = await authApi.getMe();
          set({ user: resp.data.data });
        } catch {
          get().logout();
        }
      },

      updateTheme: async (theme) => {
        await authApi.updateMe({ theme });
        set((state) => ({
          user: state.user ? { ...state.user, theme } : null,
        }));
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
```

- [ ] **Step 5: 提交**

```bash
git add frontend/
git commit -m "feat: add frontend API layer with axios interceptors and auth store"
```

---

## Task 6: 创建登录和注册页面

**Files:**
- Create: `frontend/src/features/auth/LoginPage.tsx`
- Create: `frontend/src/features/auth/RegisterPage.tsx`
- Create: `frontend/src/features/auth/__tests__/LoginPage.test.tsx`
- Create: `frontend/src/features/auth/__tests__/RegisterPage.test.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 安装依赖**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npm install react-router-dom react-hook-form zod @hookform/resolvers
```

- [ ] **Step 2: 编写登录页测试 (RED)**

创建 `frontend/src/features/auth/__tests__/LoginPage.test.tsx`：

```tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import LoginPage from '../LoginPage';

// Mock useAuthStore
vi.mock('../../../stores/useAuthStore', () => ({
  useAuthStore: () => ({
    login: vi.fn(),
    isAuthenticated: false,
  }),
}));

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('LoginPage', () => {
  it('renders email input', () => {
    renderWithRouter(<LoginPage />);
    expect(screen.getByLabelText(/邮箱/i)).toBeInTheDocument();
  });

  it('renders password input', () => {
    renderWithRouter(<LoginPage />);
    expect(screen.getByLabelText(/密码/i)).toBeInTheDocument();
  });

  it('renders login button', () => {
    renderWithRouter(<LoginPage />);
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
  });

  it('renders register link', () => {
    renderWithRouter(<LoginPage />);
    expect(screen.getByText(/注册/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: 运行测试确认失败 (RED)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run src/features/auth/__tests__/LoginPage.test.tsx
```

Expected: FAIL — `Cannot find module '../LoginPage'`

- [ ] **Step 4: 创建登录页**

创建 `frontend/src/features/auth/LoginPage.tsx`：

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/useAuthStore';
import { useState } from 'react';

const loginSchema = z.object({
  email: z.string().email('请输入有效的邮箱地址'),
  password: z.string().min(6, '密码至少6位'),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { login, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  if (isAuthenticated) {
    navigate('/calendar');
    return null;
  }

  const onSubmit = async (data: LoginForm) => {
    try {
      setError('');
      await login(data.email, data.password);
      navigate('/calendar');
    } catch {
      setError('邮箱或密码错误');
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'var(--color-bg-secondary)',
    }}>
      <div style={{
        background: 'var(--color-surface)',
        padding: 'var(--space-10)',
        borderRadius: 'var(--radius-xl)',
        boxShadow: 'var(--shadow-lg)',
        width: '100%',
        maxWidth: '400px',
      }}>
        <h1 style={{ textAlign: 'center', marginBottom: 'var(--space-2)', color: 'var(--color-primary)' }}>
          Vocal Calendar
        </h1>
        <p style={{ textAlign: 'center', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-8)' }}>
          语音日历工具
        </p>

        {error && (
          <div style={{
            background: '#FEE2E2',
            color: 'var(--color-error)',
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-md)',
            marginBottom: 'var(--space-4)',
            fontSize: 'var(--font-size-sm)',
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)}>
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label htmlFor="email" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
              邮箱
            </label>
            <input
              id="email"
              type="email"
              {...register('email')}
              placeholder="your@email.com"
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                border: `1px solid ${errors.email ? 'var(--color-error)' : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-md)',
                fontSize: 'var(--font-size-base)',
              }}
            />
            {errors.email && (
              <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>
                {errors.email.message}
              </span>
            )}
          </div>

          <div style={{ marginBottom: 'var(--space-6)' }}>
            <label htmlFor="password" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
              密码
            </label>
            <input
              id="password"
              type="password"
              {...register('password')}
              placeholder="••••••"
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                border: `1px solid ${errors.password ? 'var(--color-error)' : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-md)',
                fontSize: 'var(--font-size-base)',
              }}
            />
            {errors.password && (
              <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>
                {errors.password.message}
              </span>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              width: '100%',
              padding: 'var(--space-3)',
              background: 'var(--color-primary)',
              color: 'var(--color-text-inverse)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-base)',
              fontWeight: 600,
              opacity: isSubmitting ? 0.7 : 1,
            }}
          >
            {isSubmitting ? '登录中...' : '登录'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 'var(--space-6)', color: 'var(--color-text-secondary)' }}>
          还没有账户？{' '}
          <Link to="/register" style={{ color: 'var(--color-primary)', fontWeight: 500 }}>
            立即注册
          </Link>
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: 运行登录页测试 (GREEN)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run src/features/auth/__tests__/LoginPage.test.tsx
```

Expected: `4 passed`

- [ ] **Step 6: 创建注册页**

创建 `frontend/src/features/auth/RegisterPage.tsx`：

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/useAuthStore';
import { useState } from 'react';

const registerSchema = z.object({
  email: z.string().email('请输入有效的邮箱地址'),
  username: z.string().min(2, '用户名至少2位'),
  password: z.string().min(6, '密码至少6位'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: '两次密码不一致',
  path: ['confirmPassword'],
});

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const { register: registerUser } = useAuthStore();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterForm) => {
    try {
      setError('');
      await registerUser(data.email, data.username, data.password);
      navigate('/login');
    } catch {
      setError('注册失败，邮箱可能已被使用');
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'var(--color-bg-secondary)',
    }}>
      <div style={{
        background: 'var(--color-surface)',
        padding: 'var(--space-10)',
        borderRadius: 'var(--radius-xl)',
        boxShadow: 'var(--shadow-lg)',
        width: '100%',
        maxWidth: '400px',
      }}>
        <h1 style={{ textAlign: 'center', marginBottom: 'var(--space-2)', color: 'var(--color-primary)' }}>
          创建账户
        </h1>
        <p style={{ textAlign: 'center', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-8)' }}>
          加入 Vocal Calendar
        </p>

        {error && (
          <div style={{
            background: '#FEE2E2',
            color: 'var(--color-error)',
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-md)',
            marginBottom: 'var(--space-4)',
            fontSize: 'var(--font-size-sm)',
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)}>
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label htmlFor="email" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
              邮箱
            </label>
            <input
              id="email"
              type="email"
              {...register('email')}
              placeholder="your@email.com"
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                border: `1px solid ${errors.email ? 'var(--color-error)' : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-md)',
              }}
            />
            {errors.email && (
              <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>
                {errors.email.message}
              </span>
            )}
          </div>

          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label htmlFor="username" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
              用户名
            </label>
            <input
              id="username"
              type="text"
              {...register('username')}
              placeholder="你的名字"
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                border: `1px solid ${errors.username ? 'var(--color-error)' : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-md)',
              }}
            />
            {errors.username && (
              <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>
                {errors.username.message}
              </span>
            )}
          </div>

          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label htmlFor="password" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
              密码
            </label>
            <input
              id="password"
              type="password"
              {...register('password')}
              placeholder="至少6位"
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                border: `1px solid ${errors.password ? 'var(--color-error)' : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-md)',
              }}
            />
            {errors.password && (
              <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>
                {errors.password.message}
              </span>
            )}
          </div>

          <div style={{ marginBottom: 'var(--space-6)' }}>
            <label htmlFor="confirmPassword" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
              确认密码
            </label>
            <input
              id="confirmPassword"
              type="password"
              {...register('confirmPassword')}
              placeholder="再次输入密码"
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                border: `1px solid ${errors.confirmPassword ? 'var(--color-error)' : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-md)',
              }}
            />
            {errors.confirmPassword && (
              <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>
                {errors.confirmPassword.message}
              </span>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              width: '100%',
              padding: 'var(--space-3)',
              background: 'var(--color-primary)',
              color: 'var(--color-text-inverse)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-base)',
              fontWeight: 600,
            }}
          >
            {isSubmitting ? '注册中...' : '注册'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 'var(--space-6)', color: 'var(--color-text-secondary)' }}>
          已有账户？{' '}
          <Link to="/login" style={{ color: 'var(--color-primary)', fontWeight: 500 }}>
            立即登录
          </Link>
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 7: 更新 App.tsx 路由**

替换 `frontend/src/App.tsx`：

```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './features/auth/LoginPage';
import RegisterPage from './features/auth/RegisterPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

- [ ] **Step 8: 运行所有前端测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run
```

Expected: 所有测试通过

- [ ] **Step 9: 提交**

```bash
git add frontend/
git commit -m "feat: add login and register pages with form validation"
```

---

## Task 7: 创建 AuthGuard 路由守卫和设置页面

**Files:**
- Create: `frontend/src/features/auth/AuthGuard.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建 AuthGuard**

创建 `frontend/src/features/auth/AuthGuard.tsx`：

```tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/useAuthStore';
import { ReactNode } from 'react';

interface AuthGuardProps {
  children: ReactNode;
}

export default function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
```

- [ ] **Step 2: 更新 App.tsx 使用 AuthGuard**

替换 `frontend/src/App.tsx`：

```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './features/auth/LoginPage';
import RegisterPage from './features/auth/RegisterPage';
import AuthGuard from './features/auth/AuthGuard';

function CalendarPlaceholder() {
  return <div style={{ padding: '2rem' }}><h1>日历页面 — 即将实现</h1></div>;
}

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
              <CalendarPlaceholder />
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

- [ ] **Step 3: 验证路由守卫**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npm run dev &
sleep 3
curl -s http://localhost:5173/ | grep -o "Vocal Calendar"
kill %1
```

Expected: 页面渲染正常

- [ ] **Step 4: 运行所有测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend && pytest -v
cd /Users/linchengda/Desktop/vocal-calendar/frontend && npx vitest run
```

Expected: 所有测试通过

- [ ] **Step 5: 提交**

```bash
git add frontend/
git commit -m "feat: add AuthGuard route protection and calendar placeholder"
```

---

## Task 8: 完整验证

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

启动前后端，浏览器访问 http://localhost:5173：
1. 自动跳转到 /login
2. 点击"立即注册"→ 注册新用户 → 跳转到 /login
3. 登录 → 跳转到 /calendar
4. 刷新页面 → 保持登录状态

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "chore: phase 2 complete — user authentication system ready"
```

---

## 阶段交付物清单

| 交付物 | 状态 |
|--------|------|
| User SQLAlchemy 模型 | ☐ |
| Users 表迁移 | ☐ |
| JWT + bcrypt 安全工具 | ☐ |
| 认证 Schema（Pydantic） | ☐ |
| AuthService（注册/登录/刷新） | ☐ |
| 认证 API 路由 | ☐ |
| 依赖注入（get_current_user） | ☐ |
| axios 实例 + 拦截器 | ☐ |
| authApi 服务 | ☐ |
| useAuthStore（Zustand） | ☐ |
| 登录页面 | ☐ |
| 注册页面 | ☐ |
| AuthGuard 路由守卫 | ☐ |

## PR 提交规范提醒

每个 Task 完成后提交 commit，格式：
- `feat:` 新功能
- `test:` 测试
- `chore:` 构建/工具

## Git 要求提醒

- 每个 commit 对应完整、可运行的变更
- 使用 conventional commits 格式
