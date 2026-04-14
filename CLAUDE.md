# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**family-reading** is a family reading tracking system with a FastAPI backend and a WeChat miniprogram frontend. It enables families to manage books, track reading progress, and view reading statistics.

## Directory Structure

```
family-reading/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py             # App entry point, creates FastAPI app
│   │   ├── config.py           # Pydantic settings (env vars)
│   │   ├── auth.py             # Auth middleware (Bearer token -> AuthUser)
│   │   ├── db/
│   │   │   ├── database.py     # SQLModel engine, session, init_db
│   │   │   └── models.py       # All database models (SQLModel)
│   │   ├── routers/
│   │   │   ├── auth.py         # POST /v1/auth/dev/login, /v1/auth/wechat/login
│   │   │   ├── families.py     # Family CRUD + member management
│   │   │   ├── books.py        # POST /v1/books/resolve (ISBN lookup), POST /v1/books
│   │   │   ├── book_copies.py  # Book copy management per family
│   │   │   ├── readings.py     # Reading records (POST/PATCH/GET)
│   │   │   └── dashboard.py    # GET /v1/families/{id}/dashboard (stats)
│   │   └── services/
│   │       ├── book_provider.py # ISBN book providers (Open Library API)
│   │       └── isbn.py          # ISBN validation/conversion utilities
│   └── tests/
│       ├── conftest.py          # pytest fixtures (in-memory SQLite, auth_token)
│       └── test_*.py            # Test files
├── miniprogram/                # WeChat miniprogram frontend
│   ├── app.json                # Miniprogram config (pages, tabBar)
│   ├── utils/
│   │   ├── config.js            # BASE_URL for backend
│   │   └── api.js               # HTTP request wrapper (wx.request)
│   └── pages/
│       ├── login/               # WeChat login + dev login fallback
│       ├── home/                # Main dashboard (family stats)
│       ├── scan_add/            # Scan ISBN to add books
│       ├── reading_list/        # List of reading records
│       └── reading_detail/      # Reading detail view
└── docs/
```

## Key Commands

### Backend

```bash
# Setup (first time)
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"  # or: pip install -r requirements.txt

# Start dev server
cp .env.example .env  # if not done
uvicorn app.main:app --reload --port 8000

# Run all tests
cd backend
pytest tests/ -v

# Run single test file
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Miniprogram

Open the `miniprogram/` directory in WeChat DevTools. The backend must be running locally at `http://127.0.0.1:8000` (configurable in `miniprogram/utils/config.js`).

```bash
# Run frontend tests
cd miniprogram
npm test
npm run test:verbose
```

## Architecture

### Backend (FastAPI + SQLModel + SQLite)

- **Framework**: FastAPI with SQLModel ORM
- **Database**: SQLite by default (`backend/data/app.db`), configured via `DATABASE_URL` env var
- **Auth**: Simple Bearer token format `u:<user_id>`. Auth is done via `get_current_user()` dependency that returns `AuthUser`.
- **API prefix**: All routes are under `/v1`
- **CORS**: Configured via `CORS_ORIGINS` env var (comma-separated)

**Key models** (in `backend/app/db/models.py`):
- `User` - WeChat openid-based users
- `Family` / `FamilyMember` - Family grouping with owner
- `BookMeta` - Book metadata (ISBN, title, authors, publisher, etc.)
- `BookCopy` - A physical copy of a book owned by a family
- `Reading` - Reading progress record linking a member to a book

**API endpoints** (all prefixed with `/v1`):
| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/dev/login | Dev login with openid |
| POST | /auth/wechat/login | WeChat login with code |
| POST | /families | Create family |
| GET | /families | List families (owner only) |
| POST | /families/{id}/members | Add member |
| GET | /families/{id}/members | List members |
| POST | /books/resolve | Resolve ISBN via Open Library |
| POST | /books | Create book manually |
| POST | /families/{id}/book_copies | Add book copy to family |
| GET | /families/{id}/book_copies | List book copies |
| POST | /readings | Create reading record |
| PATCH | /readings/{id} | Update reading progress |
| GET | /families/{id}/readings | List readings |
| GET | /families/{id}/dashboard | Family reading stats |
| GET | /health | Health check |

### Frontend (WeChat Miniprogram)

- Uses `wx.request` wrapped in `miniprogram/utils/api.js` with Bearer token auth
- Token stored in `wx.setStorageSync("access_token")`
- Pages: login → home → scan_add / reading_list / reading_detail / settings

### Frontend Testing

- Jest-based tests in `miniprogram/__tests__/`
- `__mocks__/wx.js` provides mocked WeChat runtime APIs (`wx.request`, `wx.showToast`, etc.)
- `api.test.js` — tests the request wrapper (token injection, URL construction, response handling)
- `page_logic.test.js` — tests page business logic by recreating page methods with the real `request()` function
- Run: `cd miniprogram && npm test`

### Testing

- Uses pytest with `fastapi.testclient.TestClient`
- Each test gets an isolated in-memory SQLite database (`sqlite://` with `StaticPool`)
- `auth_token` fixture auto-logs in via dev login
- Tests are in `backend/tests/`

### Environment Variables

See `backend/.env.example`. Key vars:
- `DATABASE_URL` - Database connection string
- `ENABLE_DEV_LOGIN` - Enable/disable dev login (default: 1)
- `WECHAT_APP_ID` / `WECHAT_APP_SECRET` - WeChat miniprogram credentials (**stored in `backend/local.env`, never committed**)
- `CORS_ORIGINS` - Comma-separated allowed origins

**Local config**: WeChat credentials go in `backend/local.env` (gitignored). The `Settings` class auto-loads it as an override to `.env`.
