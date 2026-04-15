# 部署与发布指南

## 1. 当前状态与生产差距分析 (Gaps Analysis)

### 已就绪

| 项目 | 状态 |
|------|------|
| 后端 FastAPI + SQLModel + SQLite | 功能完整，测试通过 |
| 前端微信小程序 | 核心功能可用，Jest 测试通过 |
| ISBN 解析（Open Library 真实数据源） | 已接入 |
| CI 测试（GitHub Actions） | push/PR 时自动跑后端 + 前端测试 |
| Docker 镜像构建（GHCR） | 打 tag 自动构建并推送 |
| 环境变量管理 | `.env` + `local.env`（微信密钥不提交） |

### 已知差距（已记录待解决）

| 缺口 | 说明 | 优先级 |
|------|------|--------|
| 前端 BASE_URL 环境区分 | `miniprogram/utils/config.js` 中 `BASE_URL` 硬编码本地地址，无开发/生产切换机制 | 高 |
| HTTPS / 域名 | 微信小程序要求后端 API 必须 HTTPS | 高 |
| 微信正式环境密钥 | `WECHAT_APP_ID` / `WECHAT_APP_SECRET` 需配置为正式环境值 | 高 |
| CORS 生产域名 | `CORS_ORIGINS` 需加入生产域名 | 中 |
| 速率限制 | 后端无 API 限流 middleware，生产可能被刷 | 中 |
| 数据库迁移工具 | 无 alembic，手动改模型后需手动处理 SQLite schema | 低 |
| 结构化日志 | FastAPI/uvicorn 有基础请求日志，但无结构化日志（JSON 格式）和监控告警 | 低 |
| 小程序自动上传体验版 | 当前仅 CI 跑测试，未接入微信 CI 自动上传 | 低 |

> **生产数据库**: SQLite + 持久化卷对家庭/个人项目已够用，PostgreSQL 为可选升级项而非必须。

---

## 2. 持续集成与发布 (CI/CD)

本项目的 CI/CD 全部由 GitHub Actions 管理，以下三个 workflow 归口管理：

### 2.1 CI 测试（`.github/workflows/ci.yml`）

**触发条件**: push 或 PR 到 `main` 分支

| Job | 环境 | 命令 |
|-----|------|------|
| backend-tests | Python 3.12 | `pytest tests/ -v --tb=short` |
| miniprogram-tests | Node.js 20 | `npm test` |

两个 job 并行运行，互不依赖。测试使用内存 SQLite 和 mock 微信 API，不需要真实数据库或网络。

### 2.2 Release 构建（`.github/workflows/release.yml`）

**触发条件**: 推送 `v*` 格式的 tag（如 `v0.1.0`）

| 步骤 | Action | 说明 |
|------|--------|------|
| 1 | setup-buildx-action | 启用 containerd driver（支持 GHA cache） |
| 2 | login-action | 登录 GHCR |
| 3 | metadata-action | 生成镜像 tag（`<version>` + `latest`） |
| 4 | build-push-action | 构建并推送 Docker 镜像 |

**产出镜像**: `ghcr.io/cristinazhang/family-reading:<version>` + `:latest`

### 2.3 小程序自动上传（待实现）

**计划 workflow**: `.github/workflows/miniprogram-ci.yml`

通过微信官方 `miniprogram-ci` 工具在 CI 中自动上传体验版。

**前置条件**:
- 获取微信公众平台 CI 上传密钥（`.private.key`，不提交到 git）
- 在 GitHub Secrets 中配置 `WECHAT_CI_KEY` 和 `WECHAT_APP_ID`
- `miniprogram/package.json` 中添加 `miniprogram-ci` 依赖

### 2.4 如何触发

```bash
# 推送代码到 main（触发 CI 测试）
git push origin main

# 打 tag（触发 Release 构建）
git tag v0.1.0 && git push --tags

# 如需重新触发 release（删除旧 tag 后重建）
git tag -d v0.1.0 && git push --delete origin v0.1.0
git tag v0.1.0 && git push --tags
```

---

## 3. 系统架构

