"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _env_files() -> tuple[str, ...]:
    """Locate .env from common working directories (root or apps/api)."""
    here = Path(__file__).resolve()
    # .../apps/api/src/has_api/config/settings.py -> repo root is 5 levels up
    candidates = [
        Path.cwd() / ".env",
        here.parents[4] / ".env",  # apps/api/
        here.parents[5] / ".env",  # repo root
    ]
    seen: list[str] = []
    for path in candidates:
        text = str(path)
        if text not in seen:
            seen.append(text)
    return tuple(seen)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "staging", "production"] = "development"
    app_name: str = "Hallucination Analytics Studio"
    app_debug: bool = False
    app_secret_key: str = Field(min_length=32)

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    # Kept as plain str so local dev can use SQLite
    # (e.g. sqlite+aiosqlite:///./dev.db) without Postgres validation errors.
    # Production should still set a postgresql+asyncpg:// URL.
    database_url: str = Field(
        default="postgresql+asyncpg://has:has@localhost:5432/hallucination_analytics"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

    jwt_secret_key: str = Field(min_length=32)
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    @field_validator("api_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        # NoDecode delivers the raw env string here (no JSON pre-parsing),
        # so "http://a,http://b" and '["http://a"]' both work.
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                import json

                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except ValueError:
                    pass
            return [origin.strip() for origin in text.split(",") if origin.strip()]
        return value

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
