# API 测试文档

## 测试文件结构

```
backend/
├── tests/
│   ├── conftest.py          # 测试配置文件
│   ├── test_auth.py         # 认证相关测试
│   ├── test_families.py     # 家庭相关测试
│   └── test_books.py        # 书籍相关测试
├── requirements.txt         # 项目依赖
└── app/                     # 应用代码
    ├── main.py              # 应用入口
    ├── routers/             # API路由
    ├── db/                  # 数据库相关
    └── services/            # 业务逻辑服务
```

## 测试环境配置

### 依赖安装
```bash
# 安装所有依赖
pip install -r requirements.txt

# 核心依赖
fastapi[all]        # FastAPI框架及其所有依赖
uvicorn[standard]   # ASGI服务器
sqlmodel            # SQL数据库ORM
pydantic-settings   # 配置管理

# 测试依赖
pytest              # 测试框架
httpx               # HTTP客户端
pytest-cov          # 测试覆盖率工具

# 其他依赖
python-dotenv       # 环境变量管理
```

### 测试数据库
- 使用**内存SQLite**数据库进行测试，确保测试隔离
- 每次测试都会自动创建和销毁数据库
- 无需手动配置数据库连接

## 测试用例

### 1. 认证测试 (`test_auth.py`)

#### 1.1 开发登录测试
- **测试目标**：验证开发登录接口是否正常工作
- **请求**：`POST /v1/auth/dev/login`
- **请求体**：`{"openid": "test_user_123"}`
- **预期响应**：
  - 状态码：200 OK
  - 响应体：包含`access_token`、`token_type`和`user`信息

#### 1.2 空openid测试
- **测试目标**：验证空openid时的错误处理
- **请求**：`POST /v1/auth/dev/login`
- **请求体**：`{"openid": ""}`
- **预期响应**：
  - 状态码：400 Bad Request
  - 响应体：`{"detail": "openid required"}`

#### 1.3 微信登录测试
- **测试目标**：验证微信登录接口是否正确返回未实现状态
- **请求**：`POST /v1/auth/wechat/login`
- **请求体**：`{"code": "test_code"}`
- **预期响应**：
  - 状态码：501 Not Implemented
  - 响应体：包含"not implemented"的错误信息

#### 1.4 健康检查测试
- **测试目标**：验证健康检查接口是否正常工作
- **请求**：`GET /health`
- **预期响应**：
  - 状态码：200 OK
  - 响应体：`{"status": "ok"}`

### 2. 家庭测试 (`test_families.py`)

#### 2.1 创建家庭测试
- **测试目标**：验证创建家庭接口是否正常工作
- **请求**：`POST /v1/families`
- **请求头**：`Authorization: Bearer <token>`
- **请求体**：`{"name": "测试家庭"}`
- **预期响应**：
  - 状态码：200 OK
  - 响应体：包含家庭ID、名称、所有者ID和创建时间

#### 2.2 空名称测试
- **测试目标**：验证空名称时的错误处理
- **请求**：`POST /v1/families`
- **请求头**：`Authorization: Bearer <token>`
- **请求体**：`{"name": ""}`
- **预期响应**：
  - 状态码：400 Bad Request
  - 响应体：`{"detail": "name required"}`

#### 2.3 获取家庭列表测试
- **测试目标**：验证获取家庭列表接口是否正常工作
- **请求**：`GET /v1/families`
- **请求头**：`Authorization: Bearer <token>`
- **预期响应**：
  - 状态码：200 OK
  - 响应体：家庭列表，包含之前创建的家庭

#### 2.4 添加家庭成员测试
- **测试目标**：验证添加家庭成员接口是否正常工作
- **请求**：`POST /v1/families/{family_id}/members`
- **请求头**：`Authorization: Bearer <token>`
- **请求体**：
  ```json
  {
    "display_name": "测试成员",
    "avatar_url": "https://example.com/avatar.jpg"
  }
  ```
