"""API route handlers."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from has_api import __version__
from has_api.api.schemas.common import HealthResponse, ReadyResponse
from has_api.config import Settings, get_settings
from has_api.infrastructure.database import get_db_session
from has_api.infrastructure.redis import get_redis

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(version=__version__)


@router.get("/ready", response_model=ReadyResponse)
async def readiness_check(
    session: AsyncSession = Depends(get_db_session),
) -> ReadyResponse:
    db_status = "ok"
    redis_status = "ok"

    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"

    try:
        redis = await get_redis()
        await redis.ping()
    except Exception:
        redis_status = "unavailable"

    overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"
    return ReadyResponse(status=overall, database=db_status, redis=redis_status)


@router.get("/")
async def root(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": __version__,
        "docs": "/docs",
    }
