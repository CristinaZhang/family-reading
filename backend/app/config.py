from __future__ import annotations

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = "dev"
    app_debug: bool = True

    database_url: str = "sqlite:///./data/app.db"

    enable_dev_login: bool = True

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"


settings = Settings()


class HealthResponse(BaseModel):
    status: str