### 3.1 全系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        微信小程序 (Miniprogram)                      │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │  login   │  │   home   │  │ scan_add │  │reading_  │           │
│  │          │◀─┤          │──▶│          │  │list/detail│           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
│       │              │              │              │                │
│  ┌────┴──────────────┴──────────────┴──────────────┴─────┐         │
│  │  utils/api.js  (wx.request + Bearer token 注入)        │         │
│  │  utils/config.js  (BASE_URL 配置)                      │         │
│  └────────────────────────┬──────────────────────────────┘         │
└────────────────────────────┼───────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                               │
│                                                                     │
│  ┌───────────────────┐  ┌───────────────────────────────┐          │
│  │  CORS Middleware  │  │  Auth Middleware               │          │
│  │  (跨域处理)       │  │  (Bearer token → AuthUser)     │          │
│  └────────┬──────────┘  └──────────────┬────────────────┘          │
│           └──────────────┬─────────────┘                            │
│                          ▼                                          │
│  ┌───────────────────────────────────────────────────────┐         │
│  │                    Routers (API)                       │         │
│  │                                                       │         │
│  │  auth.py     POST /v1/auth/wechat/login               │         │
│  │              POST /v1/auth/dev/login                  │         │
│  │                                                       │         │
│  │  families.py POST /v1/families                        │         │
│  │              GET  /v1/families                        │         │
│  │              POST /v1/families/{id}/members           │         │
│  │              GET  /v1/families/{id}/members           │         │
│  │                                                       │         │
│  │  books.py    POST /v1/books/resolve  (ISBN 查询)      │         │
│  │              POST /v1/books          (手动创建)        │         │
│  │                                                       │         │
│  │  book_copies.py                                      │         │
│  │  readings.py  POST/PATCH/GET /v1/readings             │         │
│  │  dashboard.py GET /v1/families/{id}/dashboard         │         │
│  └───────────────────────┬───────────────────────────────┘         │
│                          │                                          │
│  ┌───────────────────────┴───────────────────────────────┐         │
│  │                  Services Layer                        │         │
│  │                                                       │         │
│  │  isbn.py         ISBN 校验/转换 (10→13)               │         │
│  │  book_provider.py ISBN 元数据解析 (Open Library API)  │         │
│  └───────────────────────┬───────────────────────────────┘         │
│                          │                                          │
│  ┌───────────────────────┴───────────────────────────────┐         │
│  │                  Database Layer                        │         │
│  │                                                       │         │
│  │  database.py    SQLModel engine + session + init_db   │         │
│  │  models.py      User / Family / FamilyMember          │         │
│  │                 BookMeta / BookCopy / Reading          │         │
│  └───────────────────────┬───────────────────────────────┘         │
└────────────────────────────┼───────────────────────────────────────┘
                             │ SQLModel ORM
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      数据库 (SQLite / PostgreSQL)                     │
│                                                                     │
│  users │ families │ family_members │ book_metas │ book_copies      │
│  │ readings                                                        │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  Open Library API    │  ← 外部服务 (ISBN 元数据解析)
│  (book_provider.py)  │
└──────────────────────┘
```

### 3.2 小程序模块依赖图

```
miniprogram/
├── app.js / app.json                    # 入口 & 全局配置
├── utils/
│   ├── config.js                        # BASE_URL 配置（需支持环境区分）
│   └── api.js                           # HTTP 请求封装 (wx.request + token)
├── pages/
│   ├── login/                           # 登录页
│   ├── home/                            # 主入口（家庭看板）
│   ├── scan_add/                        # ISBN 扫码添加
│   ├── reading_list/                    # 阅读记录列表
│   ├── reading_detail/                  # 阅读详情 & 进度更新
│   ├── family/                          # 家庭 & 成员管理
│   └── settings/                        # 设置
└── __tests__/                           # Jest 测试
    ├── api.test.js
    └── page_logic.test.js
```

### 3.3 页面流程图

```
┌─────────────┐
│   Login     │  ← 微信授权登录 / 开发态登录
│ pages/login │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│    Home     │────▶│   Family Mgmt    │────▶│ pages/family     │
│ pages/home  │◀────│ (设置页面入口)    │     │ 成员管理          │
└──────┬──────┘     └──────────────────┘     └──────────────────┘
       │
       ├──▶ ┌──────────────────┐     ┌──────────────────┐
       │    │   Scan & Add     │────▶│ pages/scan_add   │
       │    │                  │     │ 扫一扫添加书籍     │
       │    └──────────────────┘     └──────────────────┘
       │
       ├──▶ ┌──────────────────┐     ┌──────────────────┐
       │    │ Reading List     │────▶│ pages/reading_list│
       │    │                  │     │ 阅读记录列表       │
       │    └────────┬─────────┘     └──────────────────┘
       │             │
       │             ▼
       │    ┌──────────────────┐
       │    │ Reading Detail   │  ← 更新进度/状态/笔记
       │    │ pages/reading_   │
       │    │ detail           │
       │    └──────────────────┘
       │
       └──▶ ┌──────────────────┐
            │    Settings      │  ← API 地址配置（开发态）
            │ pages/settings   │
            └──────────────────┘
