# Phase 10: 部署与优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成生产环境部署配置，包含 Docker Compose 生产编排、Nginx 反向代理、HTTPS 证书、PWA 完善、性能优化、阿里云 ECS 部署、最终联调与演示准备。

**Architecture:** Docker Compose 编排 5 个服务（frontend build + backend + PostgreSQL + Redis + Nginx）。Nginx 作为反向代理，前端静态文件由 Nginx 托管。HTTPS 使用 Let's Encrypt 证书。PWA 通过 Service Worker 和 manifest.json 实现可安装。

**Tech Stack:** Docker, Docker Compose, Nginx, Let's Encrypt, Certbot, PWA, React 18 (production build), FastAPI

---

## File Structure

| File | Responsibility |
|------|---------------|
| `docker-compose.prod.yml` | 生产环境 Docker Compose |
| `nginx/nginx.conf` | Nginx 主配置 |
| `nginx/conf.d/default.conf` | 站点配置 |
| `frontend/Dockerfile` | 前端构建 + Nginx 部署 |
| `frontend/public/manifest.json` | PWA manifest（完善） |
| `frontend/public/sw.js` | Service Worker（完善） |
| `frontend/src/App.tsx` | 添加设置路由 |
| `backend/app/main.py` | CORS 配置更新 |
| `deploy/` | 部署脚本目录 |

---

## Task 1: 完善 Docker Compose 生产配置

**Files:**
- Create: `docker-compose.prod.yml`
- Modify: `backend/Dockerfile`
- Create: `frontend/Dockerfile`

- [ ] **Step 1: 创建生产环境 docker-compose.prod.yml**

创建 `docker-compose.prod.yml`：

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    container_name: vocal-calendar-db-prod
    environment:
      POSTGRES_USER: ${DB_USER:-vocal_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME:-vocal_calendar}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-vocal_user} -d ${DB_NAME:-vocal_calendar}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: vocal-calendar-redis-prod
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: vocal-calendar-backend-prod
    environment:
      DATABASE_URL: postgresql://${DB_USER:-vocal_user}:${DB_PASSWORD}@postgres:5432/${DB_NAME:-vocal_calendar}
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      DEBUG: "false"
      CORS_ORIGINS: '["https://${DOMAIN}"]'
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VITE_API_URL: https://${DOMAIN}
    container_name: vocal-calendar-frontend-prod
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: vocal-calendar-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./nginx/ssl:/etc/nginx/ssl
      - ./frontend/dist:/usr/share/nginx/html
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

- [ ] **Step 2: 创建前端 Dockerfile**

创建 `frontend/Dockerfile`：

```dockerfile
# Build stage
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL=
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY --from=build /app/public/sw.js /usr/share/nginx/html/sw.js
COPY --from=build /app/public/manifest.json /usr/share/nginx/html/manifest.json

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 3: 更新后端 Dockerfile**

替换 `backend/Dockerfile`：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run migrations and start server
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

- [ ] **Step 4: 提交**

```bash
git add docker-compose.prod.yml frontend/Dockerfile backend/Dockerfile
git commit -m "chore: add production Docker Compose and Dockerfiles"
```

---

## Task 2: 配置 Nginx 反向代理

**Files:**
- Create: `nginx/nginx.conf`
- Create: `nginx/conf.d/default.conf`

- [ ] **Step 1: 创建 Nginx 主配置**

创建 `nginx/nginx.conf`：

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    include /etc/nginx/conf.d/*.conf;
}
```

- [ ] **Step 2: 创建站点配置**

创建 `nginx/conf.d/default.conf`：

