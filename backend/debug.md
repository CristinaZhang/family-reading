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

