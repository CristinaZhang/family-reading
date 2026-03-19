from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import HealthResponse, settings
from app.db.database import init_db
from app.routers import auth, book_copies, books, dashboard, families, readings


def create_app() -> FastAPI:
    app = FastAPI(title="Family Reading Backend", version="0.1.0")

    origins = [o.strip() for o in (settings.cors_origins or "").split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    app.include_router(auth.router, prefix="/v1")
    app.include_router(families.router, prefix="/v1")
    app.include_router(books.router, prefix="/v1")
    app.include_router(book_copies.router, prefix="/v1")
    app.include_router(readings.router, prefix="/v1")
    app.include_router(dashboard.router, prefix="/v1")

    return app


app = create_app()


@app.on_event("startup")
def _startup() -> None:
    init_db()