```nginx
# HTTP → HTTPS redirect
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;

    # SSL (Let's Encrypt)
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend static files
    root /usr/share/nginx/html;
    index index.html;

    # API proxy
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket proxy
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

- [ ] **Step 3: 创建 SSL 目录**

```bash
mkdir -p nginx/ssl
```

- [ ] **Step 4: 提交**

```bash
git add nginx/
git commit -m "chore: add Nginx reverse proxy configuration with SSL"
```

---

## Task 3: 创建部署脚本

**Files:**
- Create: `deploy/setup.sh`
- Create: `deploy/deploy.sh`
- Create: `deploy/.env.example`

- [ ] **Step 1: 创建环境变量模板**

创建 `deploy/.env.example`：

```bash
# Database
DB_USER=vocal_user
DB_PASSWORD=your_secure_password_here
DB_NAME=vocal_calendar

# JWT
JWT_SECRET_KEY=your_jwt_secret_here

# Domain
DOMAIN=your-domain.com

# LLM API Keys
LLM_PROVIDER=qwen
QWEN_API_KEY=your_qwen_api_key
OPENAI_API_KEY=your_openai_api_key
GLM_API_KEY=your_glm_api_key

# Weather
QWEATHER_API_KEY=your_qweather_api_key
```

- [ ] **Step 2: 创建服务器初始化脚本**

创建 `deploy/setup.sh`：

```bash
#!/bin/bash
set -e

echo "=== Vocal Calendar Server Setup ==="

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo apt install -y docker-compose-plugin
fi

# Install Certbot for HTTPS
sudo apt install -y certbot

echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Point your domain to this server's IP"
echo "2. Run: sudo certbot certonly --standalone -d your-domain.com"
echo "3. Copy certificates to nginx/ssl/"
echo "4. Run: ./deploy/deploy.sh"
```

- [ ] **Step 3: 创建部署脚本**

创建 `deploy/deploy.sh`：

```bash
#!/bin/bash
set -e

echo "=== Deploying Vocal Calendar ==="

# Check .env
if [ ! -f .env ]; then
    echo "Error: .env file not found. Copy deploy/.env.example to .env and configure."
    exit 1
fi

# Build and start
echo "Building and starting services..."
docker compose -f docker-compose.prod.yml --env-file .env build
docker compose -f docker-compose.prod.yml --env-file .env up -d

# Wait for services
echo "Waiting for services to start..."
sleep 10

# Run migrations
echo "Running database migrations..."
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Check health
echo "Checking service health..."
docker compose -f docker-compose.prod.yml ps

echo "=== Deployment Complete ==="
echo "Visit: https://$(grep DOMAIN .env | cut -d= -f2)"
```

- [ ] **Step 4: 设置脚本权限**

```bash
chmod +x deploy/setup.sh deploy/deploy.sh
```

- [ ] **Step 5: 提交**

```bash
git add deploy/
git commit -m "chore: add deployment scripts and env template"
```

---

## Task 4: 完善 PWA 支持

**Files:**
- Modify: `frontend/public/manifest.json`
- Modify: `frontend/public/sw.js`
- Modify: `frontend/index.html`

- [ ] **Step 1: 完善 manifest.json**

替换 `frontend/public/manifest.json`：

```json
{
  "name": "Vocal Calendar - 语音日历",
  "short_name": "VocalCal",
  "description": "语音驱动的智能日历工具",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#FFFFFF",
  "theme_color": "#4285F4",
  "orientation": "portrait-primary",
  "scope": "/",
  "lang": "zh-CN",
  "categories": ["productivity", "utilities"],
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
```

- [ ] **Step 2: 完善 Service Worker**

替换 `frontend/public/sw.js`：

```javascript
const CACHE_NAME = 'vocal-calendar-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
];

// Install: cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Fetch: network first, fallback to cache
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // Skip API requests
  if (event.request.url.includes('/api/')) return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Cache successful responses
        if (response.ok) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        return caches.match(event.request);
      })
  );
});

// Push notification
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};

  const options = {
    body: data.body || '你有一个提醒',
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-192.png',
    vibrate: [200, 100, 200],
    data: data,
    actions: [
      { action: 'dismiss', title: '关闭' },
      { action: 'view', title: '查看' },
    ],
  };

  event.waitUntil(
    self.registration.showNotification(
      data.title || 'Vocal Calendar',
      options
    )
  );
});

// Notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'dismiss') return;

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

- [ ] **Step 3: 更新 index.html**

修改 `frontend/index.html`，在 `<head>` 中添加：

```html
<link rel="manifest" href="/manifest.json" />
<meta name="theme-color" content="#4285F4" />
<link rel="apple-touch-icon" href="/icons/icon-192.png" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
```

在 `<body>` 前添加注册脚本：

```html
<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then((reg) => console.log('SW registered:', reg.scope))
        .catch((err) => console.error('SW registration failed:', err));
    });
  }
</script>
```

- [ ] **Step 4: 创建图标目录**

```bash
mkdir -p frontend/public/icons
# 注意：需要实际的图标文件，可以用 placeholder 或从设计工具导出
```

- [ ] **Step 5: 提交**

```bash
git add frontend/
git commit -m "feat: complete PWA support with Service Worker and manifest"
```

---

## Task 5: 添加设置页面路由

**Files:**
- Create: `frontend/src/features/settings/SettingsPage.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建设置页面**

创建 `frontend/src/features/settings/SettingsPage.tsx`：

```tsx
import { useAuthStore } from '../../stores/useAuthStore';
import { useThemeStore } from '../../stores/useThemeStore';
import ShareLink from '../share/ShareLink';
import ExportMenu from '../export/ExportMenu';

export default function SettingsPage() {
  const { user, updateTheme } = useAuthStore();
  const { theme, setTheme } = useThemeStore();

  const handleThemeToggle = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    updateTheme(newTheme);
  };

  return (
    <div style={{ padding: 'var(--space-6)', maxWidth: '600px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: 'var(--space-8)', color: 'var(--color-primary)' }}>
        ⚙️ 设置
      </h1>

      {/* Profile Section */}
      <section style={{ marginBottom: 'var(--space-8)' }}>
        <h2 style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--space-4)' }}>
          个人信息
        </h2>
        <div style={{
          padding: 'var(--space-4)',
          background: 'var(--color-surface)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border)',
        }}>
          <div style={{ marginBottom: 'var(--space-3)' }}>
            <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>邮箱</span>
            <p>{user?.email}</p>
          </div>
          <div>
            <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>用户名</span>
            <p>{user?.username}</p>
          </div>
        </div>
      </section>

      {/* Theme Section */}
      <section style={{ marginBottom: 'var(--space-8)' }}>
        <h2 style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--space-4)' }}>
          外观
        </h2>
        <div style={{
          padding: 'var(--space-4)',
          background: 'var(--color-surface)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <p style={{ fontWeight: 500 }}>深色模式</p>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
              {theme === 'dark' ? '已开启' : '已关闭'}
            </p>
          </div>
          <button
            onClick={handleThemeToggle}
            style={{
              padding: 'var(--space-2) var(--space-4)',
              background: theme === 'dark' ? 'var(--color-primary)' : 'var(--color-border)',
              color: theme === 'dark' ? 'var(--color-text-inverse)' : 'var(--color-text)',
              borderRadius: 'var(--radius-full)',
              fontSize: 'var(--font-size-sm)',
              transition: 'all var(--transition-normal)',
            }}
          >
            {theme === 'dark' ? '🌙' : '☀️'}
          </button>
        </div>
      </section>

      {/* Share Section */}
      <section style={{ marginBottom: 'var(--space-8)' }}>
        <h2 style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--space-4)' }}>
          分享
        </h2>
        <ShareLink />
      </section>

      {/* Export Section */}
      <section>
        <h2 style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--space-4)' }}>
          导出
        </h2>
        <ExportMenu />
      </section>
    </div>
  );
}
```

- [ ] **Step 2: 更新 App.tsx**

修改 `frontend/src/App.tsx`，添加设置路由：

```tsx
import SettingsPage from './features/settings/SettingsPage';
```

在 Routes 中添加：

```tsx
<Route
  path="/settings"
  element={
    <AuthGuard>
      <SettingsPage />
    </AuthGuard>
  }
