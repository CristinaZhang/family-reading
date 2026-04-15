from __future__ import annotations

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.status import HTTP_302_FOUND

from app.config import HealthResponse, settings
from app.db.database import init_db
from app.routers import auth, book_copies, books, dashboard, families, readings, web


def create_app() -> FastAPI:
    app = FastAPI(
        title="Family Reading Backend",
        version="0.1.0",
        docs_url=None,  # 禁用默认的docs
        redoc_url=None,  # 禁用默认的redoc
        openapi_url="/openapi.json"
    )

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

    @app.exception_handler(HTTPException)
    async def web_auth_exception_handler(request: Request, exc: HTTPException):
        """Convert 401 on /web/* paths to HTML redirect to login."""
        if exc.status_code == 401 and request.url.path.startswith("/web/"):
            return RedirectResponse(url="/web/login", status_code=HTTP_302_FOUND)
        raise exc

    app.include_router(auth.router, prefix="/v1")
    app.include_router(families.router, prefix="/v1")
    app.include_router(books.router, prefix="/v1")
    app.include_router(book_copies.router, prefix="/v1")
    app.include_router(readings.router, prefix="/v1")
    app.include_router(dashboard.router, prefix="/v1")
    app.include_router(web.router)

    return app


app = create_app()


@app.on_event("startup")
def _startup() -> None:
    init_db()