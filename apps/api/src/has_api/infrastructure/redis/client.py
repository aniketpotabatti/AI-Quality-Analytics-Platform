"""Redis connection pool for caching and job queue.

Redis is OPTIONAL for local development: auth/register/login work without it.
If Redis is unreachable, ``get_redis`` raises on first real command (callers
handle it), and ``get_arq_pool`` raises only when a job is enqueued (the
evaluations router already treats that as fire-and-forget).
"""

from contextlib import suppress

from redis.asyncio import Redis

from has_api.config import get_settings

_redis: Redis | None = None
_arq_pool = None


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = Redis.from_url(str(settings.redis_url), decode_responses=True)
    return _redis


async def get_arq_pool():
    """Return (or lazily create) the ARQ Redis pool for enqueueing jobs."""
    global _arq_pool
    if _arq_pool is None:
        from arq import create_pool
        from arq.connections import RedisSettings

        settings = get_settings()
        _arq_pool = await create_pool(
            RedisSettings.from_dsn(str(settings.redis_url)),
            timeout=2,  # fail fast when Redis is not running locally
        )
    return _arq_pool


async def close_redis() -> None:
    global _redis, _arq_pool
    if _redis is not None:
        with suppress(Exception):
            await _redis.aclose()
        _redis = None
    if _arq_pool is not None:
        with suppress(Exception):
            await _arq_pool.aclose()
        _arq_pool = None
