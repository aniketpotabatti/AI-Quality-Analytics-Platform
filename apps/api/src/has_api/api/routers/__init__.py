"""HTTP route modules."""

from has_api.api.routers.analytics import router as analytics_router
from has_api.api.routers.api_keys import router as api_keys_router
from has_api.api.routers.auth import router as auth_router
from has_api.api.routers.datasets import router as datasets_router
from has_api.api.routers.evaluations import router as evaluations_router
from has_api.api.routers.health import router as health_router
from has_api.api.routers.models import router as models_router
from has_api.api.routers.workspaces import router as workspaces_router

__all__ = [
    "analytics_router",
    "api_keys_router",
    "auth_router",
    "datasets_router",
    "evaluations_router",
    "health_router",
    "models_router",
    "workspaces_router",
]
