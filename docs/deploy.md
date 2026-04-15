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

## 2. GitHub Actions 工作流

### 2.1 CI 工作流（`.github/workflows/ci.yml`）

**触发条件**: push 或 PR 到 `main` 分支

**运行内容**:
- **backend-tests**: Python 3.12, 安装依赖, 运行 `pytest tests/ -v --tb=short`
- **miniprogram-tests**: Node.js 20, 安装依赖, 运行 `npm test`

两个 job 并行运行，互不依赖。测试使用内存 SQLite 和 mock 微信 API，不需要真实数据库或网络。

### 2.2 Release 工作流（`.github/workflows/release.yml`）

**触发条件**: 推送 `v*` 格式的 tag（如 `v0.1.0`）

**运行内容**:
1. `docker/setup-buildx-action` — 启用 containerd driver（支持 GHA cache）
2. `docker/login-action` — 登录 GHCR
3. `docker/metadata-action` — 生成镜像 tag（`v0.1.0` + `latest`）
4. `docker/build-push-action` — 构建并推送 Docker 镜像

**产出镜像**:
- `ghcr.io/cristinazhang/family-reading:v0.1.0`
- `ghcr.io/cristinazhang/family-reading:latest`

**镜像信息**:
- 基于 `python:3.12-slim`
- 非 root 用户运行（安全性）
- 暴露端口 8000
- 启动命令: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### 2.3 如何触发

```bash
# 1. 确保代码已提交并推送到 main
git push origin main

# 2. 打 tag 并推送
git tag v0.1.0
git push --tags

# 3. 如需重新触发（删除旧 tag 后重建）
git tag -d v0.1.0
git push --delete origin v0.1.0
git tag v0.1.0
git push --tags
```

---

## 3. 小程序架构

### 3.1 页面流程图

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

### 3.2 模块依赖图

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

### 3.3 API 调用关系

```
┌──────────────┐         ┌─────────────────────────────────────────────┐
│  Miniprogram │         │  Backend (FastAPI)                          │
│              │         │                                             │
│ login        │────────▶│ POST /v1/auth/wechat/login                  │
│              │         │ POST /v1/auth/dev/login                     │
│              │         │                                             │
│ home         │────────▶│ GET  /v1/families                           │
│              │         │ GET  /v1/families/{id}/dashboard            │
│              │         │ GET  /v1/families/{id}/members              │
│              │         │                                             │
│ scan_add     │────────▶│ POST /v1/books/resolve  (ISBN 查询)         │
│              │         │ POST /v1/books          (手动创建)           │
│              │         │ POST /v1/readings       (创建阅读记录)       │
│              │         │                                             │
│ reading_list │────────▶│ GET  /v1/families/{id}/readings             │
│              │         │                                             │
│ reading_detail│────────▶│ PATCH /v1/readings/{id}  (更新进度/状态)    │
│              │         │ DELETE /v1/readings/{id}  (删除记录)         │
│              │         │                                             │
│ family       │────────▶│ POST /v1/families                           │
│              │         │ POST /v1/families/{id}/members              │
└──────────────┘         └─────────────────────────────────────────────┘
```

---

## 4. 微信小程序发布流程

微信小程序无法完全通过 CI 自动发布（需要微信开发者工具），但可以做到 CI 保障代码质量 + 半自动上传。

### 3.1 当前流程（手动）

1. 打开**微信开发者工具**，导入 `miniprogram/` 目录
2. 填写 AppID（在 `project.config.json` 中配置）
3. 点击**上传**，填写版本号和备注
4. 在[微信公众平台](https://mp.weixin.qq.com/)提交审核 → 发布

### 3.2 可选的 CI 自动上传（minci）

微信官方提供 [miniprogram-ci](https://developers.weixin.qq.com/miniprogram/dev/devtools/ci.html) 工具，可通过 CI 自动上传体验版。

**前置条件**:
- 在微信公众平台获取 **CI 上传密钥**（开发管理 → 开发设置 → 代码上传）
- 下载密钥文件（`.private.key`），**不要提交到 git**

**步骤**:

```bash
# 1. 安装 miniprogram-ci
cd miniprogram
npm install --save-dev miniprogram-ci

# 2. 将密钥文件放到安全位置（不提交）
# 放在 miniprogram/.private.key 或通过 GitHub Secrets 传入

# 3. 在 CI 中添加 workflow（可选，见下方示例）
```

**GitHub Actions 示例**（添加到 `.github/workflows/miniprogram-ci.yml`）:

```yaml
name: Miniprogram Upload

on:
  push:
    tags:
      - "v*"

jobs:
  upload:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install dependencies
        working-directory: miniprogram
        run: npm ci

      - name: Upload to WeChat
        working-directory: miniprogram
        env:
          WX_CI_KEY: ${{ secrets.WECHAT_CI_KEY }}
          WX_APPID: ${{ secrets.WECHAT_APP_ID }}
        run: |
          # 使用 miniprogram-ci 上传体验版
          # 需要先在项目中配置好 miniprogram-ci
          echo "Upload step - configure miniprogram-ci as needed"
```

> **注意**: 需要在 GitHub Settings → Secrets 中配置 `WECHAT_CI_KEY` 和 `WECHAT_APP_ID`。

---

## 5. 部署方案

### 4.1 方案对比

| 方案 | 复杂度 | 成本 | 适用场景 |
|------|--------|------|----------|
| PaaS (Railway/Render) | 低 | 低 | 个人/家庭项目，快速上线 |
| 自有云服务器 (ECS/VPS) | 中 | 中 | 已有服务器，需要完全控制 |
| 容器编排 (K8s) | 高 | 高 | 多实例、高可用场景 |

### 4.2 方案 A: PaaS 部署（推荐 MVP）

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

### 4.3 方案 B: 自有服务器 + Docker

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

### 4.4 部署后 checklist

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
3. 在 `backend/app/db/database.py` 中添加 `SQLModel.metadata.create_all(engine)`（已存在）
4. 对于已有数据的迁移，考虑使用 `sqlite3` 导出 + `pgloader` 导入

> **注意**: 生产环境建议引入 alembic 做 schema 迁移管理。

---

## 7. Release 工作流扩展（TODO）

当前 release workflow 只构建 Docker 镜像，部署逻辑已预留（见 `release.yml` 末尾注释部分）。选定部署方案后，取消注释并填入具体步骤即可。

可选扩展：
- 部署成功后自动发送 Slack/飞书通知
- 运行冒烟测试验证部署健康
- 自动更新 `docs/TODO.md` 中的部署状态
