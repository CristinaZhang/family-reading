from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

from app.config import HealthResponse, settings
from app.db.database import init_db
from app.routers import auth, book_copies, books, dashboard, families, readings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Family Reading Backend",
        version="0.1.0",
        docs_url=None,  # 禁用默认的docs
        redoc_url=None,  # 禁用默认的redoc
        openapi_url="/openapi.json",
        openapi_version="3.0.2"  # 明确指定OpenAPI版本
    )

    # 挂载静态文件目录
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # 自定义Swagger UI路由
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Swagger UI",
            # 使用本地资源
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
            swagger_favicon_url="/static/favicon-32x32.png",
        )

    # 自定义ReDoc路由
    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        from fastapi.openapi.docs import get_redoc_html
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - ReDoc",
            redoc_js_url="/static/redoc.standalone.js",
        )

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