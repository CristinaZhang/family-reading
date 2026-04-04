# family-reading 后端开发：虚拟环境 + 调试启动完整文档
适用项目：`backend/`，基于 **FastAPI + SQLModel**

## 一、核心流程总览（从0到启动）
```
进入后端目录 → 创建/激活虚拟环境 → 安装依赖 → 复制环境配置 → 启动服务（自动清理端口）→ 调试开发
```

---

## 二、从零开始：虚拟环境完整操作
### 1. 进入后端目录
```bash
cd ~/Documents/code/family-reading/backend
```

### 2. 销毁旧/损坏环境（可选，推荐）
```bash
rm -rf .venv
```

### 3. 创建全新虚拟环境
```bash
python3 -m venv .venv
```

### 4. 激活虚拟环境（必须执行）
```bash
source .venv/bin/activate
```
✅ 激活成功标志：终端前缀出现 `(.venv)`

### 5. 退出虚拟环境（用完关闭）
```bash
deactivate
```

---

## 三、依赖安装（一次性解决所有报错）
### 升级基础工具
```bash
pip install -U pip setuptools wheel
```

### 安装项目必须依赖（完整版）
```bash
pip install fastapi uvicorn python-dotenv pydantic pydantic_settings sqlmodel
```

---

## 四、环境配置
```bash
cp .env.example .env
```
> 作用：加载项目配置（密钥、数据库、端口等），项目启动必须。

---

## 五、服务启动与调试（最关键）
### 方案A：标准启动（推荐，自动清理端口）
**每次调试都用这一行，彻底解决端口占用**
```bash
lsof -ti:8000 | xargs kill -9 2>/dev/null && uvicorn app.main:app --reload --port 8000
```

### 方案B：简化启动（手动杀端口）
```bash
# 杀占用进程
lsof -ti:8000 | xargs kill -9

# 启动服务
uvicorn app.main:app --reload --port 8000
```

---

## 六、端口占用问题：查询 + 杀死 手册
### 1. 查询谁占用 8000 端口
```bash
lsof -ti:8000
```
输出数字 = 进程PID

### 2. 查看进程详情（确认是否为Uvicorn/Python）
```bash
ps 你的PID
```

### 3. 强制杀死进程
```bash
kill -9 你的PID
```

---

## 七、启动成功标志
```
Uvicorn running on http://127.0.0.1:8000
```

### 访问地址
- 本地服务：http://localhost:8000
- API文档：http://localhost:8000/docs

---

## 八、VS Code + TRAE 调试建议
1. 打开 `backend` 文件夹
2. VS Code 自动识别 `.venv` 环境
3. 使用 TRAE AI 插件：解释代码、修复报错、生成接口
4. 调试运行直接使用本文**启动命令**

---

## 九、完整一键启动脚本（最终版）
你配置好venv后，**直接复制这一段执行即可跑起项目**：
```bash
cd ~/Documents/code/family-reading/backend
source .venv/bin/activate
lsof -ti:8000 | xargs kill -9 2>/dev/null
uvicorn app.main:app --reload --port 8000
```

---

## 十、微信小程序调试

### 10.1 网络连接问题
- **问题**：小程序无法连接到后端服务
- **原因**：
  - 后端服务未启动
  - 微信开发者工具网络请求设置不正确
  - BASE_URL配置错误
- **解决方案**：
  1. 启动后端服务
  2. 在微信开发者工具中：
     - 点击 "项目" -> "项目设置" -> "本地设置"
     - 勾选 "不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书"
  3. 确保 `BASE_URL` 配置正确：
     ```javascript
     // miniprogram/utils/config.js
     const BASE_URL = "http://127.0.0.1:8000";
     ```

### 10.2 页面配置问题
- **问题**：模拟器启动失败，提示未找到页面文件
- **原因**：`app.json` 中配置了不存在的页面路径
- **解决方案**：
  - 创建缺失的页面文件
  - 或修改 `app.json` 只包含已存在的页面路径

