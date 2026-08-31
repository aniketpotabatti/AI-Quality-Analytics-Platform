"""Authentication and authorization dependencies with full JWT verification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from has_api.api.schemas.enums import WorkspaceRole
from has_api.infrastructure.auth.jwt import decode_token
from has_api.infrastructure.database.repository_factory import RepositoryContainer
from has_api.infrastructure.database.session import get_db_session

bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuth",
    description="JWT access token from POST /api/v1/auth/login",
)

api_key_scheme = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    scheme_name="ApiKeyAuth",
    description="Workspace API key (prefix has_…); alternative to JWT",
)


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    """Identity resolved from JWT or API key."""

    user_id: UUID | None
    workspace_id: UUID | None
    auth_method: str  # "jwt" | "api_key"
    role: WorkspaceRole | None = None
    api_key_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class WorkspaceAccess:
    """Principal confirmed to have access to a specific workspace."""

    principal: AuthenticatedPrincipal
    workspace_id: UUID
    role: WorkspaceRole


async def get_optional_principal(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(bearer_scheme),
    ] = None,
    api_key: Annotated[str | None, Security(api_key_scheme)] = None,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> AuthenticatedPrincipal | None:
    """Resolve principal from JWT bearer token or API key."""
    if credentials is not None:
        payload = decode_token(credentials.credentials)
        if payload is None or payload.type != "access":
            return None
        ws_id = UUID(payload.workspace_id) if payload.workspace_id else None
        return AuthenticatedPrincipal(
            user_id=UUID(payload.sub),
            workspace_id=ws_id,
            auth_method="jwt",
        )

    if api_key is not None and session is not None:
        # API key lookup — prefix-based fast path
        from has_api.infrastructure.database.models.identity import ApiKeyModel
        from sqlalchemy import select
        from has_api.infrastructure.auth.password import verify_password

        prefix = api_key[:8] if len(api_key) >= 8 else api_key
        result = await session.execute(
            select(ApiKeyModel).where(
                ApiKeyModel.key_prefix == prefix,
                ApiKeyModel.is_active.is_(True),
            )
        )
        key_model = result.scalar_one_or_none()
        if key_model and verify_password(api_key, key_model.key_hash):
            return AuthenticatedPrincipal(
                user_id=None,
                workspace_id=key_model.workspace_id,
                auth_method="api_key",
                role=WorkspaceRole.MEMBER,
                api_key_id=key_model.id,
            )

    return None


async def get_current_principal(
    principal: Annotated[AuthenticatedPrincipal | None, Depends(get_optional_principal)],
) -> AuthenticatedPrincipal:
    """Require a valid JWT or API key."""
    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "about:blank",
                "title": "Unauthorized",
                "status": 401,
                "detail": "Valid Bearer token or X-API-Key header required",
                "code": "unauthorized",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    return principal


async def get_workspace_access(
    workspace_id: UUID,
    principal: Annotated[AuthenticatedPrincipal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    x_workspace_id: Annotated[
        UUID | None,
        Header(
            alias="X-Workspace-Id",
            description="Optional explicit workspace header (must match path)",
        ),
    ] = None,
) -> WorkspaceAccess:
    """Authorize the principal for the path workspace_id via DB membership check."""
    if x_workspace_id is not None and x_workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "about:blank",
                "title": "Bad Request",
                "status": 400,
                "detail": "X-Workspace-Id header does not match path workspace_id",
                "code": "workspace_mismatch",
            },
        )

    # API key is scoped to its own workspace
    if principal.auth_method == "api_key":
        if principal.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "type": "about:blank",
                    "title": "Forbidden",
                    "status": 403,
                    "detail": "API key is not scoped to this workspace",
                    "code": "forbidden",
                },
            )
        return WorkspaceAccess(
            principal=principal,
            workspace_id=workspace_id,
            role=principal.role or WorkspaceRole.MEMBER,
        )

    # JWT principal — look up membership in DB
    if principal.user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    repos = RepositoryContainer(session)
    member = await repos.workspaces.get_member(workspace_id, principal.user_id)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "about:blank",
                "title": "Forbidden",
                "status": 403,
                "detail": "Principal is not a member of this workspace",
                "code": "forbidden",
            },
        )

    return WorkspaceAccess(
        principal=principal,
        workspace_id=workspace_id,
        role=WorkspaceRole(member.role),
    )


def require_roles(*allowed: WorkspaceRole):
    """Dependency factory: ensure workspace role is one of `allowed`."""

    async def _checker(
        access: Annotated[WorkspaceAccess, Depends(get_workspace_access)],
    ) -> WorkspaceAccess:
        if access.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "type": "about:blank",
                    "title": "Forbidden",
                    "status": 403,
                    "detail": f"Requires one of roles: {', '.join(r.value for r in allowed)}",
                    "code": "forbidden",
                },
            )
        return access

    return _checker
