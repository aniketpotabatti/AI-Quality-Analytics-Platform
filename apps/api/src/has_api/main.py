"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from has_api import __version__
from has_api.api.exception_handlers import domain_exception_handler
from has_api.api.routers import (
    analytics_router,
    api_keys_router,
    auth_router,
    datasets_router,
    evaluations_router,
    health_router,
    models_router,
    workspaces_router,
)
from has_api.config import get_settings
from has_api.domain.exceptions import DomainError
from has_api.infrastructure.redis import close_redis

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info("starting_api", env=settings.app_env, version=__version__)
    yield
    await close_redis()
    logger.info("stopped_api")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Evaluate LLM outputs for hallucination and grounding.",
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(DomainError, domain_exception_handler)  # type: ignore[arg-type]

    # Health (no prefix)
    app.include_router(health_router)

    # All v1 routes
    api_prefix = "/api/v1"
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(workspaces_router, prefix=api_prefix)
    app.include_router(datasets_router, prefix=api_prefix)
    app.include_router(evaluations_router, prefix=api_prefix)
    app.include_router(models_router, prefix=api_prefix)
    app.include_router(analytics_router, prefix=api_prefix)
    app.include_router(api_keys_router, prefix=api_prefix)

    return app


app = create_app()
