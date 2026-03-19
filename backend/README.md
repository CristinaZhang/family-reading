# Backend（FastAPI）

## 运行（本地）

```bash
cd family-reading/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"

cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

打开：

- Swagger UI：`http://127.0.0.1:8000/docs`

## 环境变量

见 `.env.example`。