/>
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
git commit -m "feat: add settings page with theme toggle, share, and export"
```

---

## Task 6: 最终验证与演示准备

- [ ] **Step 1: 全量后端测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest -v --tb=short
```

Expected: 所有测试通过

- [ ] **Step 2: 全量前端测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run
```

Expected: 所有测试通过

- [ ] **Step 3: 本地生产构建验证**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npm run build
npx vite preview
```

验证构建产物正常运行

- [ ] **Step 4: Docker 生产构建验证**

```bash
cd /Users/linchengda/Desktop/vocal-calendar
docker compose -f docker-compose.prod.yml build
```

Expected: 所有镜像构建成功

- [ ] **Step 5: 创建演示账户脚本**

创建 `deploy/seed-demo.sh`：

```bash
#!/bin/bash
# 创建演示数据
echo "Creating demo user and events..."

# 通过 API 创建演示账户
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@vocal-calendar.com","username":"演示用户","password":"demo123456"}'

# 登录获取 token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@vocal-calendar.com","password":"demo123456"}' | jq -r '.data.access_token')

# 创建示例事件
curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"项目评审会议","start_time":"2026-06-01T10:00:00Z","end_time":"2026-06-01T11:30:00Z","location":"会议室A","color":"#4285F4"}'

curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"午餐约会","start_time":"2026-06-01T12:00:00Z","end_time":"2026-06-01T13:00:00Z","color":"#34A853"}'

curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"产品需求讨论","start_time":"2026-06-02T14:00:00Z","end_time":"2026-06-02T15:30:00Z","color":"#FBBC04"}'

echo "Demo data created!"
echo "Login: demo@vocal-calendar.com / demo123456"
```

```bash
chmod +x deploy/seed-demo.sh
```

- [ ] **Step 6: 最终提交**

```bash
git add -A
git commit -m "chore: phase 10 complete — deployment, PWA, and final polish

- Docker Compose production configuration
- Nginx reverse proxy with SSL
- Deployment scripts
- PWA support (Service Worker, manifest)
- Settings page
- Demo data seeding script"
```

- [ ] **Step 7: 创建 Git Tag**

```bash
git tag -a v1.0.0 -m "v1.0.0: Vocal Calendar - Full feature release"
```

---

## 阶段交付物清单

| 交付物 | 状态 |
|--------|------|
| Docker Compose 生产配置 | ☐ |
| 前端 Dockerfile | ☐ |
| 后端 Dockerfile 更新 | ☐ |
| Nginx 配置 | ☐ |
| 部署脚本 | ☐ |
| 环境变量模板 | ☐ |
| PWA manifest 完善 | ☐ |
| Service Worker 完善 | ☐ |
| 设置页面 | ☐ |
| 演示数据脚本 | ☐ |
| Git Tag v1.0.0 | ☐ |

## PR 提交规范提醒

每个 Task 完成后提交 commit，格式：
- `feat:` 新功能
- `fix:` 修复
- `chore:` 构建/工具
- `docs:` 文档

## Git 要求提醒

- 使用 conventional commits 格式
- 最终打 tag 标记版本
- 保持主分支可运行状态

## 部署到阿里云 ECS

1. 购买 ECS（2核4G）
2. 域名解析到 ECS IP
3. SSH 登录，运行 `deploy/setup.sh`
4. 配置 SSL 证书：`sudo certbot certonly --standalone -d your-domain.com`
5. 复制证书到 `nginx/ssl/`
6. 配置 `.env` 文件
7. 运行 `deploy/deploy.sh`
8. 运行 `deploy/seed-demo.sh` 创建演示数据
9. 访问 https://your-domain.com 验证