- **预期响应**：
  - 状态码：200 OK
  - 响应体：包含成员ID、家庭ID、显示名称和头像URL

#### 2.5 空成员名称测试
- **测试目标**：验证空成员名称时的错误处理
- **请求**：`POST /v1/families/{family_id}/members`
- **请求头**：`Authorization: Bearer <token>`
- **请求体**：`{"display_name": ""}`
- **预期响应**：
  - 状态码：400 Bad Request
  - 响应体：`{"detail": "display_name required"}`

#### 2.6 获取家庭成员列表测试
- **测试目标**：验证获取家庭成员列表接口是否正常工作
- **请求**：`GET /v1/families/{family_id}/members`
- **请求头**：`Authorization: Bearer <token>`
- **预期响应**：
  - 状态码：200 OK
  - 响应体：家庭成员列表，包含之前添加的成员

### 3. 书籍测试 (`test_books.py`)

#### 3.1 解析书籍测试
- **测试目标**：验证解析书籍接口是否正常工作
- **请求**：`POST /v1/books/resolve`
- **请求头**：`Authorization: Bearer <token>`
- **请求体**：`{"isbn": "9787544270878"}`
- **预期响应**：
  - 状态码：200 OK
  - 响应体：包含书籍ID、ISBN、标题、作者、分类等信息

#### 3.2 无效ISBN测试
- **测试目标**：验证无效ISBN时的错误处理
- **请求**：`POST /v1/books/resolve`
- **请求头**：`Authorization: Bearer <token>`
- **请求体**：`{"isbn": "invalid_isbn"}`
- **预期响应**：
  - 状态码：400 Bad Request
  - 响应体：`{"detail": "invalid isbn"}`

## 运行测试

### 运行所有测试
```bash
# 进入backend目录
cd /Users/dadaozei/Documents/code/family-reading/backend

# 运行所有测试
pytest tests/ -v
```

### 运行特定测试文件
```bash
# 运行认证测试
pytest tests/test_auth.py -v

# 运行家庭测试
pytest tests/test_families.py -v

# 运行书籍测试
pytest tests/test_books.py -v
```

### 生成测试覆盖率报告
```bash
# 运行测试并生成覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

## 预期测试结果

### 测试通过情况
- ✅ 所有认证测试通过
- ✅ 所有家庭测试通过
- ✅ 所有书籍测试通过

### 测试覆盖率
- 认证模块：100%
- 家庭模块：100%
- 书籍模块：100%
- 整体覆盖率：≥90%

## 测试注意事项

1. **测试隔离**：每个测试都会在独立的内存数据库中运行，确保测试之间互不影响
2. **自动认证**：测试会自动获取认证令牌，无需手动设置
3. **错误处理**：测试覆盖了常见的错误情况，如空字段、无效ISBN等
4. **依赖顺序**：测试会按照依赖关系顺序执行，确保测试环境正确设置
5. **性能**：使用内存SQLite数据库，测试执行速度快

## 故障排除

### 测试失败的常见原因

1. **依赖问题**：确保所有依赖已正确安装
   ```bash
   pip install -r requirements.txt
   ```

2. **数据库问题**：测试使用内存SQLite，无需外部数据库

3. **认证问题**：测试会自动处理认证，确保`enable_dev_login`设置为`True`

4. **端口冲突**：确保8000端口未被占用
   ```bash
   lsof -ti:8000 | xargs kill -9 2>/dev/null
   ```

5. **代码修改**：如果修改了API代码，可能需要更新测试用例

### 查看详细测试输出
```bash
# 运行测试并显示详细输出
pytest tests/ -v -s
```

## 结论

本测试套件覆盖了API的主要功能，包括认证、家庭管理和书籍管理。通过运行这些测试，可以确保API的稳定性和可靠性，同时为项目添加了自动化测试的基础。

测试采用了最佳实践，包括测试隔离、错误处理覆盖和自动认证，确保测试的有效性和可维护性。