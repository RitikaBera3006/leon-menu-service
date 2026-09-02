from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Leon Menu Service"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production", "local"] = "development"
    sentry_dsn: str = ""
    sentry_environment: str = ""

    # API
    api_v1_prefix: str = "/api/v1"

    # Database — this service owns its own Postgres schema (migrated via
    # alembic/versions/0001_initial_menu_schema.py), independent of leon-api's
    # database. Populating it from Centegra/leon-api is a separate concern.
    database_url: str = "postgresql+asyncpg://user:password@host/leon_menu_db"
    # How long a request waits for a free pooled connection before giving up.
    # SQLAlchemy's default is 30s, which only converts pool exhaustion into 30s
    # of latency on every queued request before they fail anyway. Failing fast
    # keeps the event loop free and surfaces the real problem sooner.
    db_pool_timeout_seconds: int = 10

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    cors_allow_headers: list[str] = ["Content-Type", "Authorization", "X-API-Key"]

    # Scalar / OpenAPI HTTP Basic when docs are enabled (local/development only).
    docs_basic_auth_username: str = ""
    docs_basic_auth_password: str = ""

    @field_validator("database_url")
    @classmethod
    def reject_empty_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL must be set")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