```

---

## 4. 微信小程序发布流程

微信小程序无法完全通过 CI 自动发布（需要微信开发者工具），但可以做到 CI 保障代码质量 + 半自动上传。

### 4.1 当前流程（手动）

1. 打开**微信开发者工具**，导入 `miniprogram/` 目录
2. 填写 AppID（在 `project.config.json` 中配置）
3. 点击**上传**，填写版本号和备注
4. 在[微信公众平台](https://mp.weixin.qq.com/)提交审核 → 发布

### 4.2 可选的 CI 自动上传（miniprogram-ci）

详见 [2.3 小程序自动上传（待实现）](#23-小程序自动上传待实现) 中的 workflow 示例。

---

## 5. 部署方案

### 5.1 方案对比

| 方案 | 复杂度 | 成本 | 适用场景 |
|------|--------|------|----------|
| PaaS (Railway/Render) | 低 | 低 | 个人/家庭项目，快速上线 |
| 自有云服务器 (ECS/VPS) | 中 | 中 | 已有服务器，需要完全控制 |
| 容器编排 (K8s) | 高 | 高 | 多实例、高可用场景 |

### 5.2 方案 A: PaaS 部署（推荐 MVP）

以 Railway 为例：

```bash
# 1. 安装 Railway CLI
npm i -g @railway/cli
railway login

# 2. 初始化项目
cd backend
railway init

# 3. 设置环境变量
railway variables set DATABASE_URL=sqlite:///./data/app.db
railway variables set APP_ENV=prod
railway variables set APP_DEBUG=0
railway variables set WECHAT_APP_ID=wx...
railway variables set WECHAT_APP_SECRET=...

# 4. 部署
railway up
```

### 5.3 方案 B: 自有服务器 + Docker

```bash
# 1. 在服务器上拉取镜像
docker pull ghcr.io/cristinazhang/family-reading:latest

# 2. 准备环境文件
cat > /opt/family-reading/.env <<EOF
APP_ENV=prod
APP_DEBUG=0
DATABASE_URL=sqlite:///./data/app.db
WECHAT_APP_ID=wx...
WECHAT_APP_SECRET=...
CORS_ORIGINS=https://yourdomain.com
EOF

# 3. 运行容器
docker run -d \
  --name family-reading \
  -p 8000:8000 \
  --env-file /opt/family-reading/.env \
  -v /opt/family-reading/data:/app/data \
  ghcr.io/cristinazhang/family-reading:latest

# 4. 配置 Nginx 反向代理 + HTTPS（Let's Encrypt）
```

**Nginx 配置示例**:

```nginx
server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5.4 部署后 checklist

- [ ] `APP_ENV=prod`, `APP_DEBUG=0`
- [ ] 微信正式环境密钥已配置
- [ ] CORS 包含生产域名
- [ ] HTTPS 证书有效（小程序要求）
- [ ] 数据库持久化卷已挂载
- [ ] 小程序后端域名已更新为生产地址
- [ ] 微信公众平台服务器域名已配置（mp.weixin.qq.com → 开发管理 → 开发设置 → 服务器域名）

---

## 6. 数据库迁移策略

当前使用 SQLite，如需迁移到 PostgreSQL：

1. 更新 `DATABASE_URL` 环境变量：
   ```
   DATABASE_URL=postgresql+psycopg://user:pass@host:5432/family_reading
   ```
2. 安装 psycopg 驱动：
   ```bash
   pip install psycopg[binary]
   ```
3. 在 `backend/app/db/database.py` 中 `SQLModel.metadata.create_all(engine)` 会自动建表
4. 对于已有数据的迁移，考虑使用 `sqlite3` 导出 + `pgloader` 导入

> **注意**: 生产环境建议引入 alembic 做 schema 迁移管理。

---

## 7. Release 工作流扩展（TODO）

当前 release workflow 只构建 Docker 镜像，部署逻辑已预留（见 `.github/workflows/release.yml` 末尾注释部分）。选定部署方案后，取消注释并填入具体步骤即可。

可选扩展：
- 部署成功后自动发送 Slack/飞书通知
- 运行冒烟测试验证部署健康
- 自动更新 `docs/TODO.md` 中的部署状态