### 10.3 图标文件问题
- **问题**：编译失败，提示未找到图标文件
- **原因**：`app.json` 中配置了不存在的图标文件路径
- **解决方案**：
  - 创建 `images` 目录并添加所需图标
  - 或修改 `app.json` 移除图标配置，使用默认图标

### 10.4 登录失败问题
- **问题**：小程序登录失败，提示 "请检查后端是否启动、BASE_URL 是否正确"
- **解决步骤**：
  1. 确认后端服务正在运行
  2. 检查 `BASE_URL` 配置
  3. 检查 `enable_dev_login` 配置是否为 `True`
  4. 在后端日志中查看是否有登录请求
  5. 检查数据库连接是否正常

### 10.5 测试网络连接
在小程序的控制台中执行以下代码，测试网络连接：
```javascript
wx.request({
  url: 'http://127.0.0.1:8000/health',
  method: 'GET',
  success: function(res) {
    console.log('健康检查成功:', res);
  },
  fail: function(err) {
    console.log('健康检查失败:', err);
  }
});
```

---

## 十一、常见问题及解决方案

### 11.1 后端服务启动问题
- **症状**：`uvicorn` 启动失败
- **可能原因**：
  - 端口被占用
  - 依赖未安装
  - 环境变量配置错误
- **解决方案**：
  - 检查端口占用并释放
  - 安装所有依赖
  - 检查 `.env` 文件配置

### 11.2 数据库连接问题
- **症状**：API 请求返回数据库错误
- **可能原因**：
  - 数据库文件权限问题
  - 数据库连接字符串错误
- **解决方案**：
  - 确保 `data` 目录存在且可写
  - 检查 `DATABASE_URL` 配置

### 11.3 小程序编译问题
- **症状**：小程序编译失败
- **可能原因**：
  - 页面文件缺失
  - 配置文件错误
  - 代码语法错误
- **解决方案**：
  - 检查所有页面文件是否存在
  - 验证 `app.json` 配置
  - 检查控制台错误信息

### 11.4 API 测试失败
- **症状**：测试用例执行失败
- **可能原因**：
  - 代码语法错误
  - 测试数据不匹配
  - API 行为变更
- **解决方案**：
  - 检查测试文件语法
  - 验证测试数据
  - 确保 API 实现与测试预期一致

### 11.5 Swagger UI 版本字段错误
- **症状**：Swagger UI 显示 "Unable to render this definition"
- **原因**：OpenAPI 规范缺少有效的版本字段
- **解决方案**：
  - 在 `app/main.py` 中添加自定义的 `openapi` 方法
  - 确保生成的 OpenAPI 规范包含正确的版本字段
  ```python
  # 保存原始的 openapi 方法
  original_openapi = app.openapi

  # 自定义 OpenAPI 规范，添加版本字段
  def custom_openapi():
      if app.openapi_schema:
          return app.openapi_schema
      # 调用原始的 openapi 方法
      openapi_schema = original_openapi()
      # 确保添加正确的 OpenAPI 版本
      openapi_schema["openapi"] = "3.0.2"
      app.openapi_schema = openapi_schema
      return app.openapi_schema

  app.openapi = custom_openapi
  ```

---

## 十二、开发建议

### 12.1 后端开发
- 使用虚拟环境管理依赖
- 定期运行测试确保代码质量
- 保持 API 接口的一致性和文档完整性
- 实现适当的错误处理和日志记录

### 12.2 前端开发
- 确保网络请求配置正确
- 实现加载状态和错误提示
- 优化页面渲染性能
- 确保在不同设备上的兼容性

### 12.3 测试
- 编写单元测试和集成测试
- 测试边界情况和错误处理
- 定期运行测试套件
- 确保代码覆盖率达到预期目标

### 12.4 部署
- 使用环境变量管理配置
- 配置适当的安全措施
- 准备详细的部署文档
- 测试生产环境部署流程