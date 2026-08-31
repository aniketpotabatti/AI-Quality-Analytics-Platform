"""FastAPI dependency injection providers."""

from has_api.api.dependencies.auth import (
    AuthenticatedPrincipal,
    WorkspaceAccess,
    api_key_scheme,
    bearer_scheme,
    get_current_principal,
    get_optional_principal,
    get_workspace_access,
    require_roles,
)
from has_api.config import Settings, get_settings

__all__ = [
    "AuthenticatedPrincipal",
    "Settings",
    "WorkspaceAccess",
    "api_key_scheme",
    "bearer_scheme",
    "get_current_principal",
    "get_optional_principal",
    "get_settings",
    "get_workspace_access",
    "require_roles",
]
