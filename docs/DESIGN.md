# 家庭阅读记录系统（微信扫一扫）设计文档

## 1. Feature description

本系统用于家庭场景下的“阅读书目记录与洞察”，核心目标是：

- **记录**：家人读了什么书、何时开始/结束、当前阅读状态与进度。
- **沉淀元数据**：基于微信“扫一扫”识别 ISBN/条码，自动补全书籍元数据（书名、作者、封面、出版社等）。
- **记录来源**：每一本实体书（副本）在家庭中的来源记录（购买/赠送/学校发放等）。

非目标：

- 不做“借阅给他人”的借还管理（不记录外借/归还给非家庭成员）。

## 2. Scope（MVP）

- **微信小程序**
  - 微信登录（获取 code，后端换 token）
  - 创建/加入家庭
  - 成员管理（MVP：家庭内“成员档案”可独立于微信用户，用于记录儿童等）
  - 扫一扫录入书籍：ISBN 解析→拉取元数据→创建阅读条目
  - 阅读条目：状态（想读/在读/读完/搁置/重读）+ 进度（页码/百分比）+ 开始/结束日期
  - 来源记录：创建 BookCopy（购入/赠送等）并关联到阅读条目（可选）
  - 家庭阅读看板：按成员聚合（在读/读完/想读）
- **后端 API**
  - WeChat 登录换 token（MVP：开发态可用“伪登录”开关）
  - 家庭/成员/书籍元数据/副本/阅读条目的 CRUD
  - ISBN 元数据解析（MVP：先做可插拔 provider；默认 provider 为占位返回，可后续接入真实数据源）

## 3. Key user flows

### 3.1 扫码添加阅读条目

1. 小程序点击“扫一扫添加”
2. `wx.scanCode` 获取 `result`
3. 前端解析 ISBN（支持 ISBN-10/ISBN-13 校验；不通过则进入“手动录入 ISBN/书名”）
4. 调用后端 `POST /v1/books/resolve`：
   - 若 `BookMeta` 已存在，直接返回
   - 否则调用“元数据 Provider”拉取并缓存
5. 用户选择：
   - 成员（member）
   - 状态（默认：在读）
   - 开始日期（可选）
   - 来源（可选：创建一条 BookCopy）
6. 提交 `POST /v1/readings`

### 3.2 更新阅读状态/进度

1. 打开“在读”列表
2. 进入条目详情或在列表快捷更新
3. 更新 `status/progress/lastReadAt/finishedAt`

### 3.3 查看洞察

MVP 洞察：

- 按成员统计：读完数量（本月/今年）、在读数量
- 最近读完列表

## 4. Data model

> 说明：MVP 采用 **BookCopy** 记录来源；阅读条目可关联 `book_copy_id`（可空），保证“来源记录”与“阅读记录”都能独立存在。

### 4.1 Entities

- `User`：微信用户（登录主体）
- `Family`：家庭空间
- `FamilyMember`：家庭成员档案（用于记录家人/孩子；可选绑定 `User`）
- `BookMeta`：书籍元数据（按 ISBN 聚合）
- `BookCopy`：家庭内实体书副本（来源记录在此）
- `Reading`：阅读条目（谁读什么、状态、开始/结束日期、进度）

### 4.2 Fields（核心字段）

#### `FamilyMember`
- `id`
- `family_id`
- `display_name`
- `avatar_url`（可选）
- `bound_user_id`（可选：绑定微信登录用户）
- `created_at`

#### `BookMeta`
- `id`
- `isbn13`（唯一，优先存 13 位；10 位入参转换后写入）
- `title`
- `authors`（数组/逗号分隔均可；MVP 用 JSON 数组）
- `publisher`、`pub_date`（可选）
- `cover_url`、`summary`（可选）
- `categories`（可选）
- `raw_json`（provider 原始结果，用于排错/补全）
- `created_at`

#### `BookCopy`（来源）
- `id`
- `family_id`
- `book_meta_id`
- `acquired_type`：`purchase | gift | school | library | other`
- `acquired_at`（可选）
- `acquired_from`（渠道/赠送人等，字符串）
- `price_cny`（可选）
- `note`（可选）
- `created_at`

#### `Reading`
- `id`
- `family_id`
- `member_id`
- `book_meta_id`
- `book_copy_id`（可选）
- `status`：`wishlist | reading | finished | paused | rereading`
- `started_on`（日期，可选）
- `finished_on`（日期，可选）
- `last_read_on`（日期，可选）
- `progress_type`：`page | percent`
- `progress_value`（整数；percent 0-100）
- `note`（可选）
- `created_at`
- `updated_at`

### 4.3 Constraints（约束）

- `BookMeta.isbn13` 唯一
- 同一家庭同一成员同一本书允许多条 `Reading`（重读场景），但可通过业务层提供“当前在读唯一”快捷逻辑：
  - 约束建议：同 `(family_id, member_id, book_meta_id)` 在 `status=reading` 时最多 1 条（MVP 先不加 DB 层硬约束，避免迁移复杂）

## 5. API design（REST）

### 5.1 Auth

- `POST /v1/auth/wechat/login`
  - 请求：`{ code: string }`
  - 响应：`{ access_token: string, user: {...} }`

> 开发态开关：允许 `POST /v1/auth/dev/login { openid: string }`

### 5.2 Families & Members

- `POST /v1/families`
- `GET /v1/families`
- `POST /v1/families/{family_id}/members`
- `GET /v1/families/{family_id}/members`

### 5.3 Books

- `POST /v1/books/resolve`
  - 请求：`{ isbn: string }`
  - 响应：`BookMeta`

### 5.4 BookCopies（来源）

- `POST /v1/families/{family_id}/book_copies`
- `GET /v1/families/{family_id}/book_copies?book_meta_id=...`

### 5.5 Readings

- `POST /v1/readings`
- `GET /v1/families/{family_id}/readings?member_id=&status=&q=`
- `PATCH /v1/readings/{reading_id}`

### 5.6 Dashboard / Stats（MVP）

- `GET /v1/families/{family_id}/dashboard`
  - 按成员聚合：在读/读完/想读数量 + 最近读完

## 6. MiniProgram pages（建议）

- `pages/home`：家庭选择 + 看板入口
- `pages/scan_add`：扫一扫→确认→创建 Reading
- `pages/reading_list`：按状态列表（想读/在读/读完/搁置）
- `pages/reading_detail`：更新状态/进度/开始结束日期、关联来源
- `pages/book_detail`：书籍元数据 + 家庭内来源列表
- `pages/family`：成员管理
- `pages/settings`：API 地址配置（开发态）

## 7. Testability & test strategy（MVP）

- **单元测试（后端）**
  - ISBN 规范化与校验（10→13 转换、校验位）
  - Reading 状态流转（reading→finished）
- **接口测试**
  - resolve→create reading 的端到端（SQLite）
- **小程序手工测试**
  - 扫码识别 ISBN 成功与失败兜底
  - 创建/更新 reading

## 8. Deployment（概览）

本项目提供：

- 本地开发：后端 `uvicorn` + 小程序开发者工具
- 容器部署：Dockerfile + docker compose（默认 SQLite 持久化卷；可切换 Postgres）

详见：`family-reading/README.md` 与 `family-reading/backend/README.md`

