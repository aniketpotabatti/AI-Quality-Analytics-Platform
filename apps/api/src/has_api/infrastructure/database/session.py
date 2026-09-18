"""SQLAlchemy database session and base model."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from has_api.config import get_settings
from has_api.infrastructure.database.base import Base

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def reset_engine() -> None:
    """Reset cached engine (used in tests)."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        url = str(settings.database_url)
        if url.startswith("sqlite"):
            _engine = create_async_engine(url, echo=settings.is_development)
        else:
            _engine = create_async_engine(
                url,
                echo=settings.is_development,
                pool_pre_ping=True,
            )
    return _engine


async def init_db() -> None:
    """Create tables from metadata.

    Used for the SQLite local-dev fallback (Alembic migrations are
    Postgres-specific). On Postgres this is a harmless no-op when
    migrations have already run (``checkfirst=True``).
    """
    from has_api.infrastructure.database import models  # noqa: F401  (register metadata)

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
